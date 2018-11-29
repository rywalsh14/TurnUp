import pyaudio
import numpy as np

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

def getTimeValues(rate, chunk, numPoints):
    numSamples = numPoints * chunk
    totalTime = numSamples/rate
    t = np.linspace(0, totalTime, numPoints)
    return t
