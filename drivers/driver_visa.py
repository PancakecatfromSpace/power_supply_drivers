from power_supply_drivers.shared import SocketVals, VCP, Limits
import pyvisa

def OpenSocket(socketvals:SocketVals):
    """
    Create and return a connected TCP VISA socket.

    Args:
    SocketVals: Dataclass which contains all values needed to establish a connection, all values except SUPPLY_IP are ignored since they are not necessary.

    Returns:
    socket.socket: A connected TCP socket with timeout set.

    """
    # check all available instruments that are visa, specifies to use the PyVISA-py backend
    rm = pyvisa.ResourceManager('@py')
    # search all available VISA devices for a TCPIP device matching the IP set in SocketVals
    matching_available_devices = rm.list_resources(f"TCPIP::{socketvals.SUPPLY_IP}")
    # put amount of matching devices in own 
    matching_devices_amount = len(matching_available_devices)
    match matching_devices_amount:
        case 0:
            raise Exception(f"Error! No VISA TCP/IP Device matching the IP: {socketvals.SUPPLY_IP}!")
        case 1:
            match socketvals.CMD_LOOKUP:
                case "tti":
                    #This is stupid but necessary if the supply has a half assed implementation of the full VXI-11 Standard. 
                    #In this case the manufacturer TTI didn't bother to implement the VXI-11 Dicovery Protocoll properly. 
                    #See QPX1200S_SP Manual under the sections VXI-11 Discovery Protocoll and VISA Resource-Name for more details.
                    VISASocket = rm.open_resource(f"TCPIP::{socketvals.SUPPLY_IP}::{socketvals.SUPPLY_PORT}::SOCKET")

                case _:
                    #print(matching_available_devices[0])
                    VISASocket = rm.open_resource(matching_available_devices[0])                    
        case _:
            raise Exception(f"Error! {matching_devices_amount} Devices matching the IP Address! Matching devices: {matching_available_devices}")                    
    #set the termination socket to the value specified in SocketVals
    VISASocket.read_termination = socketvals.TERMINATION_STRING
    return VISASocket

def sendAndReceiveCommand(msg: str, supplySocket) -> str:
    """
    Send a command string over a socket, then receive and return the response.

    Args:
    msg (str): Command text to send (without trailing newline). A newline will be appended automatically.
    supplySocket: object of class socket.socket

    Returns:
    str: Decoded response from the socket with trailing newline and whitespace stripped.

    """
    msg =  msg + "\n"
    return supplySocket.query(msg)

# set value without receiving a response
def sendCommand(msg: str, supplySocket) -> None:
    """
    Send a command string over a socket.

    Args:
    msg (str): Command text to send (without trailing newline). A newline will be appended automatically.
    supplySocket: Connected socket-like object with .sendall(bytes) method (e.g., socket.socket).

    Returns:
    None
    """

    msg =  msg + "\n"
    supplySocket.write(msg)

def setVoltage(volt:float, MAX_VOLT:float, MIN_VOLT:float, supplySocket, lookup:str) -> int:
    """
    Sets the voltage to the specified value if it is within the allowed range.

    Args:
    volt (float): The voltage value to set.
    MAX_VOLT (float): The maximum allowed voltage.
    MIN_VOLT (float): The minimum allowed voltage.
    supplySocket: Connected socket-like object with .sendall(bytes) method (e.g., socket.socket).
    lookup (str): Specify which command is to be used to set the voltage. Currently implemented: tti.

    Returns:
    int: 0 if the voltage was set successfully, -1 if the voltage is out of range.
    """
    retval = 0
    match lookup:
        case "tti":
            cmd = "V1 "
        case _:
            raise Exception("ERROR! Specified Command lookup couldn't be found.")
    if volt >= MIN_VOLT and volt <= MAX_VOLT:
        sendCommand(f"{cmd}{volt}", supplySocket)
    else:

        retval = -1

    return retval

def setCurrent(cur:float, MAX_CUR:float, MIN_CUR:float, supplySocket, lookup:str) -> int:
    """
    Sets the current to the specified value if it is within the allowed range.

    Args:
    cur (float): The current value to set.
    MAX_CUR (float): The maximum allowed current.
    MIN_CUR (float): The minimum allowed current.
    supplySocket: Connected socket-like object with .sendall(bytes) method (e.g., socket.socket).
    lookup (str): Specify which command is to be used to set the voltage. Currently implemented: tti.

    Returns:
    int: 0 if the current was set successfully, -1 if the current is out of range.
    """
    retval = 0
    match lookup:
        case "tti":
            cmd = "I1 "
        case _:
            raise Exception("ERROR! Specified Command lookup couldn't be found.")
    if cur >= MIN_CUR and cur <= MAX_CUR:
        sendCommand(f"{cmd}{cur}", supplySocket)
    else:
        retval = -1
    
    return retval

def setPowerPos(power:float, MAX_POWER:float, MIN_POWER:float, supplySocket, lookup:str) -> int:
    """
    Sets the power to the specified value if it is within the allowed range.

    Args:
    power (float): The power value to set.
    MAX_POWER (float): The maximum allowed power.
    MIN_POWER (float): The minimum allowed power.
    supplySocket: The socket to which the command should be sent.

    Returns:
    int: 0 if the power was set successfully, -1 if the power is out of range.
    """
    retval = 0
    match lookup:
        #the tti power supply has no concept of max power, therefore don't do anything and return 0
        case "tti":
            return retval
        case _:
            raise Exception("ERROR! Specified Command lookup couldn't be found.")
    if power >= MIN_POWER and power <= MAX_POWER:
        sendCommand(f"{cmd}{power}", supplySocket)
    else:
        retval = -1
    return retval

def set_checked(setpoints:VCP, limits:Limits, socket, lookup:str):
    """
    Checks if the set points for voltage current and power are within the given limits. Sets the power supply connected to socket to that value.

    Args:
    setpoints (SetPoints): dataclass containing current voltage and power
    limits (Lmits): dataclass containing the correstponding limits.
    socket (socket):  dataclass containting the connected socket.
    Raises:
    Exception: if a value of setpoints is out of range set by limits
    """
    # if the current or voltage is out of range, put everything to zero and end
    if setCurrent(setpoints.current, limits.MAX_CUR, limits.MIN_CUR, socket, lookup) == -1:
        emergency_off(limits, socket)
        raise Exception(f"Fault! Attempted to set current {setpoints.current} outside range [{limits.MIN_CUR}, {limits.MAX_CUR}]!")
    if setVoltage(setpoints.voltage, limits.MAX_VOLT, limits.MIN_VOLT, socket, lookup) == -1:
        emergency_off(limits, socket)
        raise Exception(f"Fault! Attempted to set voltage {setpoints.voltage} outside range [{limits.MIN_VOLT}, {limits.MAX_VOLT}]!")
    if setPowerPos(setpoints.power, limits.MAX_POWER, limits.MIN_POWER, socket, lookup) == -1:
        emergency_off(limits, socket)
        raise Exception(f"Fault! Attempted to set power {setpoints.power} outside range [{limits.MIN_POWER}, {limits.MAX_POWER}]!")

def closeSocket(supplySocket):
    """
    Closes the socket and ends the connection the power supply.

    Args:
    supplySocket: The socket to which the command should be sent.   

    Returns:
    None
    """
    print("VISA Socket closed.")
    supplySocket.close()

def emergency_off(limits: Limits, socket):
    """
    shuts off everything and closes the socket
    """
    setCurrent(0, limits.MAX_CUR, limits.MIN_CUR, socket, "tti")
    setVoltage(0, limits.MAX_VOLT, limits.MIN_VOLT, socket, "tti")
    setPowerPos(0, limits.MAX_POWER, limits.MIN_POWER, socket, "tti")
    closeSocket(socket)

def measureVoltage(supplySocket) -> float:
    """
    Query the measured output Voltage

    Args:
    supplySocket: The socket to which the command should be sent.

    Returns:
    float: The measured output voltage parsed from the device response.
    """
    
    return float(sendAndReceiveCommand("V1O?",supplySocket)[:-1])

def measureCurrent(supplySocket) -> float:
    """
    Query the measured output Current

    Args:
    supplySocket: The socket to which the command should be sent.

    Returns:
    float: The measured output current parsed from the device response.
    """
    return float(sendAndReceiveCommand("I1O?",supplySocket)[:-1])

def measurePower(supplySocket) -> float:
    """
    Query the measured output Power

    Args:
    supplySocket: The socket to which the command should be sent.

    Returns:
    float: The measured output power parsed from the device response.
    """
    return float(sendAndReceiveCommand("I1O?",supplySocket)[:-1])*float(sendAndReceiveCommand("V1O?",supplySocket)[:-1])
