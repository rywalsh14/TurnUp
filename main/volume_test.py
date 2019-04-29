import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 7629

# Split an integer input into a two byte array to send via SPI
def write_pot(input):
    msb = (input >> 8)
    lsb = input & 0xFF
    spi.xfer([msb, lsb])
    

# Repeatedly switch a MCP4151 digital pot off then on
while True:
    write_pot(0x11E6)
    time.sleep(2)
    write_pot(0x1100)
    time.sleep(2)


#write_pot(0x1100)
"""
spi = spidev.SpiDev()
spi.open(0, 1)
spi.max_speed_hz = 976000

def write_pot(input):
    msb = input >> 8
    lsb = input & 0xFF
    spi.xfer([msb, lsb])

while True:
    #for i in range(0x00, 0x1FF, 1):
     #   write_pot(i)
      #  time.sleep(.005)
    for i in range(0x1133, 0x1100, -1):
        write_pot(i)
        time.sleep(.05)
       
"""