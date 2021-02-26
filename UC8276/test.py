import epaper
from machine import Pin, SPI

sck = Pin(18)
mosi = Pin(23)
cs = Pin(22)
busy = Pin(4)
rst = Pin(15)
dc = Pin(27)
miso = Pin(19)
spi = SPI(baudrate=600000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
display = epaper.EPD(spi, cs, dc, rst, busy)

display.clean()

array_size = display.array_size()
primary = bytearray(array_size)
secondary = bytearray(array_size)

for i in range(display.array_size()):
    row = int(i / 800)
    column = int((i % 50) / 2)
    box = (row + column) % 3
    
    if box == 0:
        primary[i] = 0xff
        secondary[i] = 0xff
    elif box == 1:
        primary[i] = 0xff
        secondary[i] = 0x00
    else:
        primary[i] = 0x00
        secondary[i] = 0xff  
display.display_frame(primary,secondary)
