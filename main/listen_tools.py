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


MIC_FORMAT = pyaudio.paInt16
INPUT_FORMAT = pyaudio.paInt24
CHANNELS = 1
RATE = 44100
CHUNK = 512

# variable to control when device should listen/stop listening
LISTEN_ACTIVE = False

# initialize threshold/sensitivity/M/B now, will be changed upon receiving user settings
THRESHOLD = 2
SENSITIVITY = 3
M=0
B=0

sensitivityMap = {
    1: 4096,
    2: 2048,
    3: 1024,
    4: 512,
    5: 256
}

# potentiometer base value & strength percentage
BASE_POT_VALUE = 240
BASE_STRENGTH_PERCENTAGE = (255 - BASE_POT_VALUE)/255

# MIN pot value corresponds to MAX amplification
# Essentially this is an amplification ceiling
MIN_POT_VALUE = 0

# initialize potentiometer value as the base pot value
pot_value = BASE_POT_VALUE

# globals to work with power data
avgExpectedMicPower = 0
avgMicPower = 0
micPower = 0

# arrays to hold data over time for graphs
inputPowerData = []
micPowerData = []
expectedMicPowerData = []
avgExpectedMicPowerData = []
avgMicPowerData = []
scaleData = []
potValData = []
ratioData = []

# Split integer pot value into a two byte array to send via SPI
def write_pot_value(pot_value):
    spi_data = pot_value + 4352    # 4352 = 0x1100, which are the spi command bits we need to append to the pot value
    msb = (spi_data >> 8)
    lsb = spi_data & 0xFF
    spi.xfer([msb, lsb])

# instantiate the spi
spi = spidev.SpiDev()
spi.open(0, 1)
write_pot_value(BASE_POT_VALUE)
spi.max_speed_hz = 7629

# Calibrate wrapper with print statements for user
def runCalibration():
    # Run through calibration process
    write_pot_value(BASE_POT_VALUE)
    m, b = calibrate(True)
    print("Completed calibration stage and received the following parameters:")
    print("\tM = " + str(m))
    print("\tB = " + str(b))
    return m, b

# given a value that is assigned to the digital potentiometer (resulting in amplification):
# calculate a corresponding scale value, which will be factored into the EXPECTED mic power calculation.
# Essentially: this helps us in calculating expected mic power when the output is being amplified analogly.
# This is necessary b/c with analog amplification, we don't have any info besides the pot value to base expected mic power off of
# This exploits the fact that pot value relates linearly to amplification
def convertPotValueToScale(new_pot_value):
    global BASE_POT_VALUE, BASE_STRENGTH_PERCENTAGE
    new_strength_percentage = (255 - new_pot_value)/255
    return new_strength_percentage/BASE_STRENGTH_PERCENTAGE
    

# input callback function to deal with audio in
# handles the input power calculation & the expected mic power calculation
def input_callback(in_data, frame_count, time_info, status):
    global avgExpectedMicPower, avgMicPower, pot_value, inputPowerData
    
    scale = convertPotValueToScale(pot_value)        # calculate expected scale from pot value
    
    inputPower = audioop.rms(in_data, 2)            # calculate the input power
    inputPowerData.append(inputPower)   
    
    expectedMicPower = M*inputPower + B             # calculate expected mic power from out power
    expectedMicPowerData.append(expectedMicPower)
    
    avgExpectedMicPower = 0.01*expectedMicPower + 0.99*avgExpectedMicPower
    avgMicPower = 0.01*micPower + 0.99*avgMicPower
    avgExpectedMicPowerData.append(avgExpectedMicPower)
    avgMicPowerData.append(avgMicPower)
    
    ratio = avgMicPower/avgExpectedMicPower
    ratioData.append(ratio)
    
    if ratio > THRESHOLD:
        # Decrement pot value --> increase amplification
        # Make sure pot value doesn't go under minimum
        pot_value = max(pot_value-1, MIN_POT_VALUE)
        write_pot_value(pot_value)
    elif pot_value < BASE_POT_VALUE:
        # If pot value lower than base (i.e. output is LOUDER than regular "no ambient noise" state,
        # Increment pot value and write it
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

# used to reset all used data for functionality/plotting, etc. so that system starts fresh on the next listen
def resetListenData():
    global inputPowerData, micPowerData, expectedMicPowerData
    global avgExpectedMicPowerData, avgMicPowerData
    global scaleData, potValData, ratioData
    global pot_value
    
    # reset the digital potentiometer
    pot_value = BASE_POT_VALUE
    write_pot_value(pot_value)
    
    # reset moving averages
    avgExpectedMicPower = 0
    avgMicPower = 0
    
    # reset all of the data arrays
    inputPowerData = []
    micPowerData = []
    expectedMicPowerData = []
    avgExpectedMicPowerData = []
    avgMicPowerData = []
    scaleData = []
    potValData = []
    ratioData = []

def stopListening():
    global LISTEN_ACTIVE
    LISTEN_ACTIVE = False

def listen(cal_slope, cal_intercept, sensitivity):
    # set the M and B parameters of the calibration graph
    global M,B, LISTEN_ACTIVE
    #M = cal_slope*1.1
    M = cal_slope
    B = cal_intercept
    
    SENSITIVITY = sensitivity
    CHUNK = sensitivityMap[SENSITIVITY]
    
    print("Set the system's sensitivity to %s\n" % (SENSITIVITY))
    
    
    # Begin main thread of code
    audio = pyaudio.PyAudio()

    # FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
    # FOR PI - input audio has device ID 2, mic audio has device ID 3
    # Open input stream source
    inputStream = audio.open(format=INPUT_FORMAT, 
                        input_device_index=getInputDeviceID(audio),
                        channels=CHANNELS,
                        rate=RATE, 
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=input_callback)


    # Open mic stream souce
    micStream = audio.open(format=MIC_FORMAT, 
                        input_device_index=getMicDeviceID(audio),
                        channels=CHANNELS,
                        rate=RATE, 
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=mic_callback)

    print("Beginning listening...")
    inputStream.start_stream()
    micStream.start_stream()
    
    LISTEN_ACTIVE = True
    
    # run until LISTEN_ACTIVE is set false by stopListening
    while LISTEN_ACTIVE:
        pass
    
    inputStream.stop_stream()
    micStream.stop_stream()
    micStream.close()
    inputStream.close()
    audio.terminate()

    print("Finished listening")

    # Power data plot
    micPowerTimeVals = getTimeValues(RATE, CHUNK, len(micPowerData))
    expectedMicPowerTimeVals = getTimeValues(RATE/CHUNK, 1, len(expectedMicPowerData))
    inputPowerTimeVals = getTimeValues(RATE/CHUNK, 1, len(inputPowerData))
    micPowerFig = plt.figure(figsize=(30,10))
    micPowerFig.suptitle('Mic Power & Expected Mic Power over Time', fontsize=14, fontweight='bold')
    micPowerPlot, = plt.plot(micPowerTimeVals, 
                             micPowerData,
                             label="Actual Mic Power")
    expMicPowerPlot, = plt.plot(expectedMicPowerTimeVals, 
                                expectedMicPowerData,
                                label="Expected Mic Power")
    inputPowerPlot, = plt.plot(inputPowerTimeVals, 
                                inputPowerData,
                                label="Input Power")
    plt.xlabel('Time (s)')
    plt.ylabel('UNITS')
    plt.legend(handles=[micPowerPlot, expMicPowerPlot, inputPowerPlot])

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
    resetListenData()
    
