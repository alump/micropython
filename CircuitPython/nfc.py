import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C
import feathers2
import time

feathers2.enable_LDO2(True)
i2c = busio.I2C(board.SCL, board.SDA)
irq_pin = DigitalInOut(board.D19)
pn532 = PN532_I2C(i2c, debug=False, reset=DigitalInOut(board.D18), irq=irq_pin)
pn532.SAM_configuration()

foo = pn532.listen_for_passive_target()
current = None
print("Waiting for RFID/NFC card...")
step = 0
while True:
    # Check if a card is available to read
    if irq_pin.value == 0:
        uid = pn532.get_passive_target()
        if current != uid:
            print("")
            print("Found card with UID:", [hex(i) for i in uid])
            data = bytearray()
            try:
                for x in range(40):
                    incoming = pn532.ntag2xx_read_block(x);
                    for byt in incoming:
                        data.append(byt)
            except:
                print("Reading stopped before page 40")
            for x in range(len(data) / 8):
                offset = x * 8
                print(hex(offset) + "\t", [hex(i) for i in data[offset: offset+8]])
                
            current = uid
        # Start listening for a card again
        foo = pn532.listen_for_passive_target()
    else:
        current = None
        step += 1
        if step % 10 == 0:
            print(".", end="")
    time.sleep(0.1)