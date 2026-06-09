# shared dataclasses used by both VISA and raw TCP/IP drivers
from dataclasses import dataclass


@dataclass
class SocketVals:
    """
    Values the socket requires to communicate with the supply. Contains default values except for the IP Address and CMD_LOOKUP.

    Args:
    SUPPLY_IP (str): IP Address of the power supply
    TYPE (str): Type of communication, determines the driver to be used. Supports Auto, DE, VISA_TTI (Default: Auto, automatically check and choose the appropiate driver)
    SUPPLY_PORT (int): Port of the power supply (Default: 8462)
    TIMOUT_SECONDS (int): Timeout after which the socket is closed (Default: 10 Seconds)
    BUFFER_SIZE (int): Maximum number of bytes to read from the socket for the response. Unused by VISA. (Default: 128)
    TERMINATION_STRING (str): String that terminates the response of a VISA query. Unused by TCP/IP. (Default: "\r\n")
    VISA_BACKEND (str): Path to the VISA driver to be used. For example the NI VISA driver is located at /Windows/System32/visa64.dll under Windows. Defaults to "@py" which resolves automatically to the pyvisa-py backend.
    CMD_LOOKUP (str): Defines if a Supply specific lookup table should be used. (Default: tti)
    """
    SUPPLY_IP:str
    TYPE:str = "Auto"
    SUPPLY_PORT:int = 8462
    TIMEOUT_SECONDS:int = 10
    BUFFER_SIZE:int = 128
    TERMINATION_STRING:str = "\r\n"
    VISA_BACKEND:str = "@py"
    CMD_LOOKUP:str = "tti"

@dataclass
class Limits:
    """
    Limits within which the supply can accept values, populated with default values.
    """
    MAX_VOLT: float = 60 # default
    MIN_VOLT: float = -10
    MAX_CUR: float = 35    #default
    MIN_CUR: float = -10
    MAX_POWER: float = 1500
    MIN_POWER: float = -10

@dataclass
class VCP:
    """
    Stores Values for voltage current and power, the used TTI Instrument has no concept of power, therefore the value is ignored
    """
    voltage:float = 0
    current:float = 0
    power:float = 0

def CheckVISA(IP: str)->bool:
    """
    Checks if there is a VISA device with a matching IP Address.

    Args:
    IP(str): IP Address that is to be checked.
    Returns:
    TRUE: IP Address belongs to one or more VISA devices.
    FALSE: IP Address doesn't belong to a VISA device.
    """
    from pyvisa import ResourceManager
    if len(ResourceManager('@py').list_resources(f"TCPIP::{IP}")) > 0:
        return True
    return False

def CheckTCP(IP: str, PORT:int)->bool:
    """
    Checks if there is a TCP device with a matching IP Address and Port.

    Args:
    IP(str): IP Address that is to be checked.
    PORT(str): Port that is to be checked.
    Returns:
    TRUE: IP Address belongs to one or more VISA devices.
    FALSE: IP Address doesn't belong to a VISA device.
    """
    import socket as sock
    testsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    if testsocket.connect_ex((IP, PORT)) == 0:
        testsocket.close()
        return True
    testsocket.close()
    return False



