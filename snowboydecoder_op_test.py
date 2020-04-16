from SnowboyDependencies import snowboydecoder_op as snowboydecoder

hotword_path = "SnowboyDependencies/Wumbo.pmdl"
key = '63NBK27X2KH7IW6SBO3LDC644SF7MGJ5'

def detected_callback():
    text = detector.get_stt(key)
    print(text)
        
detector = snowboydecoder.HotwordDetector(hotword_path, sensitivity=0.42)
detector.wait_for_hotword(detected_callback=detected_callback, sleep_time=0.01)

#to save wav 
# dattt =  adt.get_wav_data()
# file = open('TEMPTEMO.wav', 'wb')
# file.write(dattt)
# file.close