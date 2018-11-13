# Main calibration code

import numpy
from matplotlib import pyplot as plt
import wave
import sys
import sounddevice as sd
from scipy.io import wavfile
import audioop
#from utils.py import calculatePower



def calculateMax(fs, chunk, recordingDuration, recording):
    recLength = len(recording[:,1])
    recording = recording[:,1]
    start = 0
    stop = chunk-1
    powerData = []
    while start < recLength:
        if stop >= recLength:
            stop = recLength-1
        max = recording[start]
        for i in range(start, stop):
            if recording[i] > max:
                max = recording[i]
        powerData.append(recording[i])
        start = start + chunk
        stop = stop + chunk
    return powerData

def calculatePower(fs, chunk, recordingDuration, recording):
    recording = audioop.tomono(recording, 2, 1, 1)
    recLength = len(recording)
    start = 0
    stop = chunk-1
    powerData = []
    while start < recLength:
        if stop >= recLength:
            stop = recLength-1
        rms = audioop.rms(recording[start:stop], 1)
        powerData.append(rms)
        start = start + chunk
        stop = stop + chunk
    return powerData



#def audio_callback(indata, frames, time, status):
#   volume_norm = np.linalg.norm(indata) * 10
#   print("|" * int(volume_norm))

#def calculateVolume()



# Path to assets folder to store generated sound/plot files, SPECIFIC TO COMPUTER, NEED TO CHANGE FOR PI
ASSETS_PATH = "/Users/Ryan/Developer/TurnUp/calibration/assets/"

recordingDuration = 5   # duration of recording in seconds
fs = 44100                # sampling frequency
chunk = 1024

# Set default values to be consistent through repeated use
sd.default.samplerate = fs
sd.default.channels = 2

# Record
myrecording = sd.rec(int(recordingDuration * fs))
sd.wait()   # wait to return until recording finished
print("Finished Recording")



powerData = calculateMax(fs, chunk, recordingDuration, myrecording)

    
    
# Write recording to wav file
wavfile.write(ASSETS_PATH + 'recording.wav', 44100, myrecording)

# Read WAV file and plot
samplerate, data = wavfile.read(ASSETS_PATH + 'recording.wav')
times = numpy.arange(len(data))/float(samplerate)


plt.figure(figsize=(30, 4))
plt.fill_between(times, data[:,0], data[:,1], color='k') 
plt.xlim(times[0], times[-1])
plt.xlabel('time (s)')
plt.ylabel('amplitude')
# You can set the format by changing the extension
# like .pdf, .svg, .eps
plt.savefig(ASSETS_PATH + 'plot.png', dpi=100)


plt.figure(figsize=(30,4))
plt.plot(powerData)
plt.show()