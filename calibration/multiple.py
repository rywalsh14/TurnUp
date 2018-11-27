import pyaudio
import wave
from matplotlib import pyplot as plt
import sys
from scipy import signal
from scipy.io import wavfile
import audioop
import numpy as np
import time


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
RECORD_SECONDS = 5
INPUT_FILENAME = "input.wav"
MIC_FILENAME = "mic.wav"
POWER_WINDOW = 2048

# use this to query and display available audio devices
def showDevices(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        print("Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))


def playWavFile(fileName, chunk):
    f = wave.open(r"/home/pi/Developer/TurnUp/calibration/" + fileName,"rb")  
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



# wf = wave.open("input.wav", 'rb')

inputPowerData = []
micPowerData = []

scale = 1
def input_callback(in_data, frame_count, time_info, status):
    inputPower = audioop.rms(in_data, 2)
    inputPowerData.append(inputPower)
    multData = audioop.mul(in_data, 2, scale)
    return(multData, pyaudio.paContinue)

def mic_callback(mic_data, frame_count, time_info, status):
    micPower = audioop.rms(mic_data, 2)
    micPowerData.append(micPower)
    return(mic_data, pyaudio.paContinue)

"""
def calcPower(powerWindow, recording):
    recLength = len(recording)
    start = 0
    stop = powerWindow-1
    increment = int(powerWindow/4)
    avgData = []
    while start < recLength:
            if stop >= recLength:
                    stop = recLength-1
            avg = audioop.rms(recording[start:stop],2)
            avgData.append(avg)
            start += increment
            stop += increment
    return avgData
"""

def calcPower(powerWindow, recording):
    avgData = []
    for chunk in recording:
        avgData.append(audioop.rms(chunk, 2))
    return avgData

# Begin main thread of code
audio = pyaudio.PyAudio()

# FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
# FOR PI - input audio has device ID 2, mic audio has device ID 3
# Open input stream source
inputStream = audio.open(format=FORMAT, 
                    input_device_index=3,
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=input_callback)


# Open mic stream souce
micStream = audio.open(format=FORMAT, 
                    input_device_index=2,
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=mic_callback)



inputStream.start_stream()
micStream.start_stream()

while inputStream.is_active():
    print("Starting recording")
    time.sleep(RECORD_SECONDS)
    inputStream.stop_stream()

micStream.stop_stream()
micStream.close()
inputStream.close()
audio.terminate()

"""
plt.figure(figsize=(30,4))
plt.plot(micPowerData)
plt.figure(figsize=(30,4))
plt.plot(inputPowerData)

"""

plt.figure(figsize=(30,4))
plt.plot(inputPowerData, micPowerData[0:len(inputPowerData)], 'ro')
plt.show()


"""
print("recording...")
inputFrames = []
micFrames = []
 
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    inputData = inputStream.read(CHUNK)
    micData = micStream.read(CHUNK, exception_on_overflow=False)
    inputFrames.append(inputData)
    micFrames.append(micData)

print("finished recording")
 
# stop Recording
inputStream.stop_stream()
micStream.stop_stream()
inputStream.close()
micStream.close()
audio.terminate()


micPowerData = calcPower(POWER_WINDOW, micFrames)
inputPowerData = calcPower(POWER_WINDOW, inputFrames)


plt.figure(figsize=(30,4))
plt.plot(micPowerData)
plt.figure(figsize=(30,4))
plt.plot(inputPowerData)
plt.show()

"""


"""

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

# Playback input data and mic data
while True:
    print("Playing Input Recording...")
    playWavFile(INPUT_FILENAME, CHUNK)
    print("Playing Mic Recording...")
    playWavFile(MIC_FILENAME, CHUNK)
"""