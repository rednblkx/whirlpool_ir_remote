import ctypes
from bitstring import BitArray

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
        ("ClockHours", ctypes.c_uint8, 1),
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
    if (super):
        setFan(kWhirlpoolAcFanHigh)
        match ac.Mode:
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


def irCode(headermark, headerspace, onemark, onespace, zeromark, zerospace, footermark, gap, data, nbytes):
    # Header
    print(headermark, end=', ')
    print(headerspace, end=', ')
    # Data
    for i in range(0, nbytes):
        # data >>= 1
        # print(int(data[i]) & 1)
        if (int(bytes(ac)[i]) & 1):
            print(onemark, end=', ')
            print(onespace, end=', ')
        else:
            print(zeromark, end=', ')
            print(zerospace, end=', ')
    # data >>= 1
    # Footer
    print(footermark, end=', ')
    print(gap)

setMode(kWhirlpoolAcCool)


setSwing(False)

setLight(True)



setFan(0)
setTemp(18)
setClock(1,22)

setPower(True)

checksum()

print(bytes(ac))


c = BitArray(bytes=bytes(ac))

l = bytearray(21)

value = int.from_bytes(ac, byteorder='big')
print(bin(value))
for i in range(0, 6):
    value >>= 1
    print(bin(value))
# print(c & l)

irCode(kWhirlpoolAcHdrMark, kWhirlpoolAcHdrSpace, kWhirlpoolAcBitMark, kWhirlpoolAcOneSpace, kWhirlpoolAcBitMark, kWhirlpoolAcZeroSpace, kWhirlpoolAcBitMark, kWhirlpoolAcGap, c, 6)

