"""
MicroPython

Driver for UC8276 based display:
http://e-paper-display.com/products_detail/productId=543.html


Code based on:
Waveshare 2.9" Black/White/Red GDEW029Z10 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer
Copyright (c) 2020 Sami Viitanen <sami.viitanen@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Example usage (update Pins to your setup):
# ==========================================
#import epaper
#from machine import Pin, SPI
#
#sck = Pin(18)
#mosi = Pin(23)
#cs = Pin(22)
#busy = Pin(4)
#rst = Pin(15)
#dc = Pin(27)
#miso = Pin(19)
#spi = SPI(baudrate=600000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
#display = epaper.EPD(spi, cs, dc, rst, busy)
#display.clean()
#
# After this you can use imageserverpython.py demo to fetch image over wifi
# connection

from micropython import const
from time import sleep_ms, sleep_us
import ustruct


BUSY = const(0)  # 0=busy, 1=idle

class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.orig_width = 400
        self.width = 400
        self.orig_height = 300
        self.height = 300
        
    def size(self, width, height):
        self.orig_width = width
        self.width = width
        self.orig_height = height
        self.height = height

    def _command(self, command, data=None):
        self.cs(0)
        self.dc(0)
        sleep_us(3)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.cs(0)
        self.dc(1)
        sleep_us(3)
        self.spi.write(data)
        self.cs(1)

    def _prepare(self):        
        self.reset()
        self.wait_until_idle()
        self._command(0x04) # SWRESET
        self.wait_until_idle()
        
        self._command(0x00, b'\x0f') # panel setting LUT from OTP£¬400x300
    
    def pixels(self):
        return self.width * self.height

    def array_size(self):
        return self.pixels() // 8;

    def wait_until_idle(self):
        self._command(0x71)
        
        while self.busy.value() == BUSY:
            self._command(0x71)
            
        sleep_us(100)

    def reset(self):
        self.rst(0)
        sleep_ms(10)
        self.rst(1)
        sleep_ms(5)
    
    def _framebuffer_data(self, buffer):
        row_size = (self.width // 8)
        rows = len(buffer) // row_size
        for i in range(rows):
            at = i * row_size
            self._data(buffer[at:(at+row_size)])
            
    def _empty_row(self):
        row_size = (self.width // 8)
        row = bytearray(row_size)
        for x in range(row_size):
            row[x] = 0xff
        return row
        

    # Set primary content from bytearray (1 bit = 1 pixel, 1 = black,
    # 0 = white). Call either set_secondary_content() or refresh after this
    def set_primary_content(self, array):        
        if (array != None):
            self._command(0x10, array)
        else:
            self._command(0x10)
            row = self._empty_row()
            for i in range(self.height):
                self._data(row)
        
        sleep_us(100)

    # Set secondary content from bytearray (1 bit = 1 pixel, 1 = white/black,
    # 0 = secondary color (red or yellow)). If you array as None, this will
    # just clear secondary color.
    # You need to call refresh() after this to update display
    def set_secondary_content(self, array, clear = False):
        if (array == None and clear == False):
            return

        if (array != None):
            self._command(0x13, array)
        elif clear:
            self._command(0x13)
            row = self._empty_row()
            for i in range(self.height):
                self._data(row)
        sleep_us(100)

    # To be used after set_primary_content (and optionally
    # set_secondary_content) to refresh display. You might want to follow
    # this with wait_until_idle()
    def refresh(self):
        self._command(0x12)
        sleep_us(100)
        self.wait_until_idle()

    def display_frame(self, primary_array, secondary_array):
        self._prepare()
        self.set_primary_content(primary_array)
        self.set_secondary_content(secondary_array, secondary_array == None)
        self.refresh()
        self.sleep()
        
        
    def clean(self):
        self._prepare()
        size = self.array_size()
        self._command(0x10)
        row = self._empty_row()
        for x in range(self.height):
            self._data(row)
        self._command(0x13)
        for x in range(self.height):
            self._data(row)
        self.refresh()
        self.sleep()

    def set_rotate(self, rotate):
        if (rotate == ROTATE_0):
            self.rotate = ROTATE_0
            self.width = self.orig_width
            self.height = self.orig_height
        elif (rotate == ROTATE_90):
            self.rotate = ROTATE_90
            self.width = self.orig_height
            self.height = self.orig_width
        elif (rotate == ROTATE_180):
            self.rotate = ROTATE_180
            self.width = self.orig_width
            self.height = self.orig_height
        elif (rotate == ROTATE_270):
            self.rotate = ROTATE_270
            self.width =self.orig_height
            self.height = self.orig_width

    def set_pixel(self, frame_buffer, x, y, colored):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == ROTATE_0):
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_90):
            point_temp = x
            x = self.orig_width - y
            y = point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_180):
            x = self.orig_width - x
            y = self.orig_height- y
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_270):
            point_temp = x
            x = y
            y = self.orig_height - point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)

    def set_absolute_pixel(self, frame_buffer, x, y, colored):
        # To avoid display orientation effects
        # use EPD_WIDTH instead of self.width
        # use EPD_HEIGHT instead of self.height
        if (x < 0 or x >= self.orig_width or y < 0 or y >= self.orig_height):
            return
        if (colored):
            frame_buffer[(x + y * self.orig_width) // 8] &= ~(0x80 >> (x % 8))
        else:
            frame_buffer[(x + y * self.orig_width) // 8] |= 0x80 >> (x % 8)

    # to wake call reset() or init()
    def sleep(self):
        self._command(0x50, b'\xf7')
        self._command(0x02)
        self.wait_until_idle()
        self._command(0x07, b'\xA5')


