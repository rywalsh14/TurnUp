# Main calibration code

import numpy
from matplotlib import pyplot as plt
import wave
import sys
import sounddevice as sd
from scipy import signal
from scipy.io import wavfile
import audioop

def calculateAverage(fs, chunk, recording):
	recLength = len(recording)
	start = 0
	stop = chunk-1
	increment = int(chunk/4)
	avgData = []
	while start < recLength:
		if stop >= recLength:
			stop = recLength-1
		avg = audioop.rms(abs(recording[start:stop]),4)
		avgData.append(avg)
		start += increment
		stop += increment
	return avgData
"""
def calibrationGraph(micData, inputData):
    avgMicData = calculateAverage(fs, chunk, micData)
    avgInputData = calculateAverage(fs, chunk, inputData)
    





return 0
"""

##def calculateAverage(fs, chunk, recording):
##	recLength = len(recording)
##	print (recLength)
##	start = 0
##	stop = chunk-1
##	avgData = []
##	while start<recLength:
##            avg = audioop.avg(recording[start:stop], 1)
##            start += chunk
##            stop += chunk
##            chunk += chunk
##            avgData.append(avg)
##	return avgData
##	while start < recLength:
##		if stop >= recLength:
##			stop = recLength-1
##		rms = audioop.rms(recording[start:stop],1)
##		powerData.append(rms)
		
	    


# Path to assets folder to store generated sound/plot files, SPECIFIC TO COMPUTER, NEED TO CHANGE FOR PI
ASSETS_PATH = "/home/pi/Developer/TurnUp/calibration/assets/"

recordingDuration = 5   # duration of recording in seconds
fs = 44100              # sampling frequency
chunk = 2048

print(sd.query_devices())

# Set default values to be consistent through repeated use
#sd.default.device = 'C-Media USB Headphone Set'
sd.default.samplerate = fs
sd.default.channels = 1

# Record
print("Starting Recording")
myrecording = sd.rec(int(recordingDuration * fs))
sd.wait()   # wait to return until recording finished
print("Finished Recording")
print(myrecording)
#Stream
stream = sd.Stream(samplerate=fs, device=3, channels=1)
stream.start()

# Filter Recording
#h = signal.firwin(numtaps=250, cutoff=100, nyq=fs/2)
#filteredRecording = numpy.ascontiguousarray(signal.lfilter(h, 1.0, myrecording, zi=None))
#print(filteredRecording)
#powerData = calculatePower(fs, chunk, filteredRecording)
avgData = calculateAverage(fs, chunk, myrecording)
# Playback on loop
print(sd.query_devices())



rstream = stream.write(10000)


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
plt.plot(avgData)
plt.show()


while True:
	sd.play(rstream)
	sd.wait()

stream.stop()