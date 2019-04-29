import sys, os
sys.path.append(os.path.abspath(".."))
import spidev
import time
import audioop
import pyaudio
import numpy as np
from math import trunc
from matplotlib import pyplot as plt
from utils import getInputDeviceID, getMicDeviceID, getTimeValues

spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 7629

# Split an integer input into a two byte array to send via SPI
def write_pot(input):
    msb = (input >> 8)
    lsb = input & 0xFF
    spi.xfer([msb, lsb])
    
def mic_callback(mic_data, frame_count, time_info, status):
    micPower = audioop.rms(mic_data, 2)
    micPowerData.append(micPower)
    return(mic_data, pyaudio.paContinue)
    
def calibrate(plot=False):
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
        print("Beginning signal...")
        write_pot(0x11ff)
        time.sleep(2)
        write_pot(0x11cc)
        time.sleep(2)
        write_pot(0x1199)
        time.sleep(2)
        write_pot(0x1166)
        time.sleep(2)
        write_pot(0x1133)
        time.sleep(2)
        write_pot(0x1100)
        time.sleep(2)
        micStream.stop_stream()

    micStream.close()
    audio.terminate()
    print("Finished listening to calibration signal...")
    
    #m, b = np.polyfit(calibratePowerData, micPowerData[0:len(calibratePowerData)], 1)
    
    interval = trunc(len(micPowerData)/6)
    
    averages = []
    index = 0
    for i in range (0, 6):
        section = micPowerData[index:index+interval]
        averages.append(sum(section)/len(section))
        index += interval
        
    print(averages)
    
    print(interval)
    
    
    if plot:

        micTimeValues = getTimeValues(RATE, CHUNK, len(micPowerData))
        # Mic power over time plot
        micPowerFig = plt.figure(figsize=(30,4))
        micPowerFig.suptitle('Mic Power over Time', fontsize=14, fontweight='bold')
        plt.plot(micTimeValues, micPowerData)
        plt.xlabel('Time (s)')
        plt.ylabel('UNITS')

        plt.show()
        
    
    
    
    
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 10

calibratePowerData = []
micPowerData = []

calibrate(plot=True)
# Repeatedly switch a MCP4151 digital pot off then on

