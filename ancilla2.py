import speech_recognition as sr
from SnowboyDependencies import snowboydecoder
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
from contextlib import contextmanager

ding_path = "SnowboyDependencies/resources/ding.wav"
dong_path = "SnowboyDependencies/resources/dong.wav"
hotword_path = "SnowboyDependencies/Wumbo.pmdl"

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt): pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
@contextmanager
def no_alsa_error():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

r = sr.Recognizer()
r.pause_threshold = 0.5 #seconds of non-speaking audio before a phrase is considered complete
r.phrase_threshold = 0.2 #minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
r.non_speaking_duration = .3 # seconds of non-speaking audio to keep on both sides of the recording

def get_text():
    with no_alsa_error():
        with sr.Microphone(sample_rate = 48000) as source:
            # r.adjust_for_ambient_noise(source)
            snowboydecoder.play_audio_file(ding_path)
            
            audio = r.listen(source, snowboy_configuration=("SnowboyDependencies", {hotword_path}))
        
    snowboydecoder.play_audio_file(dong_path)
    text = "Failure"
    try:
        text = r.recognize_google(audio).lower()
    except sr.UnknownValueError:
        print("Sorry, I'm retarded")
    except sr.RequestError:
        print("Problem with Google")
    return text

print(get_text())