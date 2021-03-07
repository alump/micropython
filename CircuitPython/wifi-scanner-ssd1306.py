import feathers2
from board import SCL, SDA
import busio
import adafruit_ssd1306
import wifi

feathers2.enable_LDO2(True)
try:
    i2c = busio.I2C(SCL, SDA)
    display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)

    display.fill(0)
    display.text("Network Scanner", 1, 2, True)
    display.line(0,14,128,14,True)
    display.text("Scanning...", 20, 24, True)
    display.show()

    try:
        y = 16
        networks = []
        for network in wifi.radio.start_scanning_networks():
            networks.append((network.ssid, network.rssi))
            
        display.text(str(len(networks)), 100, 2, True)
        
        networks = sorted(networks, key=lambda x: x[1], reverse=True)[0:5]
        
        display.rect(0,16,128,64,False,fill=True)
        for network in networks:
            display.text(str(network[1]) + " " + network[0], 0, y, True)
            y += 10
    except:
        display.text("Error", 0, y, True)
    finally:
        wifi.radio.stop_scanning_networks()
        display.show()
finally:
    i2c.deinit()
