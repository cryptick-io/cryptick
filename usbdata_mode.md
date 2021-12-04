# Cryptick USB Client - usbdata mode

Cryptick is able to display arbitrary market data.  To do so, first change the mode to usbdata mode:

```python cryptick.py --setmode usbdata```

Now you can update the Cryptick device with any market data you wish to display using the setassetsdata command and a json file containing the asset data:

```python cryptick.py --setassetsdata usb_setassetsdata.json```

Please see the example [usb_setassetsdata.json](usb_setassetsdata.json) for example an example json file.

## setassetsdata json spec

The json string is an array of up to ten json objects, each representing a market asset.  Each asset can include the following value pairs:

```
{
	"id": "BTC"
	"price": "61,057", 
	"rank": "#1", 
	"c1h": "0.53%", 
	"c24h": "-2.74%", 
	"c7d": "6.27%", 
	"c14d": "13.3%", 
	"c30d": "51.2%", 
	"c1y": "377%", 
	"7day": "15121A1113101315161312140E0D0B0F0E0B0E0E100D0C0A110F0D0E0D0E040B0F1917181916151109121715140F1615151B1A171817161D191F2226262924242623262524283F3B3B3A35373430302E3039342E241F1B1B1D191C1B211F1C2421221B0B"
}
```

### id
Asset trading symbol.

### price
Current spot price of the asset.  This should be specified in the device's currency, which can be set using the setcurrency command.

### rank
This value is unused.

### c1h
Asset value change, 1 hour.

### c24h
Asset value change, 1 day.

### c7d
Asset value change, 1 week.

### c14d
Asset value change, 2 weeks.

### c30d
Asset value change, 30 dat.

### c1y
Asset value change, 1 year.

### 7day
Graph of the market data "sparkline" - this is the last seven days of market data.  The graph should be encoded as a list of 100 values.  The values be within range [0,62].  Encode the value list as a string in hex format.  Each value is represented by two charcters.  The string length is therefore 200 characters.  An example 7day string is:

```
"7day": "15121A1113101315161312140E0D0B0F0E0B0E0E100D0C0A110F0D0E0D0E040B0F1917181916151109121715140F1615151B1A171817161D191F2226262924242623262524283F3B3B3A35373430302E3039342E241F1B1B1D191C1B211F1C2421221B0B"
```

This string represents the following 7day value list:
```
[21, 18, 26, 17, 19, 16, 19, 21, 22, 19, 18, 20, 14, 13, 11, 15, 14, 11, 14, 14, 16, 13, 12, 10, 17, 15, 13, 14, 13, 14, 4, 11, 15, 25, 23, 24, 25, 22, 21, 17, 9, 18, 23, 21, 20, 15, 22, 21, 21, 27, 26, 23, 24, 23, 22, 29, 25, 31, 34, 38, 38, 41, 36, 36, 38, 35, 38, 37, 36, 40, 63, 59, 59, 58, 53, 55, 52, 48, 48, 46, 48, 57, 52, 46, 36, 31, 27, 27, 29, 25, 28, 27, 33, 31, 28, 36, 33, 34, 27, 11]
```
