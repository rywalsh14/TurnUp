import sys, os
sys.path.append(os.path.abspath(".."))
import pyaudio
import wave
from matplotlib import pyplot as plt
from scipy import signal
from scipy.io import wavfile
import audioop
import numpy as np
import time
import json
from utils import getInputDeviceID, getMicDeviceID, getTimeValues
import sounddevice as sd


MIC_FORMAT = pyaudio.paInt16
INPUT_FORMAT = pyaudio.paInt24
CHANNELS = 1
RATE = 44100
CHUNK = 512

CALIBRATION_WAVE_FILE = "/home/pi/Developer/TurnUp/calibration/calibration.wav"

# read the wav file into a numpy array so that this array may be played as a sound device object
cal_fs, cal_array = wavfile.read(CALIBRATION_WAVE_FILE)

# initialize the mic intensity data array
micIntensityData = []

# initialize cal intensity array
calibrateIntensityData = []

def resetCalibrateData():
    global micIntensityData, calibrateIntensityData
    micIntensityData = []
    calibrateIntensityData = []


def mic_callback(mic_data, frame_count, time_info, status):
    micIntensity = audioop.rms(mic_data, 2)    # take rms over this chunk of mic data
    micIntensityData.append(micIntensity)
    return(mic_data, pyaudio.paContinue)


def input_callback(in_data, frame_count, time_info, status):
    calibrateIntensity = audioop.rms(in_data, 2)    # take rms over this chunk of mic data
    calibrateIntensityData.append(calibrateIntensity)
    return(in_data, pyaudio.paContinue)
    

def calibrate(plot=False):
    os.system("amixer set PCM 80%")     # set the internal pi volume control to 35 (somehow 74% results in 35)
    audio = pyaudio.PyAudio()

    # FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
    # FOR PI - input audio has device ID 2, mic audio has device ID 3
    # Open input stream source
    
    # Open mic stream souce
    micStream = audio.open(format=MIC_FORMAT, 
                        input_device_index=getMicDeviceID(audio),
                        channels=1,
                        rate=RATE, 
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=mic_callback)
    
    inputStream = audio.open(format=INPUT_FORMAT, 
                        input_device_index=getInputDeviceID(audio),
                        channels=CHANNELS,
                        rate=RATE, 
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=input_callback)
    
    micStream.start_stream()
    inputStream.start_stream()
    
    sd.play(cal_array, cal_fs)
    sd.wait()

    micStream.close()
    audio.terminate()

    print("Finished listening to calibration signal...")
    
    
    # get linear relationship... get min length first so dimensions match in the linear fit
    minLength = min(len(calibrateIntensityData), len(micIntensityData))
    
    #scaledDownMinLength = int(0.9*minLength)
    
    m, b = np.polyfit(calibrateIntensityData[0:minLength], micIntensityData[0:minLength], 1)
    #m *= 1.1
    
    # save M and B to calibration_parameters.json
    with open('calibration_parameters.json', 'w') as outfile:
        json.dump({'M': m, 'B': b}, outfile, sort_keys=True, indent=4)
    
    if plot:
        lowerBound = min(calibrateIntensityData)
        upperBound = max(calibrateIntensityData)
        print("Generating graphs...")
        x = np.linspace(lowerBound, upperBound)
        y = []
        for i in range(0, len(x)):
            y.append(m*x[i]+b)

        micTimeValues = getTimeValues(RATE, CHUNK, len(micIntensityData))
        # Mic power over time plot
        micIntensityFig = plt.figure(figsize=(30,4))
        micIntensityFig.suptitle('Mic Intensity over Time', fontsize=14, fontweight='bold')
        plt.plot(micTimeValues, micIntensityData)
        plt.xlabel('Time (s)')
        plt.ylabel('Relative Fraction of Maximum Intensity')

        calibrateTimeValues = getTimeValues(RATE, CHUNK, len(calibrateIntensityData))
        # Calibrate signal power over time plot
        calibrateIntensityFig = plt.figure(figsize=(30,4))
        calibrateIntensityFig.suptitle('Calibrate Signal Intensity over Time', fontsize=14, fontweight='bold')
        plt.plot(calibrateTimeValues, calibrateIntensityData)
        plt.xlabel('Time (s)')
        plt.ylabel('Relative Fraction of Maximum Intensity')

        # Mic Pickup Power vs. Input Signal Power graph
        powerFig = plt.figure(figsize=(30,4))
        powerFig.suptitle('Mic Pickup Intensity vs. Input Signal Intensity', fontsize=14, fontweight='bold')
        powerDataPoints, = plt.plot(calibrateIntensityData[0:minLength], 
                                   micIntensityData[0:minLength], 
                                   'o',
                                   color="orange",
                                   label="Intensity Data Points")
        bestFit, = plt.plot(x, 
                           y, 
                           'b-',
                           label=("Best Fit Line\ny=%.4fx+%.4f" % (m,b)))
        plt.xlabel('Relative Fraction of Maximum Intensity')
        plt.ylabel('Relative Fraction of Maximum Intensity')
        plt.legend(handles=[powerDataPoints, bestFit])
        print("Done!")
        plt.show()
        
    resetCalibrateData()
    return (m, b)    


# ------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------- #

if __name__ == "__main__": calibrate()
#
#    # Begin main thread of code
#    audio = pyaudio.PyAudio()
#
#    # FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
#    # FOR PI - input audio has device ID 2, mic audio has device ID 3
#    # Open input stream source
#
#
#    # Open mic stream souce
#    micStream = audio.open(format=FORMAT,
#                        input_device_index=getMicDeviceID(audio),
#                        channels=1,
#                        rate=RATE,
#                        input=True,
#                        output=True,
#                        frames_per_buffer=CHUNK,
#                        stream_callback=mic_callback)
#
#
#
#
#    micStream.start_stream()
#
#    while micStream.is_active():
#        print("Beginning calibration...")
#        time.sleep(RECORD_SECONDS)
#        micStream.stop_stream()
#
#    print("Finished calibrating...")
#
#    micStream.close()
#    audio.terminate()
#
#    print("Generating graphs...")
#    lowerBound = min(calibratePowerData)
#    upperBound = max(calibratePowerData)
#    m, b = np.polyfit(calibratePowerData, micPowerData[0:len(calibratePowerData)], 1)
#    x = np.linspace(lowerBound, upperBound)
#    y = []
#    for i in range(0, len(x)):
#        y.append(m*x[i]+b)
#
#
#    micTimeValues = getTimeValues(RATE, CHUNK, len(micPowerData))
#    # Mic power over time plot
#    micPowerFig = plt.figure(figsize=(30,4))
#    micPowerFig.suptitle('Mic Power over Time', fontsize=14, fontweight='bold')
#    plt.plot(micTimeValues, micPowerData)
#    plt.xlabel('Time (s)')
#    plt.ylabel('UNITS')
#
#    calibrateTimeValues = getTimeValues(RATE, CHUNK, len(calibratePowerData))
#    # Calibrate signal power over time plot
#    calibratePowerFig = plt.figure(figsize=(30,4))
#    calibratePowerFig.suptitle('Calibrate Signal Power over Time', fontsize=14, fontweight='bold')
#    plt.plot(calibrateTimeValues, calibratePowerData)
#    plt.xlabel('Time (s)')
#    plt.ylabel('UNITS')
#
#    # Mic Pickup Power vs. Input Signal Power graph
#    powerFig = plt.figure(figsize=(30,4))
#    powerFig.suptitle('Mic Pickup Power vs. Input Signal Power', fontsize=14, fontweight='bold')
#    powerDataPoints, = plt.plot(calibratePowerData,
#                               micPowerData[0:len(calibratePowerData)],
#                               'o',
#                               color="orange",
#                               label="Power Data Points")
#    bestFit, = plt.plot(x,
#                       y,
#                       'b-',
#                       label=("Best Fit Line\ny=%.4fx+%.4f" % (m,b)))
#    plt.xlabel('UNITS')
#    plt.ylabel('UNITS')
#    plt.legend(handles=[powerDataPoints, bestFit])
#    print("Done!")
#    plt.show()
