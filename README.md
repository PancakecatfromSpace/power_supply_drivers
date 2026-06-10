# The simple way to work with Supplies over a network.

## Motivation and scope

This driver was written for my bachelor thesis during which I was confronted with the issue of changing power supplies within my Project. I originally developed a driver for the [DE SM210-CP-150](https://www.deltaelektronika.com/en/products/sm15k-series) within my [SunCell](https://github.com/PancakecatfromSpace/SunCell) project, but was forced to switch to a [TTI QPX1200SP](https://www.aimtti.com/product-category/dc-power-supplies/aim-qpxseries) since the original supply was not in the required power range. Adapting my programm turned out to be difficult and I wanted my driver to still be compatible with both supplies. Therefore I developed a wrapper that automatically detects different TCP/IP and VISA VXI-11 power supplies within the network, establish the communication, measure and set voltage, current, power and send user specified commands to the supply.
Because of these requirements and the wish of my professor to reuse my driver in other projects I came up with the following architecture:

# Architecture

## wrapper

The wrapper file contains the logic to determine which driver to load and methods to measure and set output voltage current and (if applicable) power. This is contained within a single class called **SupplyCommunication** and its methods. It expects a driver file for the specific power supply. It is possible to use the drivers directly but it is discouraged, since it is possible to initialize a VISA communication or TCP/IP socket without closing the socket properly. This may leed to orphaned sockets which may leed to unexpected behaiviour. It may have the following arguments:

- IP (str): IP Address as String, in the Format: 192.168.178.1, expects no subnet mask!
- type (str): Type of communication, determines the driver to be used. Supports Auto, EA, VISA_TTI (Default: Auto, automatically check and choose the appropiate driver)
- SUPPLY_PORT (int): Port of the power supply (Default: 8462)
- BUFFER_SIZE (int): Maximum number of bytes to read from the socket for the response. Unused by VISA. (Default: 128)
- TERMINATION_STRING (str): String that terminates the response of a VISA query. Unused by TCP/IP. (Default: \r\n)
- VISA_BACKEND (str): Path to the VISA driver to be used. For example the NI VISA driver is located at /Windows/System32/visa64.dll under Windows. Defaults to "@py" which resolves automatically to the pyvisa-py backend.
- CMD_LOOKUP (str): Defines if a Supply specific lookup table should be used. (Default: tti)

During initialzation the class first checks the value of **type**, if none is given it defaults to Auto and probes if a VISA VXI-11 or a TCP/IP device with the specified **IP** Adress is available. If resources are scarse this probing step can be skipped by specifying through **type** which specific driver should be used. Currently available options are: *VISA* and *DE*.
If initialization was successfull you can start communicating with the power supply through the following methods:

### setValues

Sets the output values of the power supply to the specified value. Expects:
- U (float): Voltage to set the output to
- I (float): Current to set the output to
- P (float): Power to set the output to
You may edit all or none of the values. Any unedited value will default to the previous value stored within the setpoints dataclass stored within the object.
When setting the setpoint Voltage Current and Power are checked against the values stored within the limits dataclass. Attempting to set a setpoint outside of the given limits will raise an exception.
**WARNING: CHECK IF THE STANDARD VALUES WITHIN power_supply_drivers.shared.limits are set to a sensible set of values for your circuit! If you don't do this only gods mercy can save your circuit and or power supply!**

### setLimits

Expects a dataclass limits object which is located within power_supply_drivers.shared.Limits. Attempting to set the according MIN value greater or equal to the MAX value will raise an expection. 

### measureValues

Measures all voltages and saves the result in SupplyCommunication.measuredpoints.

### sendOnly

Send raw scpi or text command to supply without expecting a response. 
WARNING! No checks are performed when calling this method.

### sendReceive

Send raw scpi or tesxt command to supply and output response as string. The end of the message is determined by **TERMINATION_STRING** when using the *VISA driver*. The standard value is set to accomidate the broken implementation of the *TTI QPX1200SP*
WARNING! No checks are performed when calling this method. Result will not be saved in object.

## shared

Dataclasses and functions used by both drivers. Also contains the probing functions.