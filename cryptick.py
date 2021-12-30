"""

Cryptick usb client class

Provides an interface to send commands to a cryptick usb device.
Examples:

# get the device version information 
# For example, a version 1 device will return "Cryptick FE v1"
python cryptick.py --getversion

# get the internal clock time and UTC offset from 
# the cryptick device
python cryptick.py --gettime

# set the cryptick internal clock from the current system 
# time, also setting the UTC offset from the system
# enable 12-hour display
python cryptick.py --settime --h12

# set the cryptick mode.  Values: coin, clock, usbdata
python cryptick.py --setmode clock

# set the cryptick display brightness.  Value range [1,5]
python cryptick.py --setbrightness 5

# get the public key from cryptick device
python cryptick.py --getpubkey

# reset the wifi settings of the cryptick device
# this removes any stored wifi access point credentials
python cryptick.py --resetwifi

# set the wifi settings of the cryptick device
# the device will store the wifi credentials and attempt to 
# connect on next boot.
python cryptick.py --setwifi ssid password

# Execute digital signature authorization challenge (DSA)
# get the public key from cryptick.io based on the serial string
python cryptick.py --authenticate --serial cryptick-fe/49

# Execute digital signature authorization challenge (DSA) 
# using public key pem read from disk
python cryptick.py --authenticate --pubkeypem ./cryptick.pem

# get the device's valid vs currency list.
python cryptick.py --getcurrencylist

# get the device's valid coin list (list of 200 valid coins)
python cryptick.py --getcoinlist

# set the device's vs currency.
python cryptick.py --setcurrency usd

# Set the device's subscribed coins from the list of arguments 
# (up to 10 coins).
python cryptick.py --setcoins btc eth ada dot xlm xrp 

# If device mode is set to usbdata, then you can send an asset data 
# json string to display in the ticker.  This allows you to send any
# arbitrary market data.  The json string is loaded from the specified
# file in the arguments. 
# See the example json file usb_setassetsdata.json
python cryptick.py --setassetsdata usb_setassetsdata.json

"""

import json
import datetime, time
import serial
import serial.tools.list_ports
import argparse
import string
import os
import random
import binascii

from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

from urllib.request import urlopen


class cryptick_client:

	# constructor.  set up the command line argument parser
	def __init__(self):
		parser = argparse.ArgumentParser()
		parser_auth_group = parser.add_mutually_exclusive_group(required=False)
		parser.add_argument("--port", default=None, type=str, nargs=1, required=False,
												help="specify a serial port (for example, COM1)")

		parser.add_argument("--getversion", default=None, action="store_true", required=False,
												help="gets the device's version string")

		parser.add_argument("--gettime", default=None, action="store_true", required=False,
												help="gets the device's internal clock current time")

		parser.add_argument("--settime", default=None, action="store_true", required=False,
												help="sets the device's clock and UTC offset from system time.")

		parser.add_argument("--h12", default=None, action="store_true", required=False,
												help="used with settime command.  sets time display to 12-hour format.")

		parser.add_argument("--setbrightness", default=None, type=int, required=False,
												help="specify a mode for the setbrightness command.  Value must be in range [1,5]")

		parser.add_argument("--setmode", default=None, type=str, required=False,
												help="specify a mode for the setmode command.  Possible values: coin, clock, usbdata")

		parser.add_argument("--setfreq", default=None, type=int, required=False,
												help="specify ticker change frequency (in seconds)")

		parser.add_argument("--setpchange", default=None, type=str, required=False,
												help="specify a percentage change.  Possible values: 1h, 24h, 7d, 14d, 30d, 1y")

		parser.add_argument("--resetwifi", default=None, action="store_true", required=False,
												help="resets the device's stored wifi credentials")

		parser.add_argument("--setwifi", default=None, type=str, nargs=2, required=False,
												help="set the device's wifi credentials.  Requires two arguments: ssid, password")

		parser.add_argument("--getcurrencylist", default=None, action="store_true", required=False,
												help="get the device's valid vs currency list.")

		parser.add_argument("--getcoinlist", default=None, action="store_true", required=False,
												help="get the device's valid coin list (list of 200 valid coins)")

		parser.add_argument("--setcurrency", default=None, type=str, required=False,
												help="set the device's vs currency.")

		parser.add_argument("--setcoins", default=None, type=str, nargs="+", required=False,
												help="Set the device's subscribed coins from the list of arguments (up to 10 coins).")

		parser.add_argument("--setassetsdata", default=None, type=str, required=False,
												help="If the device is in usbdata mode, set the displayed asset data from the specified json file.")

		parser.add_argument("--getconfig", default=None, action="store_true", required=False,
												help="Get the device's config data.")

		parser.add_argument("--getpubkey", default=None, type=str, required=False,
												help="get the device's public key pem - specify pem file for the authenticate command.  For example: cryptick.pem.")

		parser.add_argument("--authenticate", default=None, action="store_true", required=False,
												help="authenticate the device using ECDSA.")
		parser_auth_group.add_argument("--serial", default=None, type=str, required=False,
												help="specify the device serial number for the authenticate commmand  For example: cryptick-fe/49")
		parser_auth_group.add_argument("--pubkeypem", default=None, type=str, required=False,
												help="specify public key pem file for the authenticate command.  For example: cryptick.pem")	

		self.args = parser.parse_args()


	# check the command json result string for success/failure.
	# returns True if the command succeeded
	def check_command_result(self, command_name, command_json_result):

		json_response = json.loads(command_json_result)
		if 'success' == json_response['result']:
			print("{} command success.".format(command_name))
			return True
		else:
			print("{} command failed.".format(command_name))
			return False


	# verify an ecdsa signature of a given message using public key pem.  
	# challenge is a 64-byte hex encoded string
	# signature is a 128-byte hex encoded string
	# public_key_string is the public key pem string
	def challenge_verify(self, challenge, signature, public_key_string):

		message_binary = bytearray.fromhex(challenge)
		sig_binary = bytearray.fromhex(signature)

		key = ECC.import_key(public_key_string)
		h = SHA256.new(message_binary)
		verifier = DSS.new(key, 'fips-186-3')
		try:
			verifier.verify(h, sig_binary)
			print ("The message is authentic.")
			return True
		except ValueError:
			print ("The message is not authentic.")
			return False		


	# send a usb command over the USB serial port to the cryptick device
	def send_usb_command(self, json_obj):
		
		message_json = json.dumps(json_obj) + '\n'
		mbytes = bytes(message_json, 'utf-8')
		self.ser.write(mbytes)
		response = self.ser.readline()
		return response


	# gets the current time from the cryptick device's internal clock
	def cmd_get_time(self):

		message = {}
		message['cmd'] = "gettime"

		pc_epoch = int(time.time())
		# if local time is within daylight savings and a
		# dst offset is defined, use the dst altzone for UTC offset
		if time.localtime().tm_isdst and time.daylight:
			pc_offset = time.altzone
		else:
			pc_offset = time.timezone

		response = self.send_usb_command(message)

		json_response = json.loads(response)
		epoch = json_response.get('time')
		utc_offset = json_response.get('offset')

		cryptick_time = time.gmtime(epoch)
		pc_time = time.gmtime(pc_epoch)

		error_seconds = epoch - pc_epoch

		if 'success' == json_response['result'] and epoch and utc_offset:
			print("Get time command success.")
			print("PC time            : " + str(pc_epoch))
			print("PC utc offset      : " + str(pc_offset))
			print("Cryptick time      : " + str(epoch))
			print("Cryptick utc offset: " + str(utc_offset))

			print("Cryptick is " + str(error_seconds) + ' seconds ahead of the PC clock\n')

			print("Cryptick time : " + time.strftime('%Y-%m-%dT%H:%M:%SZ', cryptick_time))
			print("PC time       : " + time.strftime('%Y-%m-%dT%H:%M:%SZ', pc_time))

		else:
			print("Get time command failed.")		


	# sets the cryptick device's internal clock and UTC offset from the 
	# system's clock.
	def cmd_set_time(self):

		message = {}
		message['cmd'] = "settime"
		message['time'] = int(time.time())
		# if local time is within daylight savings and a
		# dst offset is defined, use the dst altzone for UTC offset
		if time.localtime().tm_isdst and time.daylight:
			message['offset'] = time.altzone
		else:
			message['offset'] = time.timezone

		if self.args.h12:
			message['h12'] = 1

		response = self.send_usb_command(message)
		self.check_command_result("settime", response)


	# send random 64-byte string to the cryptick device.  Cryptick device
	# generates SHA256 hash digest of the message, and signs it using fips-186-3
	# digital signature.  This function reads the signature back and verifies
	# it using the public key.
	#
	# Public key is specified on the command line.  Although it's possible to read
	# the public key from the device using cmd_get_public_key function, it is 
	# recommended to get it directly from the NFT on the Ethereum blockchain, and 
	# specify it on the command line to this script. 
	def cmd_authenticate(self):

		pub_key_pem = ""
		if self.args.serial:
			url = "https://cryptick.io/" + self.args.serial + "/publickey.pem"
			print("Reading public key from " + url)
			pub_key_pem = urlopen(url).read()
		else:
			if not self.args.pubkeypem:
				print("Error - no serial or pubkeypem provided.")
				exit(1)
			else:
				try:
					with open(self.args.pubkeypem, "r") as f_pubkey:
						pub_key_pem = f_pubkey.read()
						f_pubkey.close()
						print("read pem file {}.".format(self.args.pubkeypem))

				except IOError:
					print("error - pem file {} not found.".format(self.args.pubkeypem))
					exit(1)


		# challenge must be a 32-byte binary byte array, 
		# represented as a 64-byte hexadecimal string.  Example:
		# "AC467DC3693375900EEA66BBDD299AE197569B9BC4C3831BF09323D83C5C0E21"
		# Note that this absolutely must be a string of random hex values 
		# in order to avoid replay attack susceptibility.  
		hex_chars = "0123456789ABCDEF"
		challenge_str = ''.join(random.SystemRandom().choice(hex_chars) for _ in range(64))
		message = {}
		message['cmd'] = "authenticate"
		message['challenge'] = challenge_str

		response = self.send_usb_command(message)
		print (message)
		print(response)

		json_response = json.loads(response)
		signature = json_response.get('signature')
		if 'success' == json_response['result']:
			if signature:
				print("Signature:\n" + signature + '\n')
				result = self.challenge_verify(challenge_str, signature, pub_key_pem)
				if result:
					print("Challenge verification success.")
				else:
					print("Challenge verification failure.")
		else:
			print("Challenge command failed.")


	# reads the public key pem from the cryptick device and writes 
	# it to file cryptick.pem
	def cmd_get_public_key(self):

		message = {}
		message['cmd'] = "getpubkey"

		response = self.send_usb_command(message)
		print(str(response))

		json_response = json.loads(response)
		pub_key_pem = json_response.get('public_key')
		if 'success' == json_response['result'] and pub_key_pem:
			if 0 != len(self.args.getpubkey):
				pem_filename = self.args.getpubkey		
				f = open(pem_filename, "w")
				f.write(pub_key_pem)
				f.close()
				print("wrote pem to: " + pem_filename)

			print("Cryptick public key pem:\n" + pub_key_pem + '\n')
			return True
		else:
			print("Get public key command failed.")
			return False


	# set display brightness, range [0,4]
	def cmd_set_brightness(self):

		if self.args.setbrightness not in range(1,6):
			print("Error - invalid brightness value {}.  Valid value range is [1,5]".format(str(self.args.setbrightness)))
			exit(1)

		message = {}
		message['cmd'] = "setbrightness"
		# actual brightness range on device is [0, 4]
		message['brightness'] = self.args.setbrightness - 1

		response = self.send_usb_command(message)
		self.check_command_result("setbrightness", response)


	# set device mode: coin, clock, or usbdata
	def cmd_set_mode(self):

		if self.args.setmode not in ["coin", "clock", "usbdata"]:
			print("Error - invalid mode value: {}".format(self.args.setmode))
			exit(1)

		message = {}
		message['cmd'] = "setmode"
		message['mode'] = self.args.setmode

		response = self.send_usb_command(message)
		self.check_command_result("setmode", response)


	# set the device ticker frequency
	def cmd_set_freq(self):
		message = {}
		message['cmd'] = "setfreq"
		message['freq'] = self.args.setfreq

		response = self.send_usb_command(message)
		self.check_command_result("setfreq", response)


	# set the device percentage change unit
	def cmd_set_pchange(self):

		if self.args.setpchange not in ['1h', '24h', '7d', '14d', '30d', '1y']:
			print("Set pchange command failed. {} not valid percentage change.  Valid values: 1h, 24h, 7d, 14d, 30d, 1y".format(self.args.setpchange))
			exit(1)

		message = {}
		message['cmd'] = "setpchange"
		message['pchange'] = self.args.setpchange

		response = self.send_usb_command(message)
		self.check_command_result("setpchange", response)


	# get the device currency list
	def cmd_getcurrencylist(self):
		message = {}
		message['cmd'] = "getcurrencylist"

		response = self.send_usb_command(message)
		self.check_command_result("getcurrencylist", response)


	# get the device coin list
	def cmd_getcoinlist(self):
		message = {}
		message['cmd'] = "getcoinlist"

		response = self.send_usb_command(message)
		self.check_command_result("getcoinlist", response)


	# set the device currency list
	def cmd_setcurrency(self):
		if self.args.setcurrency is None:
			print("setcurrency - error, no currency value specified.")
			exit(1)

		# first check to make sure the new currency is in the list
		# of valid currencies
		message = {}
		message['cmd'] = "getcurrencylist"

		response = self.send_usb_command(message)

		json_response = json.loads(response)
		if 'success' != json_response['result']:
			print("getcurrencylist command failed.")
			exit(1)
		currency_list = json_response["currencies"];

		if self.args.setcurrency not in currency_list:
			print("currency {} is not in the list of valid currencies.".format(self.args.setcurrency))
			exit(1)

		message = {}
		message['cmd'] = "setcurrency"
		message['currency'] = self.args.setcurrency;

		response = self.send_usb_command(message)
		self.check_command_result("setcurrency", response)


	# set the device's subscribed coins list
	def cmd_setcoins(self):
		if len(self.args.setcoins) > 10:
			print("setcoins - error, maximum of 10 coins allowed.")
			exit(1)

		# first get list of available coins
		message = {}
		message['cmd'] = "getcoinlist"

		response = self.send_usb_command(message)

		json_response = json.loads(response)
		if 'success' != json_response['result']:
			print("getcoinlist command failed.")
			exit(1)
		coinlist = json_response["coins"]

		for coin in self.args.setcoins:
			if coin not in coinlist:
				print("coin {} is not in available coin list.".format(coin))
				exit(1)

		message = {}
		message['cmd'] = "setcoins"
		message['coins'] = self.args.setcoins;

		response = self.send_usb_command(message)
		self.check_command_result("setcoins", response)


	# set the device assets data.  device must be in usbdata mode.
	def cmd_setassetsdata(self):
		# get the assetsdata json from specified file
		setassetsdata = ""
		try:
			with open(self.args.setassetsdata, "r") as f:
				setassetsdata = f.read()
				f.close()
				print("read assets json file {}.".format(self.args.setassetsdata))

		except IOError:
			print("error - assets json file {} not found.".format(self.args.setassetsdata))
			exit(1)

		json_assetsdata = json.loads(setassetsdata)

		message = {}
		message['cmd'] = "setassetsdata"
		message['assetsdata'] = json_assetsdata;

		response = self.send_usb_command(message)
		self.check_command_result("setwifi", response)


	# get the device configuration json string
	def cmd_getconfig(self):
		message = {}
		message['cmd'] = "getconfig"

		response = self.send_usb_command(message)
		self.check_command_result("getconfig", response)


	# get the device version string
	def cmd_getversion(self):
		message = {}
		message['cmd'] = "getversion"

		response = self.send_usb_command(message)

		if self.check_command_result("getversion", response):
			json_response = json.loads(response)
			print("version: {}".format(json_response['version']))


	# set the device wifi ssid and password
	def cmd_set_wifi(self):
		if self.args.setwifi is None:
			print("setwifi - error, no ssid / password specified.")
			exit(1)

		message = {}
		message['cmd'] = "setwifi"
		message['ssid'] = self.args.setwifi[0];
		message['pass'] = self.args.setwifi[1];
		print(message)

		response = self.send_usb_command(message)
		self.check_command_result("setwifi", response)


	# reset the device wifi
	def cmd_reset_wifi(self):
		message = {}
		message['cmd'] = "setwifi"
		# wifi reset requires no ssid or pass in json message.

		response = self.send_usb_command(message)
		self.check_command_result("resetwifi", response)


	# run the command specified in commandline arguments
	def run_command(self):

		ports = serial.tools.list_ports.comports()

		if 0 == len(ports):
			print("No Cryptick serial port found.")
			exit(1)

		#for port, desc, hwid in sorted(ports):
		#        print("{}: {} [{}]".format(port, desc, hwid))

		if self.args.port:
			port = self.args.port
		else:
			port, desc, hwid = ports[0]
		
		print ("connecting to port: " + port)

		self.ser = serial.Serial(port)
		self.ser.baudrate = 115200
		self.ser.timeout = 10

		if self.args.getpubkey:
			self.cmd_get_public_key()
		elif self.args.authenticate:
			self.cmd_authenticate()
		elif self.args.gettime:
			self.cmd_get_time()
		elif self.args.settime:
			self.cmd_set_time()
		elif self.args.setmode:
			self.cmd_set_mode()
		elif self.args.setfreq:
			self.cmd_set_freq()
		elif self.args.setpchange:
			self.cmd_set_pchange()
		elif self.args.setbrightness:
			self.cmd_set_brightness()
		elif self.args.resetwifi:
			self.cmd_reset_wifi()
		elif self.args.setwifi:
			self.cmd_set_wifi()
		elif self.args.getcurrencylist:
			self.cmd_getcurrencylist()
		elif self.args.getcoinlist:
			self.cmd_getcoinlist()
		elif self.args.setcurrency:
			self.cmd_setcurrency()
		elif self.args.setcoins:
			self.cmd_setcoins()
		elif self.args.getconfig:
			self.cmd_getconfig()
		elif self.args.setassetsdata:
			self.cmd_setassetsdata()
		elif self.args.getversion:
			self.cmd_getversion()
		else:
			print("Invalid command.")

if __name__ == "__main__":
	
	cryptick = cryptick_client()
	cryptick.run_command()


