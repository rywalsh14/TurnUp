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


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
RECORD_SECONDS = 10

CALIBRATION_WAVE_PATH = "../calibration/calibration.wav"

# load the calibration power data
with open('calibration_power_512.json') as calibratePowerFile:
    calDictionary = json.load(calibratePowerFile)
calibratePowerData = calDictionary['calibratePowerData']

# read the wav file into a numpy array
cal_fs, cal_array = wavfile.read("/home/pi/Developer/TurnUp/calibration/calibration.wav")

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

calibrateWave = wave.open(CALIBRATION_WAVE_PATH, 'rb')
micPowerData = []

scale = 1
def input_callback(in_data, frame_count, time_info, status):
    calibrateData = calibrateWave.readframes(CHUNK)
    calibratePower = audioop.rms(calibrateData, 2)
    calibratePowerData.append(calibratePower)
    #multData = audioop.mul(calibrateData, 2, scale)
    return(calibrateData, pyaudio.paContinue)


#chunk_count = 0
def mic_callback(mic_data, frame_count, time_info, status):
    global chunk_count
    #chunk_count +=1
    #if chunk_count == 16:
    micPower = audioop.rms(mic_data, 2)
    micPowerData.append(micPower)
    #chunk_count = 0
    return(mic_data, pyaudio.paContinue)

def calibrate(plot=True):
    # Begin main thread of code
    os.system("amixer set PCM 74%")     # set the internal pi volume control to 35 (somehow 74% results in 35)
    audio = pyaudio.PyAudio()

    # FOR MAC - built-in mic has device ID 0, USB Audio device has device ID 2
    # FOR PI - input audio has device ID 2, mic audio has device ID 3
    # Open input stream source

    
##    calibrateFile = wave.open(r"/home/pi/Developer/TurnUp/calibration/calibration.wav", "rb")
##    calibrateStream = audio.open(format = audio.get_format_from_width(calibrateFile.getsampwidth()),
##                                 channels = calibrateFile.getnchannels(),
##                                 rate = calibrateFile.getframerate(),
##                                 output = True)
    
    # Open mic stream souce
    micStream = audio.open(format=FORMAT, 
                        input_device_index=getMicDeviceID(audio),
                        channels=1,
                        rate=RATE, 
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=mic_callback)

    micStream.start_stream()

##    #read data
##    data = calibrateFile.readframes(CHUNK)
##    
##    #play stream
##    while data:
##        calibrateStream.write(data)
##        data = calibrateFile.readframes(CHUNK)
    
    sd.play(cal_array, cal_fs)
    sd.wait()

    micStream.close()
    audio.terminate()

    print(len(micPowerData))
    print(len(calibratePowerData))

    print("Finished listening to calibration signal...")
    
    # get linear relationship... get min length first so dimensions match in the linear fit
    minLength = min(len(calibratePowerData), len(micPowerData))
    m, b = np.polyfit(calibratePowerData[0:minLength], micPowerData[0:minLength], 1)
    
    # save M and B to calibration_parameters.json
    with open('calibration_parameters.json', 'w') as outfile:
        json.dump({'M': m, 'B': b}, outfile, sort_keys=True, indent=4)
    
    if plot:
        lowerBound = min(calibratePowerData)
        upperBound = max(calibratePowerData)
        print("Generating graphs...")
        x = np.linspace(lowerBound, upperBound)
        y = []
        for i in range(0, len(x)):
            y.append(m*x[i]+b)

        micTimeValues = getTimeValues(RATE, CHUNK, len(micPowerData))
        # Mic power over time plot
        micPowerFig = plt.figure(figsize=(30,4))
        micPowerFig.suptitle('Mic Intensity over Time', fontsize=14, fontweight='bold')
        plt.plot(micTimeValues, micPowerData)
        plt.xlabel('Time (s)')
        plt.ylabel('Relative Fraction of Maximum Intensity')

        calibrateTimeValues = getTimeValues(RATE, CHUNK, len(calibratePowerData))
        # Calibrate signal power over time plot
        calibratePowerFig = plt.figure(figsize=(30,4))
        calibratePowerFig.suptitle('Calibrate Signal Intensity over Time', fontsize=14, fontweight='bold')
        plt.plot(calibrateTimeValues, calibratePowerData)
        plt.xlabel('Time (s)')
        plt.ylabel('Relative Fraction of Maximum Intensity')

        # Mic Pickup Power vs. Input Signal Power graph
        powerFig = plt.figure(figsize=(30,4))
        powerFig.suptitle('Mic Pickup Intensity vs. Input Signal Intensity', fontsize=14, fontweight='bold')
        powerDataPoints, = plt.plot(calibratePowerData, 
                                   micPowerData[0:len(calibratePowerData)], 
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
