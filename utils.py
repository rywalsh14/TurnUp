import pyaudio
import numpy as np

# use this to query and display available audio devices
def showDevices(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        print("Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

# finds and returns the audio input device port
def getInputDeviceID(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
        #if "C-Media USB Headphone Set" in name:
        if "USB Audio Device" in name:
            return i
    return -1

# finds and returns the mic device port
def getMicDeviceID(audio):
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
        if "USB audio CODEC" in name:
            return i
    return -1

# returns a linspace of time values that given an array of sample points so that they may be graphed over time
def getTimeValues(rate, chunk, numPoints):
    numSamples = numPoints * chunk
    totalTime = numSamples/rate
    t = np.linspace(0, totalTime, numPoints)
    return t
