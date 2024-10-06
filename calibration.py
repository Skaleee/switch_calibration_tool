import hid
from hid_utils import *
import time
import msvcrt
import controller_actions

def print_stick_dict(stick, subtract=False):
    """
    subtract: If True, actual min and max are printed. 
                Else, does not subtract the calibration minimum from the middle.
    """
    if not subtract:
        print(f'       min |  mid |  max')
        print(f'horz: {hex(stick["hmin"])}, {hex(stick["hmid"])}, {hex(stick["hmax"])}')
        print(f'vert: {hex(stick["vmin"])}, {hex(stick["vmid"])}, {hex(stick["vmax"])}')
    else:
        print(f'       min |  mid |  max')
        print(f'horz: {hex(stick["hmid"]-stick["hmin"])}, {hex(stick["hmid"])}, {hex(stick["hmid"]+stick["hmax"])}')
        print(f'vert: {hex(stick["vmid"]-stick["vmin"])}, {hex(stick["vmid"])}, {hex(stick["vmid"]+stick["vmax"])}')

def find_calibration_values(device, isLeft: bool):
    """
    Does not actually return trustable values, because they depend on the current calibration.
    But you can use the current values to deduce the difference between the current stick position and where 0,0 should be.
    """
    lhmin = None
    lhmax = None
    rhmin = None
    rhmax = None
    lvmin = None
    lvmax = None
    rvmin = None
    rvmax = None
    while True:
        state = device.read(64)
        left, right = stick_data_to_values(state[6:12])

        if lhmin is None or left[0] < lhmin:
            lhmin = left[0]
        if lhmax is None or left[0] > lhmax:
            lhmax = left[0]
        if lvmin is None or left[1] < lvmin:
            lvmin = left[1]
        if lvmax is None or left[1] > lvmax:
            lvmax = left[1]
        
        if rhmin is None or right[0] < rhmin:
            rhmin = right[0]
        if rhmax is None or right[0] > rhmax:
            rhmax = right[0]
        if rvmin is None or right[1] < rvmin:
            rvmin = right[1]
        if rvmax is None or right[1] > rvmax:
            rvmax = right[1]

        print(f"current left: {hex(left[0])}, {hex(left[1])} | right: {hex(right[0])}, {hex(right[1])}")
        if isLeft:
            print(f'left:   min |  mid |  max')
            print(f'horz: {hex(lhmin)}, {hex((lhmax+lhmin)//2)}, {hex(lhmax)}')
            print(f'vert: {hex(lvmin)}, {hex((lvmax+lvmin)//2)}, {hex(lvmax)}')
        else:
            print(f'right:')
            print(f'horz: {hex(lhmin)}, {hex((lhmax+lhmin)//2)}, {hex(lhmax)}')
            print(f'vert: {hex(lvmin)}, {hex((lvmax+lvmin)//2)}, {hex(lvmax)}')

        if msvcrt.kbhit():
            if msvcrt.getch().decode('utf-8') in ['q','Q']:
                break
            
        for i in range(4):
            print('\033[1A',end='')
            print('\x1b[2K',end='')

        """left = {"hmin":lhmin, "vmin":lvmin, 
                "hmax":lhmax, "vmax":lvmax, 
                "hmid":(lhmax+lhmin)//2, "vmid":(lvmax+lvmin)//2}
        right = {"hmin":rhmin, "vmin":rvmin, 
                 "hmax":rhmax, "vmax":rvmax, 
                 "hmid":(rhmax+rhmin)//2, "vmid":(rvmax+rvmin)//2}"""
    print()
    return left, right

def decode_stick(data):
    """current value in very response"""
    horz = data[0] | ((data[1] & 0xF) << 8)
    vert = (data[1] >> 4) | (data[2]  << 4)
    return horz, vert

def stick_data_to_values(data):
    """from current stick values in every response"""
    left = data[:3]
    left = decode_stick(left)
    right = data[3:6]
    right = decode_stick(right)
    return left, right

def decode_calibration(data):
    values = [0]*6
    values[0] = (data[1] << 8) & 0xF00 | data[0]
    values[1] = (data[2] << 4) | (data[1] >> 4)
    values[2] = (data[4] << 8) & 0xF00 | data[3]
    values[3] = (data[5] << 4) | (data[4] >> 4)
    values[4] = (data[7] << 8) & 0xF00 | data[6]
    values[5] = (data[8] << 4) | (data[7] >> 4)
    return values

def encode_calibration(values):
    data = [0]*9
    data[0] = values[0] & 0xFF
    data[1] = (values[0]>>8) & 0xF | (values[1]<<4) & 0xF0
    data[2] = (values[1]>>4) & 0xFF
    data[3] = values[2] & 0xFF
    data[4] = (values[2]>>8) & 0xF | (values[3]<<4) & 0xF0
    data[5] = (values[3]>>4) & 0xFF
    data[6] = values[4] & 0xFF
    data[7] = (values[4]>>8) & 0xF | (values[5]<<4) & 0xF0
    data[8] = (values[5]>>4) & 0xFF
    return data

def calibration_data_to_values(data, left=True):
    """0x603D 18 bytes"""
    values = decode_calibration(data)
    if left:
        dic = {"hmin":values[4], "vmin":values[5], 
                "hmax":values[0], "vmax":values[1], 
                "hmid":values[2], "vmid":values[3]}
    else:
        dic = {"hmin":values[2], "vmin":values[3], 
                "hmax":values[4], "vmax":values[5], 
                "hmid":values[0], "vmid":values[1]}
    return dic

def values_to_calibration_data(values, left=True):
    if left:
        arr = [values["hmax"], values["vmax"], values["hmid"], values["vmid"], values["hmin"], values["vmin"]]
    else:
        arr = [values["hmid"], values["vmid"], values["hmin"], values["vmin"], values["hmax"], values["vmax"]]
    return encode_calibration(arr)

def copyCalibration(device, source: str):
    """
    source="User"|"Factory"
    destination will be the other one
    """
    data = read_spi_flash(device, 0x8012 if source=="User" else 0x603D, 20)
    if data is None:
        print("Reading err")
        return
    if source=="User":
        data = data[:9]+data[9+2:9+2+9]
    else:
        data = data[0:18]
        
    res = write_spi_flash(device, 0x603D if source=="User" else 0x8012, data)
    if not res:
        print("Writing err")

def readCalibration(device, section: str, left: bool):
    """
    section="User"|"Factory"
    """
    address = 0x603D
    if section == "User":
        address = 0x8012
        if not left:
            address+=9+2
    else: # already 0603D
        if not left:
            address+=9
    data = read_spi_flash(device,address, 9)
    stick = calibration_data_to_values(data, left)
    return stick

def writeCalibration(device, section: str, left: bool, stick):
    """
    section="User"|"Factory"
    """
    data = values_to_calibration_data(stick, left)
    if len(data) != 9:
        return False
    
    address = 0x603D
    if section == "User":
        address = 0x8012
        if not left:
            address+=9+2
    else: # already 0603D
        if not left:
            address+=9
    return write_spi_flash(device, address, data)

def changeCalibrationValue(stick, calName, newValue):
    print(f"changing {calName}={hex(newValue)}")
    stick[calName] = newValue

if __name__ == "__main__":
    a = controller_actions.tryConnectController()

    left = readCalibration(a,"Factory",True)
    print()
    print("left")
    print_stick_dict(left, False)
    print()
    changeCalibrationValue(left, "vmin",0x600)
    changeCalibrationValue(left, "vmid",0x6e4+0x3b)
    changeCalibrationValue(left, "vmax",0x600)

    print(writeCalibration(a,"Factory",True,left))
    find_calibration_values(a, True)

    #controller_actions.copyCalibration(a,"User")

    #controller_actions.disconnectController(a)
    a.close()
