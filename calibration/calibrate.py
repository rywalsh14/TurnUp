# Main calibration code

import numpy
from matplotlib import pyplot as plt
import wave
import sys
import sounddevice as sd
from scipy.io import wavfile

# SPECIFIC TO COMPUTER, NEED TO CHANGE FOR PI
ASSETS_PATH = "/Users/Ryan/Developer/TurnUp/calibration/assets/"

recordingDuration = 5   # duration of recording in seconds
fs = 44100              # sampling frequency

# Set default values to be consistent through repeated use
sd.default.samplerate = fs
sd.default.channels = 2

# Record
myrecording = sd.rec(int(recordingDuration * fs))
sd.wait()   # wait to return until recording finished
print("Finished Recording")

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
plt.show()