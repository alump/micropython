
import config_lora
import machine
import ssd1306
import time
import sx127x
import math

class MyLora:

    # frequency 868E6 (EU) or 915E6 (US)
    def __init__(self, lora_freq = 915E6, lora_txpwr = 2):
        self._i2c = machine.I2C(-1, scl=machine.Pin(15), sda=machine.Pin(4), freq=400000)
        self._oled = ssd1306.SSD1306_I2C(128, 64, self._i2c)

        self._d_rst = machine.Pin(16, machine.Pin.OUT)
        self._d_rst.value(0)
        time.sleep_ms(20)

        device_pins = {
            'miso':19,
            'mosi':27,
            'ss':18,
            'sck':5,
            'dio_0':26,
            'reset':16,
            'led':2, 
        }

        lora_parameters = {
            'frequency': lora_freq, 
            'tx_power_level': lora_txpwr,
            'signal_bandwidth': 125E3,    
            'spreading_factor': 8, 
            'coding_rate': 5, 
            'preamble_length': 8,
            'implicit_header': False, 
            'sync_word': 0x12, 
            'enable_CRC': False,
            'invert_IQ': False,
        }

        self._device_spi = machine.SPI(baudrate = 10000000, 
            polarity = 0, phase = 0, bits = 8, firstbit = machine.SPI.MSB,
            sck = machine.Pin(device_pins['sck'], machine.Pin.OUT, machine.Pin.PULL_DOWN),
            mosi = machine.Pin(device_pins['mosi'], machine.Pin.OUT, machine.Pin.PULL_UP),
            miso = machine.Pin(device_pins['miso'], machine.Pin.IN, machine.Pin.PULL_UP))
        self._lora = sx127x.SX127x(self._device_spi, pins=device_pins, parameters=lora_parameters)

        self._d_rst.value(1)
        self._oled.init_display()
        self._oled.contrast(1)
        self.show('System Initialized', 'Call receiver()', '...or sender()')

    def receiver(self):
        self.show('Receiver', 'Nothing received')
        while True:
                if self._lora.received_packet():
                    self._lora.blink_led()
                    header = "Receiver {0} MHz".format(math.floor(self._lora._frequency / 1000000))
                    snr = "SNR: {0}".format(self._lora.packet_snr())
                    self.show(header, self._lora.read_payload(), self.recv_quality(), snr)


    def recv_quality(self):
        rssi = self._lora.packet_rssi()
        perc = math.floor((120 + (rssi + 30)) / 1.2)
        if perc > 100:
            perc = 100
        elif perc < 0:
            perc = 0
        return "RSSI: {0} {1}dB".format(perc, rssi)

    def sender(self):
        counter = 0
        while True:
            payload = 'Hello ({0})'.format(counter)
            power = "Power: {0} dB".format(self._lora._tx_power_level)
            header = "Sender {0} MHz".format(math.floor(self._lora._frequency / 1000000))
            self.show(header, payload, power)
            self._lora.blink_led()
            self._lora.println(payload)

            counter += 1
            time.sleep_ms(5000)

    
    def show(self, header, *lines):
        self._oled.fill(0)
        print("===\n{}\n-----------".format(header))
        self._oled.text(header, 0, 0)
        self._oled.line(0,13,128,13,1)
        y = 20
        for line in lines:
            self._oled.text(line, 0, y)
            print("{}".format(line))
            y = y + 11
        print("===\n")
        self._oled.show()


