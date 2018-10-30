# Main calibration code

import pyaudio
import struct
import numpy as np

 
CHUNK = 1024 * 4         	# samples per frame
FORMAT = pyaudio.paInt16 	# audio format (bytes per sample)
CHANNELS = 1               	# single channel for microphone
RATE = 44100                # samples per second

 
 
p = pyaudio.PyAudio()
 
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

while True:
    data = stream.read(CHUNK)					                #reading input	
    data_int = struct.unpack(str(2 * CHUNK) + 'B', data) 	#converts bytes to integers
    data_int	
