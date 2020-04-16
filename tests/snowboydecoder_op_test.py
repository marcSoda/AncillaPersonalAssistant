from SnowboyDependencies import snowboydecoder_op as snowboydecoder

hotword_path = "SnowboyDependencies/Wumbo.pmdl"

def detected_callback():
    text = detector.get_stt()
    print(text)
    text2 = detector.get_stt()
    print(text2)
        
detector = snowboydecoder.HotwordDetector(hotword_path, sensitivity=0.42)
detector.wait_for_hotword(detected_callback=detected_callback, sleep_time=0.01)

#to save wav 
# dattt =  adt.get_wav_data()
# file = open('TEMPTEMO.wav', 'wb')
# file.write(dattt)
# file.close