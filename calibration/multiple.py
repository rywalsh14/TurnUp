import pyaudio
import wave

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
INPUT_FILENAME = "input.wav"
MIC_FILENAME = "mic.wav"

# use this to query and display available audio devices
def showDevices(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        print("Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

def playWavFile(fileName, chunk):
    f = wave.open(r"/Users/Ryan/Developer/TurnUp/calibration/" + fileName,"rb")  
    #instantiate PyAudio  
    p = pyaudio.PyAudio()  
    #open stream  
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                    channels = f.getnchannels(),  
                    rate = f.getframerate(),  
                    output = True)  
    #read data  
    data = f.readframes(chunk)  

    #play stream
    while data:  
        stream.write(data)  
        data = f.readframes(chunk)  

    #stop stream  
    stream.stop_stream()  
    stream.close()  

    #close PyAudio  
    p.terminate()
    return


# Begin main thread of code
audio = pyaudio.PyAudio()

# FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
# Open input stream source
inputStream = audio.open(format=FORMAT, 
                    input_device_index=0,
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    frames_per_buffer=CHUNK)


# Open mic stream souce
micStream = audio.open(format=FORMAT, 
                    input_device_index=2,
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    frames_per_buffer=CHUNK)




print("recording...")
inputFrames = []
micFrames = []
 
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    inputData = inputStream.read(CHUNK)
    micData = micStream.read(CHUNK)
    inputFrames.append(inputData)
    micFrames.append(micData)

print("finished recording")
 
# stop Recording
inputStream.stop_stream()
micStream.stop_stream()
inputStream.close()
micStream.close()
audio.terminate()

# write input wav file
waveFile = wave.open(INPUT_FILENAME, 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(inputFrames))
waveFile.close()

# write mic wav file
waveFile = wave.open(MIC_FILENAME, 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(micFrames))
waveFile.close()


while True:
    print("Playing Input Recording...")
    playWavFile(INPUT_FILENAME, CHUNK)
    print("Playing Mic Recording...")
    playWavFile(MIC_FILENAME, CHUNK)