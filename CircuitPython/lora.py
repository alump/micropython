import digitalio
import board
import busio
import adafruit_rfm9x
import feathers2

feathers2.enable_LDO2(True)
RADIO_FREQ_MHZ = 868.0
CS = digitalio.DigitalInOut(board.D18)
RESET = digitalio.DigitalInOut(board.D19)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

rfm9x.signal_bandwidth = 62500
rfm9x.coding_rate = 6
rfm9x.spreading_factor = 8
rfm9x.enable_crc = True

rfm9x.frequency_mhz

for x in range(10):
    rfm9x.send("Hwllo World".encode("ASCII"))

msg = rfm9x.receive(timeout=10)