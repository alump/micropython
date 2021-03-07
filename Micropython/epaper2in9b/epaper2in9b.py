"""
MicroPython Waveshare 2.9" Black/White/Red GDEW029Z10 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer
Copyright (c) 2019 Sami Viitanen <sami.viitanen@gmail.com>

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

# also works for black/white/yellow GDEW029C32?

# Changes made by Sami Viitanen to version from Mike Causer
# - Cleaned up memory heavy drawing methods, this is wrong place for those
# - Split display_frame to separate methods to allow memory optimization
# - Try to add deep sleep support
#
# Example usage (update Pins to your setup):
# ==========================================
# import epaper2in9b
# from machine import Pin
# from machine import SPI
#
# sck = Pin(22)
# mosi = Pin(23)
# cs = Pin(15)
# busy = Pin(25)
# rst = Pin(26)
# dc = Pin(27)
# miso = Pin(19)
# spi = SPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
# display = epaper2in9b.EPD(spi, cs, dc, rst, busy)
# display.reset()
# display.init()
#
# After this you can use imageserverpython.py demo to fetch image over wifi
# connection

from micropython import const
from time import sleep_ms
import ustruct

# Display resolution
EPD_WIDTH  = const(128)
EPD_HEIGHT = const(296)

# Display commands
PANEL_SETTING                  = const(0x00)
POWER_SETTING                  = const(0x01)
POWER_OFF                      = const(0x02)
#POWER_OFF_SEQUENCE_SETTING     = const(0x03)
POWER_ON                       = const(0x04)
#POWER_ON_MEASURE               = const(0x05)
BOOSTER_SOFT_START             = const(0x06)
DEEP_SLEEP                     = const(0x07)
DATA_START_TRANSMISSION_1      = const(0x10)
#DATA_STOP                      = const(0x11)
DISPLAY_REFRESH                = const(0x12)
DATA_START_TRANSMISSION_2      = const(0x13)
#PLL_CONTROL                    = const(0x30)
#TEMPERATURE_SENSOR_COMMAND     = const(0x40)
#TEMPERATURE_SENSOR_CALIBRATION = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51)
#TCON_SETTING                   = const(0x60)
TCON_RESOLUTION                = const(0x61)
#GET_STATUS                     = const(0x71)
#AUTO_MEASURE_VCOM              = const(0x80)
#VCOM_VALUE                     = const(0x81)
VCM_DC_SETTING_REGISTER        = const(0x82)
#PARTIAL_WINDOW                 = const(0x90)
#PARTIAL_IN                     = const(0x91)
#PARTIAL_OUT                    = const(0x92)
#PROGRAM_MODE                   = const(0xA0)
#ACTIVE_PROGRAM                 = const(0xA1)
#READ_OTP_DATA                  = const(0xA2)
CHECK_CODE                     = const(0xA5)
#POWER_SAVING                   = const(0xE3)

# Display orientation
ROTATE_0   = const(0)
ROTATE_90  = const(1)
ROTATE_180 = const(2)
ROTATE_270 = const(3)

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
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.rotate = ROTATE_0

    def _command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def init(self):
        self.reset()
        self._command(BOOSTER_SOFT_START, b'\x17\x17\x17')
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PANEL_SETTING, b'\x8F')
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x77')
        self._command(TCON_RESOLUTION, ustruct.pack(">BH", EPD_WIDTH, EPD_HEIGHT))
        self._command(VCM_DC_SETTING_REGISTER, b'\x0A')

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    # Set primary content from bytearray (1 bit = 1 pixel, 1 = black,
    # 0 = white). Call either set_secondary_content() or refresh after this
    def set_primary_content(self, array):
        if (array != None):
            self._command(DATA_START_TRANSMISSION_1)
            sleep_ms(2)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([array[i]]))
            sleep_ms(2)

    # Set secondary content from bytearray (1 bit = 1 pixel, 1 = white/black,
    # 0 = secondary color (red or yellow)). If you array as None, this will
    # just clear secondary color.
    # You need to call refresh() after this to update display
    def set_secondary_content(self, array, clear = False):
        if (array == None and clear == False):
            return

        self._command(DATA_START_TRANSMISSION_2)
        sleep_ms(2)
        for i in range(0, self.width * self.height // 8):
            if (array != None):
                self._data(bytearray([array[i]]))
            elif clear:
                self._data(bytearray(255))
        sleep_ms(2)

    # To be used after set_primary_content (and optionally
    # set_secondary_content) to refresh display. You might want to follow
    # this with wait_until_idle()
    def refresh(self):
        self._command(DISPLAY_REFRESH)

    def display_frame(self, primary_array, secondary_array):
        self.set_primary_content(primary_array)
        self.set_secondary_content(secondary_array)
        self.refresh()
        self.wait_until_idle()

    def set_rotate(self, rotate):
        if (rotate == ROTATE_0):
            self.rotate = ROTATE_0
            self.width = EPD.EPD_WIDTH
            self.height = EPD.EPD_HEIGHT
        elif (rotate == ROTATE_90):
            self.rotate = ROTATE_90
            self.width = EPD.EPD_HEIGHT
            self.height = EPD.EPD_WIDTH
        elif (rotate == ROTATE_180):
            self.rotate = ROTATE_180
            self.width = EPD.EPD_WIDTH
            self.height = EPD.EPD_HEIGHT
        elif (rotate == ROTATE_270):
            self.rotate = ROTATE_270
            self.width = EPD.EPD_HEIGHT
            self.height = EPD.EPD_WIDTH

    def set_pixel(self, frame_buffer, x, y, colored):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == ROTATE_0):
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_90):
            point_temp = x
            x = EPD.EPD_WIDTH - y
            y = point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_180):
            x = EPD.EPD_WIDTH - x
            y = EPD.EPD_HEIGHT- y
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_270):
            point_temp = x
            x = y
            y = EPD.EPD_HEIGHT - point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)

    def set_absolute_pixel(self, frame_buffer, x, y, colored):
        # To avoid display orientation effects
        # use EPD_WIDTH instead of self.width
        # use EPD_HEIGHT instead of self.height
        if (x < 0 or x >= EPD_WIDTH or y < 0 or y >= EPD_HEIGHT):
            return
        if (colored):
            frame_buffer[(x + y * EPD_WIDTH) // 8] &= ~(0x80 >> (x % 8))
        else:
            frame_buffer[(x + y * EPD_WIDTH) // 8] |= 0x80 >> (x % 8)

    # to wake call reset() or init()
    def sleep(self):
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x37')
        self._command(VCM_DC_SETTING_REGISTER, b'\x00') # to solve Vcom drop
        self._command(POWER_SETTING, b'\x02\x00\x00\x00') # gate switch to external
        self.wait_until_idle()
        self._command(POWER_OFF)

    # To wake call reset() - NEEDS TO BE TESTED
    def deepsleep(self):
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x37')
        self._command(VCM_DC_SETTING_REGISTER, b'\x00') # to solve Vcom drop
        self._command(POWER_SETTING, b'\x02\x00\x00\x00') # gate switch to external
        self.wait_until_idle()
        self._command(DEEP_SLEEP)
        self._command(CHECK_CODE)
