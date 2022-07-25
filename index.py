import base64
import ctypes
from bitstring import BitArray
import broadlink
import datetime

# Constants
kWhirlpoolAcChecksumByte1 = 13
kWhirlpoolAcChecksumByte2 = 20
kWhirlpoolAcHeat = 0
kWhirlpoolAcAuto = 1
kWhirlpoolAcCool = 2
kWhirlpoolAcDry = 3
kWhirlpoolAcFan = 4
kWhirlpoolAcFanAuto = 0
kWhirlpoolAcFanHigh = 1
kWhirlpoolAcFanMedium = 2
kWhirlpoolAcFanLow = 3
kWhirlpoolAcMinTemp = 18     # 18C (DG11J1-3A), 16C (DG11J1-91)
kWhirlpoolAcMaxTemp = 32     # 32C (DG11J1-3A), 30C (DG11J1-91)
kWhirlpoolAcAutoTemp = 23    # 23C
kWhirlpoolAcCommandLight = 0x00
kWhirlpoolAcCommandPower = 0x01
kWhirlpoolAcCommandTemp = 0x02
kWhirlpoolAcCommandSleep = 0x03
kWhirlpoolAcCommandSuper = 0x04
kWhirlpoolAcCommandOnTimer = 0x05
kWhirlpoolAcCommandMode = 0x06
kWhirlpoolAcCommandSwing = 0x07
kWhirlpoolAcCommandIFeel = 0x0D
kWhirlpoolAcCommandFanSpeed = 0x11
kWhirlpoolAcCommand6thSense = 0x17
kWhirlpoolAcCommandOffTimer = 0x1D



kWhirlpoolAcHdrMark = 8950
kWhirlpoolAcHdrSpace = 4484
kWhirlpoolAcBitMark = 597
kWhirlpoolAcOneSpace = 1649
kWhirlpoolAcZeroSpace = 533
kWhirlpoolAcGap = 7920
kWhirlpoolAcMinGap = 100000; # Just a guess.
kWhirlpoolAcSections = 3

def bitwise_and_bytes(a):
    result_int = int.from_bytes(a, byteorder="big") & 1
    return result_int.to_bytes(max(len(a), 1), byteorder="big")

def xorBytes(code, length):
    code = bytearray(code)

    checksum = 0x00

    for i in range(0, length):
        checksum ^= code[i]

    return checksum

def pad_hex_to_double_byte(bytes):
    return bytes.zfill(4)

def padHexToByte(byte):
    return byte.zfill(2)

def bigEndianToBigLittleDoubleHexByte(bytes):
    return bytes[2:] + bytes[0:2]

def pulesArrayToBroadlink(pulesArray):
    pulse_array.insert(0, 0)
    # clone a copy of the array
    pulesArray = pulesArray[:]
    # The boarding final command
    broadlinkHexCommand = ''
    # Get the frequency of the command
    frequency = pulesArray.pop(0)
    # whenever its a IR command
    isIr = False
    # If the frequency is default or 38/IR frequency
    if frequency == 0 or frequency == 38:
        isIr = True
        broadlinkHexCommand +=  f'{38:x}'
    else:
        broadlinkHexCommand +=  f'{frequency:x}'
    # The amount of pules
    length = len(pulesArray)
    # Add don't repeat byte flag
    broadlinkHexCommand += '00'
    # Get the length as hex value, (add 6 for the additional const broadlink command header)
    hexLength =  f'{length + 6:x}'
    # Pad the hex value to fill 2 bytes (for example for '2a' pad to '002a')
    hexLengthByte = pad_hex_to_double_byte(hexLength)
    # Convert the hex bytes to little endian (for example from '002a' to '2a00')
    littleEndianLengthByte = bigEndianToBigLittleDoubleHexByte(hexLengthByte)
    # Add the length bytes to the broadlink command
    broadlinkHexCommand += littleEndianLengthByte
    # Now convert all the pules
    for pulesItem in pulesArray:
        # Calculate the pules length (µs * 2^-15 formula)
        puls = pulesItem * 269 / 8192
        # Flat the pules (from xx.xx to xx)
        flatPuls = int(puls)
        # Convert the pules to hex
        hexPuls =  f'{flatPuls:x}'
        # the pules as broadlink hex
        hexCommand = ''
        # If the hex can stored in one byte
        if len(hexPuls) <= 2:
            # Pad the byte if needed (from 0x1 to '01')
            hexCommand = padHexToByte(hexPuls)
        else:
            # Else if it can't stored in one byte, pad it to double byte
            # and add the '00' flag (this flag mark that the next value is two bytes and not only one)
            hexCommand = '00' + pad_hex_to_double_byte(hexPuls)
        # Add the command to the final broadlink command
        broadlinkHexCommand += hexCommand
    # Return the final command, and add the IR command ends flag (for IR only)
    return broadlinkHexCommand + (isIr and '000d05000000000000' or '')

class WhirlpoolAC(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("pad0", ctypes.c_uint8 * 2),
        ("Fan", ctypes.c_uint8, 2),
        ("Power", ctypes.c_uint8, 1),
        ("Sleep", ctypes.c_uint8, 1),
        ("", ctypes.c_uint8, 3),
        ("Swing1", ctypes.c_uint8, 1),
        ("Mode", ctypes.c_uint8, 3),
        ("", ctypes.c_uint8, 1),
        ("Temp", ctypes.c_uint8, 4),
        ("", ctypes.c_uint8, 8),
        ("", ctypes.c_uint8, 4),
        ("Super1", ctypes.c_uint8, 1),
        ("", ctypes.c_uint8, 2),
        ("Super2", ctypes.c_uint8, 1),
        ("ClockHours", ctypes.c_uint8, 5),
        ("LightOff", ctypes.c_uint8, 1),
        ("", ctypes.c_uint8, 2),
        ("ClockMins", ctypes.c_uint8, 6),
        ("", ctypes.c_uint8, 1),
        ("OffTimerEnabled", ctypes.c_uint8, 1),
        ("OffHours", ctypes.c_uint8, 5),
        ("", ctypes.c_uint8, 1),
        ("Swing2", ctypes.c_uint8, 1),
        ("", ctypes.c_uint8, 1),
        ("OffMins", ctypes.c_uint8, 6),
        ("", ctypes.c_uint8, 1),
        ("OnTimerEnabled", ctypes.c_uint8, 1),
        ("OnHours", ctypes.c_uint8, 5),
        ("", ctypes.c_uint8, 3),
        ("OnMins", ctypes.c_uint8, 6),
        ("", ctypes.c_uint8, 2),
        ("", ctypes.c_uint8, 8),
        ("Sum1", ctypes.c_uint8, 8),
        ("", ctypes.c_uint8, 8),
        ("Cmd", ctypes.c_uint8, 8),
        ("pad1", ctypes.c_uint8 * 2),
        ("", ctypes.c_uint8, 3),
        ("J191", ctypes.c_uint8, 1),
        ("", ctypes.c_uint8, 4),
        ("", ctypes.c_uint8, 8),
        ("Sum2", ctypes.c_uint8, 8),
    ]

ac = WhirlpoolAC()

state = bytearray(b'\x83\x06\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

ac = WhirlpoolAC.from_buffer_copy(state)

def setTemp(temp):
    newtemp = min(kWhirlpoolAcMaxTemp, max(kWhirlpoolAcMinTemp, temp))
    ac.Temp = newtemp - kWhirlpoolAcMinTemp
    setSuper(False)  # Changing temp cancels Super/Jet mode.
    ac.Cmd = kWhirlpoolAcCommandTemp

def setFan(speed):
        ac.Fan = speed
        setSuper(False)  # Changing fan speed cancels Super/Jet mode.
        ac.Cmd = kWhirlpoolAcCommandFanSpeed

def setSuper(super):
    Mode = ac.Mode
    if (super):
        setFan(kWhirlpoolAcFanHigh)
        match Mode:
            case 0:
                setTemp(kWhirlpoolAcMaxTemp)
            case 2:
                setTemp(kWhirlpoolAcMinTemp)
                # setMode(kWhirlpoolAcCool)
            case _:
                setTemp(kWhirlpoolAcMinTemp)
                # setMode(kWhirlpoolAcCool)
        ac.Super1 = 1
        ac.Super2 = 1
    else:
        ac.Super1 = 0
        ac.Super2 = 0
    ac.Cmd = kWhirlpoolAcCommandSuper

def setSleep(sleep):
    ac.Sleep = sleep
    if (sleep): setFan(kWhirlpoolAcFanLow)
    ac.Cmd = kWhirlpoolAcCommandSleep

def setMode(mode):
    setSuper(False)  # Changing mode cancels Super/Jet mode.
    if(mode == kWhirlpoolAcAuto):
        setFan(kWhirlpoolAcFanAuto)
        setTemp(kWhirlpoolAcAutoTemp)
        setSleep(False) # Auto mode cancels sleep mode.
        ac.Cmd = kWhirlpoolAcCommand6thSense
    else:
        ac.Mode = mode
        ac.Cmd = kWhirlpoolAcCommandMode

def setSwing(swing):
    ac.Swing1 = swing
    ac.Swing2 = swing
    ac.Cmd = kWhirlpoolAcCommandSwing

def setLight(light):
    ac.LightOff = not light
    ac.Cmd = kWhirlpoolAcCommandLight

def setClock(hours, mins):
    ac.ClockHours = hours
    ac.ClockMins = mins

def setPower(power):
    ac.Power = power
    setSuper(False)  # Changing power cancels Super/Jet mode.
    ac.Cmd = kWhirlpoolAcCommandPower

def setCommand(cmd):
    ac.Cmd = cmd

def checksum():
    if (21 >= kWhirlpoolAcChecksumByte1):
        ac.Sum1 = xorBytes(bytes(ac)[2:], kWhirlpoolAcChecksumByte1 - 1 - 2)
    if (21 >= kWhirlpoolAcChecksumByte2):
        ac.Sum2 = xorBytes(bytes(ac)[kWhirlpoolAcChecksumByte1 + 1:],
        kWhirlpoolAcChecksumByte2 - kWhirlpoolAcChecksumByte1 - 1)
now = datetime.datetime.now()
setMode(kWhirlpoolAcCool)
setSwing(False)
setLight(True)
setFan(0)
setTemp(18)
setClock(now.hour, now.minute)
setPower(True)
checksum()
print(bytes(ac))
c = BitArray(bytes=bytes(ac))
l = bytearray(21)
value = int.from_bytes(ac, byteorder='big')

pulse_array = [kWhirlpoolAcHdrMark, kWhirlpoolAcHdrSpace]

def pulse_codes(dataptr, nbytes, end):
  result = []
  for i in range(nbytes):
    data = dataptr[i]
    for _ in range(8):
      if (data & 1):
        result.append(kWhirlpoolAcBitMark)
        result.append(kWhirlpoolAcOneSpace)
      else:
        result.append(kWhirlpoolAcBitMark)
        result.append(kWhirlpoolAcZeroSpace)
      data >>= 1
    result.append(kWhirlpoolAcBitMark)
    result.append(kWhirlpoolAcGap)
  return result

pulse_array.extend(pulse_codes(bytearray(ac), 6, False))
pulse_array.extend(pulse_codes(bytearray(ac)[6:], 8, False))
pulse_array.extend(pulse_codes(bytearray(ac)[14:], 7, True))

# base64_string = base64.b64encode(bytes.fromhex(pulesArrayToBroadlink(pulse_array)))

# print(base64_string)

hex = pulesArrayToBroadlink(pulse_array)

# Sending the IR command to the Broadlink device.
device = broadlink.hello('10.0.0.35')  # IP address of your Broadlink device.

device.auth()

# device.send_data(bytes.fromhex(hex))