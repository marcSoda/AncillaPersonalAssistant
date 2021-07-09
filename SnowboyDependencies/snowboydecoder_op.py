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
    def __init__(self,
                 decoder_model = None,
                 resource=RESOURCE_FILE,
                 sensitivity=[],
                 audio_card_number=1,
                 audio_gain=1):

        self.AUDIO_CARD_NUMBER = audio_card_number

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

        self.init_recording()

    def record_proc(self):
        while self.recording:
            chunk = 2048
            record_rate = 16000

            cmd = 'arecord --device=plughw:'+ str(self.AUDIO_CARD_NUMBER) + ',0 -q -r %d -f S16_LE' % record_rate
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

        logger.debug("finished.")

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

    def get_stt(self, begin_count_threshold=5, silent_count_threshold=3, sleep_time=.03, sample_rate=16000, trim=5, sample_width=2):
        speech = self.fetch_audio_data(begin_count_threshold, silent_count_threshold, trim, sleep_time)
        try:
            text = recognize_google(speech)
        except Exception as e:
            text = "Error"
        if text == "":
            text = "Error"
        return text

    def terminate(self):
        self.recording = False
        self.record_thread.join()

#adapted from SpeechRecognition by Anthony Zhang
def recognize_google(raw_data, language="en-US", show_all=False):
    flac_data = get_flac_data(raw_data)
    key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
    url = "http://www.google.com/speech-api/v2/recognize?{}".format(urlencode({
        "client": "chromium",
        "lang": language,
        "key": key,
    }))
    request = Request(url, data=flac_data, headers={"Content-Type": "audio/x-flac; rate={}".format(16000)})

    # obtain audio transcription results
    try:
        response = urlopen(request, timeout=None)
    except HTTPError as e:
        raise RequestError("recognition request failed: {}".format(e.reason))
    except URLError as e:
        raise RequestError("recognition connection failed: {}".format(e.reason))
    response_text = response.read().decode("utf-8")

    # ignore any blank blocks
    actual_result = []
    for line in response_text.split("\n"):
        if not line: continue
        result = json.loads(line)["result"]
        if len(result) != 0:
            actual_result = result[0]
            break

    # return results
    if show_all: return actual_result
    if not isinstance(actual_result, dict) or len(actual_result.get("alternative", [])) == 0: raise ValueError("Unknown Value Error")

    if "confidence" in actual_result["alternative"]:
        # return alternative with highest confidence score
        best_hypothesis = max(actual_result["alternative"], key=lambda alternative: alternative["confidence"])
    else:
        # when there is no confidence available, we arbitrarily choose the first hypothesis.
        best_hypothesis = actual_result["alternative"][0]
    if "transcript" not in best_hypothesis: raise ValueError("Unknown Value Error")
    return best_hypothesis["transcript"]

def get_flac_data(raw_data, convert_rate=None, convert_width=None):
    wav_data = get_wav_data(raw_data)
    flac_converter = get_flac_converter()
    if os.name == "nt":  # on Windows, specify that the process is to be started without showing a console window
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # specify that the wShowWindow field of `startup_info` contains a value
        startup_info.wShowWindow = subprocess.SW_HIDE  # specify that the console window should be hidden
    else:
        startup_info = None  # default startupinfo
    process = subprocess.Popen([
        flac_converter,
        "--stdout", "--totally-silent",  # put the resulting FLAC file in stdout, and make sure it's not mixed with any program output
        "--best",  # highest level of compression available
        "-",  # the input FLAC file contents will be given in stdin
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startup_info)
    flac_data, stderr = process.communicate(wav_data)
    return flac_data

def get_flac_converter():
    """Returns the absolute path of a FLAC converter executable, or raises an OSError if none can be found."""
    flac_converter = shutil_which("flac")  # check for installed version first
    if flac_converter is None:  # flac utility is not installed
        base_path = os.path.dirname(os.path.abspath(__file__))  # directory of the current module file, where all the FLAC bundled binaries are stored
        system, machine = platform.system(), platform.machine()
        if system == "Windows" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-win32.exe")
        elif system == "Darwin" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-mac")
        elif system == "Linux" and machine in {"i686", "i786", "x86"}:
            flac_converter = os.path.join(base_path, "flac-linux-x86")
        elif system == "Linux" and machine in {"x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-linux-x86_64")
        else:  # no FLAC converter available
            raise OSError("FLAC conversion utility not available - consider installing the FLAC command line application by running `apt-get install flac` or your operating system's equivalent")

    # mark FLAC converter as executable if possible
    try:
        # handle known issue when running on docker:
        # run executable right after chmod() may result in OSError "Text file busy"
        # fix: flush FS with sync
        if not os.access(flac_converter, os.X_OK):
            stat_info = os.stat(flac_converter)
            os.chmod(flac_converter, stat_info.st_mode | stat.S_IEXEC)
            if 'Linux' in platform.system():
                os.sync() if sys.version_info >= (3, 3) else os.system('sync')

    except OSError: pass
    return flac_converter

def shutil_which(pgm):
    """Python 2 compatibility: backport of ``shutil.which()`` from Python 3"""
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
