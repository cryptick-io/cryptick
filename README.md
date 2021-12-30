# Cryptick USB Client - Python

This repo provides scripts for communicating with a [Cryptick physical NFT device](https://cryptick.io) using Python.  Each Cryptick device is a WiFi connected stock ticker for crypto tokens, and is also connected to an NFT on the Ethereum blockchain.

If you're here to authenticate your Cryptick device, skip down to the [Digital Signature Authentication (DSA) section](#Cryptick-Digital-Signature-Authentication).

## Requirements

1. Python >=3
2. pycrypto lib (for DSA and SHA256 functions)

## Available Commands

### getversion
Get the cryptick device's version information 
For example, a version 1 device will return "Cryptick FE v1"

```python cryptick.py --getversion```

### gettime
Get the internal clock time from cryptick device

```python cryptick.py --gettime```

### settime
Set the cryptick internal clock from the current system time, also setting the UTC offset from the system.

```python cryptick.py --settime```

24 hour display mode is default.  Optionally, specify 12 hour display mode:

```python cryptick.py --settime --h12```

### setmode
Set the cryptick mode.  Possible modes are coin, clock, and usbdata.  coin displays the cryptocurrency market ticker.  clock displays the current time.  usbdata mode will listen for any [setassetsdata](#setassetsdata) command, allowing for display of arbitrary market data.

```python cryptick.py --setmode clock```

### setbrightness
Set the cryptick display brightness.  Value range [1,5]

```python cryptick.py --setbrightness 4```

### getpubkey
Get the public key from cryptick device and write to a pem file.  This can be used as a sanity check; to verify that the public key matches the one stored in the NFT on the Ethereum blockchain.  Specify the pem output filename as an argument.

```python cryptick.py --getpubkey cryptick.pem```

### resetwifi
Reset the wifi settings of the cryptick device.  This removes any stored wifi access point credentials from the device.

```python cryptick.py --resetwifi```

### setwifi
Set the wifi settings of the cryptick device.  The device will store the wifi credentials and attempt to connect on next boot.

```python cryptick.py --setwifi ssid password```

### getcurrencylist
Get the device's valid vs currency list.

```python cryptick.py --getcurrencylist```

### getcoinlist
Get the device's valid coin list (list of all valid coins cached from last connection to web service).

```python cryptick.py --getcoinlist```

### setcurrency
Set the device's vs currency.

```python cryptick.py --setcurrency usd```

### setcoins
Set the device's subscribed coins from the list of arguments (up to 10 coins).

```python cryptick.py --setcoins btc eth ada dot xlm xrp```

### setassetsdata
If device mode is set to usbdata, then you can send an asset data json string to display in the ticker.  This allows you to send any arbitrary market data to be displayed.  The json string is loaded from the specified file in the arguments.  Please see the [usbdata mode doc](usbdata_mode.md) for example json file usb_setassetsdata.json

```python cryptick.py --setassetsdata usb_setassetsdata.json```

### getconfig
gets the device's config as a json string and prints it to stdout.  

```python cryptick.py --getconfig```

### authenticate
Execute digital signature authentication challenge (DSA) to verify the authenticity of the physical Cryptick device.  This process is described in the [Digital Signature Authentication (DSA) section](#Cryptick-Digital-Signature-Authentication).


## Cryptick Digital Signature Authentication

Each Cryptick device has an embedded crypto chip which stores a unique private key for ECC DSA.  This private key is securely stored and cannot be read out from the device.  

Each Cryptick device is associated with a Cryptick NFT on the Ethereum blockchain.  The public key is stored in the Cryptick NFT metadata.  At any time in the future, anyone can view the Cryptick NFT on the blockchain and see that it is associated with the owner of the Cryptick NFT.  

To authenticate the physical Cryptick device, use the following process:

1. Clone this repository and install the prerequisite library pycrypto:

```
git clone https://github.com/cryptick-io/cryptick.git
pip install pycrypto
```

2. Plug in the Cryptick device to your computer using a USB-C cable.  

3. Locate the serial number of your Cryptick on the back lid, engraved in the wood.  In this example, let's assume it is [Cryptick Founders Edition (FE) #49](https://cryptick.io/cryptick-fe-49).

4. Next, we can run the script's authenticate command.  In this example we will authenticate cryptick founders edition #49:

```python cryptick.py --authenticate --serial cryptick-fe/49```

5. The script will grab the cryptick device's public key from cryptick.io based on the provided serial string (full link generated [here](https://cryptick.io/cryptick-fe/49/publickey.pem)).  It then performs a DSA challenge and verifies the results using the [NIST FIPS 186-4 ECDSA algorithm](https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/dss2/dsa2vs.pdf).  If the device is authenticated successfully, it will print to the terminal:

```Challenge verification success.```

6. To be even safer, you can remove all 3rd parties from the authentication chain, and specify the public key on the command line.  To do this, you'll need to view the NFT's data on the Ethereum blockchain. The easiest way to do this is to view the NFT metadata in your Metamask wallet, Etherscan, or on OpenSea.io.  In the Cryptick NFT's metadata, the public key is included at the end of the description.  Copy the contents of this string into a pubkey.pem file in the same folder as the cryptick.py script and run

```python cryptick.py --authenticate --pubkeypem ./pubkey.pem```

If the device is authenticated successfully, it will print to the terminal:

```Challenge verification success.```