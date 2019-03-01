import sys, os
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../calibration"))
import pyaudio
import wave
from matplotlib import pyplot as plt
from scipy import signal
from scipy.io import wavfile
from termcolor import colored
import audioop
import numpy as np
import time
import json
import spidev
from calibrate import calibrate
from utils import getInputDeviceID, getMicDeviceID, getTimeValues


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
LISTEN_SECONDS = 30

THRESHOLD = 2
sensitivity = 5



sensitivityMap = {
    1: 4096,
    2: 2048,
    3: 1024,
    4: 512,
    5: 256
}





CHUNK = sensitivityMap[sensitivity]



# potentiometer base value & strength percentage
BASE_POT_VALUE = 240
BASE_STRENGTH_PERCENTAGE = (255 - BASE_POT_VALUE)/255

# MIN pot value corresponds to MAX amplification
# Essentially this is an amplification ceiling
MIN_POT_VALUE = 0
pot_value = BASE_POT_VALUE

# instantiate the spi
spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 7629

# Split integer pot value into a two byte array to send via SPI
def write_pot_value(pot_value):
    spi_data = pot_value + 4352    # 4352 = 0x1100, which are the spi command bits we need to append to the pot value
    msb = (spi_data >> 8)
    lsb = spi_data & 0xFF
    spi.xfer([msb, lsb])


# given a value that is assigned to the digital potentiometer (resulting in amplification):
# calculate a corresponding scale value, which will be factored into the EXPECTED mic power calculation.
# Essentially: this helps us in calculating expected mic power when the output is being amplified analogly.
# This is necessary b/c with analog amplification, we don't have any info besides the pot value to base expected mic power off of
# This exploits the fact that pot value relates linearly to amplification
def convertPotValueToScale(new_pot_value):
    global BASE_POT_VALUE, BASE_STRENGTH_PERCENTAGE
    new_strength_percentage = (255 - new_pot_value)/255
    return new_strength_percentage/BASE_STRENGTH_PERCENTAGE


write_pot_value(BASE_POT_VALUE)







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

# Calibrate wrapper with print statements for user
def runCalibration():
    # Run through calibration process
    input("Press \'Enter\' to begin calibration")
    m, b = calibrate(plot=True)
    print("Completed calibration stage and received the following parameters:")
    print("\tM = " + str(m))
    print("\tB = " + str(b))
    return m, b

# Converts user yes/no response to boolean value
def readYesOrNo(input):
    responses = {
        "YES": True,
        "Yes": True,
        "yes": True,
        "Y": True,
        "y": True,
        "NO": False,
        "No": False,
        "no": False,
        "N": False,
        "n": False
    }
    if input in responses:
        return responses[input]
    return None

outputPowerData = []

def input_callback(in_data, frame_count, time_info, status):
    global avgExpectedMicPower, avgMicPower, scale, pot_value
    
    
    
    
    
    scale = convertPotValueToScale(pot_value)        # calculate expected scale from pot value
    out_data = audioop.mul(in_data, 2, scale)        # calculate expected out data by multiplying the input data by the scale factor
    outputPower = audioop.rms(out_data, 2)            # calculate the output power
    outputPowerData.append(outputPower) 
    
    
    #in_data = audioop.mul(in_data, 2, scale)
    
    
    expectedMicPower = M*outputPower+B
    expectedMicPowerData.append(expectedMicPower)
    
    
    avgExpectedMicPower = 0.01*expectedMicPower + 0.99*avgExpectedMicPower
    avgMicPower = 0.01*micPower + 0.99*avgMicPower
    avgExpectedMicPowerData.append(avgExpectedMicPower)
    avgMicPowerData.append(avgMicPower)
    
    ratio = avgMicPower/avgExpectedMicPower
    ratioData.append(ratio)
    
    if ratio > THRESHOLD:
        pot_value = max(pot_value-1, MIN_POT_VALUE)
        write_pot_value(pot_value)
    elif pot_value < BASE_POT_VALUE:
        pot_value += 1
        write_pot_value(pot_value)
    scaleData.append(scale)
    potValData.append(pot_value)
    
    return(in_data, pyaudio.paContinue)

def mic_callback(mic_data, frame_count, time_info, status):
    global micPower
    micPower = audioop.rms(mic_data, 2)
    micPowerData.append(micPower)
    return(mic_data, pyaudio.paContinue)




    















spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 7629

print("Welcome to TurnUp!")
print("Would you like to recalibrate? (Y/N): ")
# Prompt user for if they would like to recalibrate
recalibrate = readYesOrNo(input(""))
if recalibrate == None:
    while recalibrate == None:
        print("Must answer \'YES\' or \'NO\'!")
        recalibrate = readYesOrNo(input("Would you like to recalibrate? (Y/N): "))

if recalibrate:
    M, B = runCalibration()
else:
    print('Okay! Loading last saved parameters from \'calibration_parameters.json\'...')
    # Load calibration parameters from calibration_parameters.json
    try:
        with open('calibration_parameters.json') as parameterFile:
            parameters = json.load(parameterFile)
        M = parameters['M']
        B = parameters['B']
        print(colored("Success!", "green"))
        print("Loaded the following parameters:")
        print("\tM = " + str(M))
        print("\tB = " + str(B))
    except IOError as e:
        # No previous calibration_parameters.json file found, so run the calibration stage
        print(colored("Failed to find previously saved parameters.", "red"))
        print(colored("Calibration necessary", "red"))
        M, B = runCalibration()

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


#FOR Visualization Purposes
avgExpectedMicPowerData = []
avgMicPowerData = []


scale = 1
scaleData = []
potValData = []
ratioData = []


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
                    output=False,
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
micPowerFig = plt.figure(figsize=(30,10))
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
movingAvgFig = plt.figure(figsize=(30,10))
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

# Plot of scale factor & ratio over time on same plot
scaleTimeVals = getTimeValues(RATE, CHUNK, len(scaleData))
ratioTimeVals = getTimeValues(RATE, CHUNK, len(ratioData))
potTimeVals = getTimeValues(RATE, CHUNK, len(potValData))

scaleRatioFig = plt.figure(figsize=(30,10))
scaleRatioFig.suptitle('Scale Factor and Avg. Expected Mic Power to Avg Mic Power Ratio over Time', fontsize=14, fontweight='bold')

# First plot ratio
plt.subplot(311)
plt.plot(ratioTimeVals, ratioData, color="tab:red")
plt.ylabel('Ratio Magnitude')

# Next plot a line on the threshold
threshLine = []
for i in range (0, len(ratioTimeVals)):
    threshLine.append(THRESHOLD)
plt.plot(ratioTimeVals, threshLine, color="gray", linestyle='dashed')

# Now plot the scale on a separate Subplot
plt.subplot(312)
plt.plot(scaleTimeVals, scaleData, color="tab:blue")
plt.xlabel('Time (s)')
plt.ylabel('Scale Magnitude')

plt.subplot(313)
plt.plot(potTimeVals, potValData, color="tab:green")
plt.xlabel('Time (s)')
plt.ylabel('Potentiometer Value Magnitude')

plt.show()


