import pyaudio
import wave
from matplotlib import pyplot as plt
import sys
from scipy import signal
from scipy.io import wavfile
import audioop
import numpy as np
import time
from calibrate import calibrate

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
LISTEN_SECONDS = 10

THRESHOLD = 1.5
MAX_SCALE = 16

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
    second = False
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
        if "C-Media USB Headphone Set" in name:
            return i
    return -1

def getMicDeviceID(audio):
    second = False
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
        if "USB audio CODEC" in name:
            return i
    return -1

def getTimeValues(rate, chunk, numPoints):
    numSamples = numPoints * chunk
    totalTime = numSamples/rate
    t = np.linspace(0, totalTime, numPoints)
    return t

print("Welcome to TurnUp!")
input("Press \'Enter\' to begin calibration")

M, B = calibrate(plot=True)
print("Completed calibration stage and received the following parameters:")
print("\tM = " + str(M))
print("\tB = " + str(B))

input("Press \'Enter\' to begin listening")

# buffers to hold x points of input/mic power, where x is the window size of the power we want to average over
inputPowerBuffer = []
micPowerBuffer = []

inputPowerData = []
micPowerData = []

micPower = 0

expectedMicPowerData = []

# MIGHT NEED TO CHANGE INIT
avgExpectedMicPower = 0
avgMicPower = 0


#powerDiffAvg = 0
#powerDiffData = []

#FOR Visualization Purposes
avgExpectedMicPowerData = []
avgMicPowerData = []


scale = 1
scaleData = []
ratioData = []
def input_callback(in_data, frame_count, time_info, status):
    global avgExpectedMicPower, avgMicPower, scale
    
    in_data = audioop.mul(in_data, 2, scale)
    
    inputPower = audioop.rms(in_data, 2)
    inputPowerData.append(inputPower)
    
    expectedMicPower = M*inputPower + B
    expectedMicPowerData.append(expectedMicPower)
    
    avgExpectedMicPower = 0.01*expectedMicPower + 0.99*avgExpectedMicPower
    avgMicPower = 0.01*micPower + 0.99*avgMicPower
    avgExpectedMicPowerData.append(avgExpectedMicPower)
    avgMicPowerData.append(avgMicPower)
    
    ratio = avgMicPower/avgExpectedMicPower
    ratioData.append(ratio)

    if ratio > THRESHOLD:
        scale = min(scale+0.5, MAX_SCALE)
        scale += 0.5
    elif scale > 1:
        scale -= 0.5
    scaleData.append(scale)
    
    #powerDiff = micPower - expectedMicPower
    #powerDiffData.append(powerDiff)
    
    multData = audioop.mul(in_data, 2, scale)
    return(in_data, pyaudio.paContinue)

def mic_callback(mic_data, frame_count, time_info, status):
    global micPower
    micPower = audioop.rms(mic_data, 2)
    micPowerData.append(micPower)
    return(mic_data, pyaudio.paContinue)

# Begin main thread of code
audio = pyaudio.PyAudio()

# FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
# FOR PI - input audio has device ID 2, mic audio has device ID 3
# Open input stream source
inputStream = audio.open(format=FORMAT, 
                    input_device_index=getInputDeviceID(audio),
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=input_callback)


# Open mic stream souce
micStream = audio.open(format=FORMAT, 
                    input_device_index=getMicDeviceID(audio),
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=mic_callback)

inputStream.start_stream()
micStream.start_stream()

while inputStream.is_active():
    print("Beginning listening...")
    time.sleep(LISTEN_SECONDS)
    inputStream.stop_stream()

micStream.stop_stream()
micStream.close()
inputStream.close()
audio.terminate()

print("Finished listening")

# Power data plot
micPowerTimeVals = getTimeValues(RATE, CHUNK, len(micPowerData))
expectedMicPowerTimeVals = getTimeValues(RATE, CHUNK, len(expectedMicPowerData))
micPowerFig = plt.figure(figsize=(30,4))
micPowerFig.suptitle('Mic Power & Expected Mic Power over Time', fontsize=14, fontweight='bold')
micPowerPlot, = plt.plot(micPowerTimeVals, 
                         micPowerData,
                         label="Actual Mic Power")
expMicPowerPlot, = plt.plot(expectedMicPowerTimeVals, 
                            expectedMicPowerData,
                            label="Expected Mic Power")
plt.xlabel('Time (s)')
plt.ylabel('UNITS')
plt.legend(handles=[micPowerPlot, expMicPowerPlot])

# Plot of moving average of power
avgMicPowerTimeVals = getTimeValues(RATE, CHUNK, len(avgMicPowerData))
avgExpectedMicPowerTimeVals = getTimeValues(RATE, CHUNK, len(avgExpectedMicPowerData))
movingAvgFig = plt.figure(figsize=(30,4))
movingAvgFig.suptitle('Moving Averages of Mic Power & Expected Mic Power over Time', fontsize=14, fontweight='bold')
avgMicPowerPlot, = plt.plot(avgMicPowerTimeVals, 
                            avgMicPowerData,
                            label="Mic Power Moving Average")
avgExpMicPowerPlot, = plt.plot(avgExpectedMicPowerTimeVals,
                               avgExpectedMicPowerData,
                               label="Expected Mic Power Moving Average")
plt.xlabel('Time (s)')
plt.ylabel('UNITS')
plt.legend(handles=[avgMicPowerPlot, avgExpMicPowerPlot])

"""
# Plot of the scale factor over time
scaleTimeVals = getTimeValues(RATE, CHUNK, len(scaleData))
scaleFig = plt.figure(figsize=(30,4))
scaleFig.suptitle('Scale Factor over Time', fontsize=14, fontweight='bold')
plt.plot(scaleTimeVals, scaleData)
plt.xlabel('Time (s)')
plt.ylabel('Magnitude')
"""

# Plot of scale factor & ratio over time on same plot
scaleTimeVals = getTimeValues(RATE, CHUNK, len(scaleData))
ratioTimeVals = getTimeValues(RATE, CHUNK, len(ratioData))
scaleRatioFig = plt.figure(figsize=(30,4))
scaleRatioFig.suptitle('Scale Factor over Time', fontsize=14, fontweight='bold')


# First plot ratio
color = 'tab:red'
ax1 = scaleRatioFig.add_subplot(111)
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Ratio Magnitude', color=color)
ax1.plot(ratioTimeVals, ratioData, color=color)
ax1.tick_params(axis='y', labelcolor=color)

# Next plot a line on the threshold
threshLine = []
for i in range (0, len(ratioTimeVals)):
    threshLine.append(THRESHOLD)
plt.plot(ratioTimeVals, threshLine, color="gray", linestyle='dashed')

ax2 = ax1.twinx()

# Then plot scale
color = "tab:blue"
ax2.set_ylabel('Scale Magnitude', color=color)
ax2.plot(scaleTimeVals, scaleData, color=color)
ax2.tick_params(axis='y', labelcolor=color)

plt.show()