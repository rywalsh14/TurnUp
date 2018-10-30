# Main calibration code

import numpy
import sounddevice as sd

recordingDuration = 5   # duration of recording in seconds
fs = 44100              # sampling frequency

# Set default values to be consistent through repeated use
sd.default.samplerate = fs
sd.default.channels = 1

myrecording = sd.rec(int(recordingDuration * fs))

sd.wait()               # wait to return until recording finished
print("Finished Recording")

sd.play(myrecording)
for i in myrecording:
    print(i)