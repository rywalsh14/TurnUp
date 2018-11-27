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
RECORD_SECONDS = 10
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

def getInputDeviceID(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
        if "C-Media USB Headphone Set" in name:
            return i
    return -1

def getMicDeviceID(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
        if "USB audio CODEC" in name:
            return i
    return -1



calibrateWave = wave.open("calibration.wav", 'rb')
calibratePowerData = []
micPowerData = []

scale = 1
def input_callback(in_data, frame_count, time_info, status):
    calibrateData = calibrateWave.readframes(CHUNK)
    calibratePower = audioop.rms(calibrateData, 2)
    calibratePowerData.append(calibratePower)
    #multData = audioop.mul(calibrateData, 2, scale)
    return(calibrateData, pyaudio.paContinue)

def mic_callback(mic_data, frame_count, time_info, status):
    calibrateData = calibrateWave.readframes(CHUNK)
    calibratePower = audioop.rms(calibrateData, 2)
    calibratePowerData.append(calibratePower)
    micPower = audioop.rms(mic_data, 2)
    micPowerData.append(micPower)
    return(calibrateData, pyaudio.paContinue)

# Begin main thread of code
audio = pyaudio.PyAudio()

# FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
# FOR PI - input audio has device ID 2, mic audio has device ID 3
# Open input stream source


# Open mic stream souce
micStream = audio.open(format=FORMAT, 
                    input_device_index=getMicDeviceID(audio),
                    channels=1,
                    rate=RATE, 
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=mic_callback)




micStream.start_stream()

while micStream.is_active():
    print("Starting recording")
    time.sleep(RECORD_SECONDS)
    micStream.stop_stream()


micStream.close()
audio.terminate()


lowerBound = min(calibratePowerData)
upperBound = max(calibratePowerData)
m, b = np.polyfit(calibratePowerData, micPowerData[0:len(calibratePowerData)], 1)
x = np.linspace(lowerBound, upperBound)
y = []
for i in range(0, len(x)):
    y.append(m*x[i]+b)

plt.figure(figsize=(30,4))
plt.plot(micPowerData)
plt.figure(figsize=(30,4))
plt.plot(calibratePowerData)



plt.figure(figsize=(30,4))
plt.plot(calibratePowerData, micPowerData[0:len(calibratePowerData)], 'ro')
plt.plot(x, y, 'b-')
plt.show()