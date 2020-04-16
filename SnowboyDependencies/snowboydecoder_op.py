
#!/usr/bin/env python

import collections
from SnowboyDependencies import snowboydetect
import time
import wave
import os
import logging
import subprocess
import threading
import sys
import json
import io
import sys
import aifc
import platform
import stat
import audioop
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logging.basicConfig()
logger = logging.getLogger("snowboy")
logger.setLevel(logging.INFO)


logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

TOP_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCE_FILE = os.path.join(TOP_DIR, "resources/common.res")
DETECT_DING = os.path.join(TOP_DIR, "resources/ding.wav")
DETECT_DONG = os.path.join(TOP_DIR, "resources/dong.wav")


class RingBuffer(object):
    """Ring buffer to hold audio from audio capturing tool"""
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        """Adds data to the end of buffer"""
        self._buf.extend(data)

    def get(self):
        """Retrieves data from the beginning of buffer and clears it"""
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp

    def clear(self):
        self._buf.clear()


def play_audio_file(fname=DETECT_DING):
    """Simple callback function to play a wave file. By default it plays
    a Ding sound.
    :param str fname: wave file name
    :return: None
    """
    os.system("aplay " + fname + " > /dev/null 2>&1")

def get_wav_data(raw_data):
    # generate the WAV file contents
    with io.BytesIO() as wav_file:
        wav_writer = wave.open(wav_file, "wb")
        try:
            wav_writer.setframerate(16000) #sample_rate always 16000
            wav_writer.setsampwidth(2) #sample_width always 2
            wav_writer.setnchannels(1)
            wav_writer.writeframes(raw_data)
            wav_data = wav_file.getvalue()
        finally:
            wav_writer.close()
    return wav_data
    
def recognize_wit(raw_data, key, show_all=False, timeout=None):
    wav_data = get_wav_data(raw_data)
    url = "https://api.wit.ai/speech?v=20160526"
    request = Request(url, data=wav_data, headers={"Authorization": "Bearer {}".format(key), "Content-Type": "audio/wav"})
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as e:
        raise Exception("recognition request failed: {}".format(e.reason))
    except URLError as e:
        raise Exception("recognition connection failed: {}".format(e.reason))
    response_text = response.read().decode("utf-8")
    result = json.loads(response_text)
    # return results
    if show_all: return result
    if "_text" not in result or result["_text"] is None: raise Exception()
    return result["_text"]

class HotwordDetector(object):
    """
    Snowboy decoder to detect whether a keyword specified by `decoder_model`
    exists in a microphone input stream.
    :param decoder_model: decoder model file path, a string or a list of strings
    :param resource: resource file path.
    :param sensitivity: decoder sensitivity, a float of a list of floats.
                              The bigger the value, the more senstive the
                              decoder. If an empty list is provided, then the
                              default sensitivity in the model will be used.
    :param audio_gain: multiply input volume by this factor.
    """
    def __init__(self, decoder_model = None,
                 resource=RESOURCE_FILE,
                 sensitivity=[],
                 audio_gain=1):

        tm = type(decoder_model)
        ts = type(sensitivity)
        if tm is not list:
            decoder_model = [decoder_model]
        if ts is not list:
            sensitivity = [sensitivity]
        model_str = ",".join(decoder_model)

        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource.encode(), model_str=model_str.encode())
        self.detector.SetAudioGain(audio_gain)
        self.num_hotwords = self.detector.NumHotwords()

        if len(decoder_model) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity*self.num_hotwords
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), \
                "number of hotwords in decoder_model (%d) and sensitivity " \
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str.encode())

        self.ring_buffer = RingBuffer(
            self.detector.NumChannels() * self.detector.SampleRate() * 5)

    def record_proc(self):
        while self.recording:
            chunk = 2048
            record_rate = 16000
            
            cmd = 'arecord --device=plughw:1,0 -q -r %d -f S16_LE' % record_rate
            process = subprocess.Popen(cmd.split(' '),
                                       stdout = subprocess.PIPE,
                                       stderr = subprocess.PIPE)
            wav = wave.open(process.stdout, 'rb')
            while self.recording:
                data = wav.readframes(chunk)
                self.ring_buffer.extend(data)
            process.terminate()

    def init_recording(self):
        """
        Start a thread for spawning arecord process and reading its stdout
        """
        self.recording = True
        self.record_thread = threading.Thread(target = self.record_proc)
        self.record_thread.start()

    def get_stt(self, key, begin_count_threshold=5, silent_count_threshold=3, sleep_time=.03, sample_rate=16000, trim=5, sample_width=2):
        speech = self.fetch_audio_data(begin_count_threshold, silent_count_threshold, trim, sleep_time)
        try:
            text = recognize_wit(speech, key)
        except:
            text = None
        return text

    def fetch_audio_data(self, begin_count_threshold, silent_count_threshold, trim, sleep_time):
        while True:
            data = self.ring_buffer.get()
            if len(data) == 0:
                time.sleep(sleep_time)
                continue
                    
            status = self.detector.RunDetection(data)
            if not self.begin:
                self.recorded_data.append(data) #record before beginning 
                if status == 0:
                    if self.begin_count >= begin_count_threshold:
                        self.begin = True
                    self.begin_count+=1
                else:
                    self.begin_count = 0
                    buffer_len = len(self.recorded_data)
                    if buffer_len >= trim:
                        del self.recorded_data[0:len(self.recorded_data)-trim] #keep some frames so audio doesn't cutoff
                    else:
                        del self.recorded_data[:]
                continue  
            if status == -2:
                if self.silent_count > silent_count_threshold:
                    final_data = b''.join(self.recorded_data)
                    self.recorded_data = []   
                    self.silent_count = 0 
                    self.begin_count = 0
                    self.begin = False
                    return final_data
                else:
                    self.silent_count+=1
            elif status == 0:
                self.silent_count = 0
            self.recorded_data.append(data)

    def wait_for_hotword(self, detected_callback=play_audio_file,
                         interrupt_check=lambda: False,
                         sleep_time=.03):
        """
        Start the voice detector. For every `sleep_time` second it checks the
        audio buffer for triggering keywords. If detected, then call
        corresponding function in `detected_callback`, which can be a single
        function (single model) or a list of callback functions (multiple
        models). Every loop it also calls `interrupt_check` -- if it returns
        True, then breaks from the loop and return.
        :param detected_callback: a function or list of functions. The number of
                                  items must match the number of models in
                                  `decoder_model`.
        :param interrupt_check: a function that returns True if the main loop
                                  needs to stop.
        :param float sleep_time: how much time in second every loop waits.  
        :param silent_count_threshold: indicates how long silence must be heard 
                                  to mark the end of a phrase that is  
                                  being recorded.  
        :return: None
        """

        self.init_recording()

        if interrupt_check():
            logger.debug("detect voice return")
            return

        tc = type(detected_callback)
        if tc is not list:
            detected_callback = [detected_callback]
        if len(detected_callback) == 1 and self.num_hotwords > 1:
            detected_callback *= self.num_hotwords

        assert self.num_hotwords == len(detected_callback), \
            "Error: hotwords in your models (%d) do not match the number of " \
            "callbacks (%d)" % (self.num_hotwords, len(detected_callback))

        logger.debug("detecting...")
    
        while True:
            if interrupt_check():
                logger.debug("detect voice break")
                break
            data = self.ring_buffer.get()
            if len(data) == 0:
                time.sleep(sleep_time)
                continue

            status = self.detector.RunDetection(data)
            if status == -1:
                logger.warning("Error initializing streams or reading audio data")

            if status > 0: #key word found  
                self.recorded_data = []   
                self.silent_count = 0 
                self.begin_count = 0
                self.begin = False
                message = "Keyword " + str(status) + " detected at time: "
                message += time.strftime("%Y-%m-%d %H:%M:%S",
                                            time.localtime(time.time()))
                logger.info(message)
                callback = detected_callback[status-1]
                if callback is not None:
                    callback()
                self.ring_buffer.clear()
                # self.recorded_data.append(data) 
                        
        logger.debug("finished.")

    def terminate(self):
        """
        Terminate audio stream. Users cannot call start() again to detect.
        :return: None
        """
        self.recording = False
        self.record_thread.join()