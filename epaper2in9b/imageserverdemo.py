import network
import urequests
import time

# Demo Python class for epaper2in9b
# Usage:
# import imageserverdemo
# 
# server = imageserverdemo.ImageServerDemo("http://192.168.1.2:8080/{}")
# server.fetch_image(epaperdisplay)
# 
class ImageServerDemo:

	def __init__(self, url_template):
		self.url_template = url_template

	# Just utility method if you aren't already connected
	def connect_wifi(self, essid, passphrase):
		sta_if = network.WLAN(network.STA_IF)
		if not sta_if.active():
			print("Activate STA_IF")
			sta_if.active(True)
		if not sta_if.isconnected():
			print("Connect to WiFi {}".format(essid))
			sta_if.connect(essid, passphrase)
			time.sleep(3)
		wait_time_left = 27
		while not sta_if.isconnected():
			print("... still connecting ...")
			wait_time_left -= 2
			if(wait_time_left < 2):
				break
			time.sleep(2)
			pass
		if sta_if.isconnected():
			print("Connected")
		else:
			print("Failed to connect")
    
	def fetch_image(self, epaper):
		response = urequests.get(self.url_template.format("primary"))
		if response.status_code is 200:
			print("Unexpected HTTP {} received for primary fetch".format(response.status_code))
			response.close()
			return
		epaper.set_primary_content(response.content)
		response.close()

		response = urequests.get(self.url_template.format("secondary"))
		if response.status_code is not 200:
			print("Unexpected HTTP {} received for secondary fetch".format(response.status_code))
			response.close()
			return
		epaper.set_secondary_content(response.content)
		response.close()

		epaper.refresh()