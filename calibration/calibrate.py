# Main calibration code

import numpy
from matplotlib import pyplot as plt
import wave
import sys
import sounddevice as sd
from scipy.io import wavfile
import audioop

def calculatePower(fs, chunk, recording):
	recLength = len(recording)
	start = 0
	stop = chunk-1
	powerData = []
	while start < recLength:
		if stop >= recLength:
			stop = recLength-1
		rms = audioop.rms(recording[start:stop],1)
		powerData.append(rms)
		start += chunk
		stop += chunk
	return powerData




# Path to assets folder to store generated sound/plot files, SPECIFIC TO COMPUTER, NEED TO CHANGE FOR PI
ASSETS_PATH = "/home/pi/Developer/TurnUp/calibration/assets/"

recordingDuration = 5   # duration of recording in seconds
fs = 44100              # sampling frequency
chunk = 2048

# Set default values to be consistent through repeated use
sd.default.samplerate = fs
sd.default.channels = 1

# Record
print("Starting Recording")
myrecording = sd.rec(int(recordingDuration * fs))
sd.wait()   # wait to return until recording finished
print("Finished Recording")

powerData = calculatePower(fs, chunk, myrecording)

# Playback on loop
"""
while True:
	sd.play(myrecording)
	sd.wait()
"""

# Write recording to wav file
wavfile.write(ASSETS_PATH + 'recording.wav', 44100, myrecording)

# Read WAV file and plot
samplerate, data = wavfile.read(ASSETS_PATH + 'recording.wav')
times = numpy.arange(len(data))/float(samplerate)

plt.figure(figsize=(30, 4))
plt.fill_between(times, data, color='k') 
plt.xlim(times[0], times[-1])
plt.xlabel('time (s)')
plt.ylabel('amplitude')
# You can set the format by changing the extension
# like .pdf, .svg, .eps
plt.savefig(ASSETS_PATH + 'plot.png', dpi=100)

plt.figure(figsize=(30,4))
plt.plot(powerData)
plt.show()
