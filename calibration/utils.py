# Library for general utilities to work with audio
import audioop

# calculates power over a sampled signal in increments of a single chunk
def calculatePower(fs, chunk, recordingDuration, recording):
    recLength = len(recording[:,1])
    start = 0
    stop = chunk-1
    powerData = []
    while start < recLength:
        if stop >= reclength:
            stop = reclength-1
        rms = audioop.rms(recording[start:stop], 2)
        powerData.append(rms)
        start = start + chunk
        stop = stop + chunk
    return powerData