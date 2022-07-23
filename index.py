import ctypes

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



setMode(kWhirlpoolAcCool)


setSwing(False)

setLight(False)


setPower(False)

setFan(kWhirlpoolAcFanLow)
setTemp(26)
setClock(2,0)

checksum()

print(bytes(ac))