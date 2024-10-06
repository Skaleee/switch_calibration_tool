import hid
import hid_utils

def setColorType(device, type: str):
    """
    type = "NoCustom"|"CustomBodyAndButtons"|"AllCustom"
    """
    byte = 0x0
    if type == "NoCustom":
        byte = 0x0
    elif type == "CustomBodyAndButtons":
        byte = 0x1
    elif type == "AllCustom":
        byte = 0x2
    else:
        return False
    
    return hid_utils.write_spi_flash(device, 0x601B, [byte])

def printDeviceInfo(deviceDict):
    print(f'Found: vid: {deviceDict["vendor_id"]}, pid: {deviceDict["product_id"]}, SN: {deviceDict["serial_number"]}, interface_number: {deviceDict["interface_number"]}')
    print(f'       path: {deviceDict["path"]}')
    print(f'       Manufacturer: {deviceDict["manufacturer_string"]}')
    print(f'       Product: {deviceDict["product_string"]}')
    
def tryConnectController():
    """
    I only support pro controller, though the code is modifyable
    """
    vendor_id = 0x57e
    proConID = 0x2009

    devs = hid.enumerate(vendor_id,product_id=proConID)
    for dev in devs:
        if dev["product_id"] != proConID:
            continue
        printDeviceInfo(dev)
        device = hid.device()

        hid_utils.setBluetooth(True)
        if dev["serial_number"]=="000000000001":
            hid_utils.setBluetooth(False)

        if dev["interface_number"] == 0 or dev["interface_number"] == -1:
            device.open_path(dev["path"])
        else:
            continue

        if not hid_utils.isBluetooth():
            response = hid_utils.hid_exchange(device,[0x80, 0x01])
            if response[2]==0x3:
                print("Controller disconnected")
            else:
                sn = ""
                for i in range(6):
                    sn+= f"{response[9-i]:x}"
                print(f'Found: SN: {sn.upper()}')

            hid_utils.hid_exchange(device,[0x80, 0x02]) # handshaking
            hid_utils.hid_exchange(device,[0x80, 0x03]) # switch baudrate to 3Mbit
            hid_utils.hid_exchange(device,[0x80, 0x02]) # handshaking again?
            hid_utils.hid_exchange(device,[0x80, 0x04]) # Only talk HID from now on

            print("Initialised")
        return device

def disconnectController(device):
    hid_utils.hid_exchange(device,[0x80, 0b1111])
    print("Disconnected")