import hid

bluetooth = True

def setBluetooth(isBluetooth: bool):
    global bluetooth
    bluetooth = isBluetooth

def isBluetooth():
    global bluetooth
    return bluetooth

def hid_exchange(device, data):
    device.write(data)
    return device.read(128)


def hex_dump(buf: bytearray):
    for i in buf:
        print(f"{hex(i)} ", end="")
    print()
    print()

def send_command(device: hid.device, command: int, data: bytearray):
    buf = None
    if not bluetooth:
        buf = [0x0]*9
        buf[0] = 0x80
        buf[1] = 0x92
        buf[3] = 0x31

        buf[8] = command
    else:
        buf = [0]*1
        buf[0] = command

    if data is not None:
        buf = buf + data
    device.write(buf)

def send_subcommand(device: hid.device, command: int, subcommand: int, data: bytearray):

    send_subcommand.global_count += 1
    buf = [send_subcommand.global_count&0xF, 0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40, 
           subcommand]
    buf = buf + data

    send_command(device, command, buf)
send_subcommand.global_count = 0

def address_to_bytearray(address):
    arr = []
    for i in range(4):
        b = address&0xFF
        arr.append(b) 
        address = address>>8
    return arr

def read_spi_flash(device: hid.device, address: int, len: int):
    """len <= 0x1D"""
    if len > 0x1D:
        len = 0x1D
    if len < 0:
        len = 0
    if address < 0 or address >= 2**19:
        return
    address_arr = address_to_bytearray(address)
    for j in range(20):
        send_subcommand(device, 0x1, 0x10, address_arr+[len])
        for i in range(10):
            wrong = False
            data = device.read(64)
            if not isBluetooth():
                data = data[10:]
            # make sure we got the real packet with our requested data
            # would fail the first time on each read for consecutive reads (too fast maybe?)
            if data[0] == 0x21:
                for i in range(4):
                    if data[(0xF)+i] != address_arr[i]:
                        wrong = True
                        break

                if not wrong:
                    return data[0x14:0x14+len]
            print(".", end="")
    return None

def write_spi_flash(device: hid.device, address: int, data: bytearray):
    """len(data) <= 0x1D"""
    if len(data) > 0x1D:
        return False
    if address < 0x2000 or address >= (0x10000-len(data)):
        return False
    
    address_arr = address_to_bytearray(address)
    for j in range(20):
        send_subcommand(device, 0x1, 0x11, address_arr+[len(data)]+data)
        for i in range(10):
            data = device.read(64)
            if not isBluetooth():
                data = data[10:]

            # make sure we got the ack
            # would fail the first time on each read for consecutive reads (too fast maybe?)
            if data[13:16] == [0x80,0x11,0x00]: # ack and success flag
                return True
            print(":", end="")
    return False

def setPlayerLED(device, nibblePattern : int):
    """
    pattern counts the in binary.
    lowest player number is lowest bit
    """
    send_subcommand(device,1,0x30,[nibblePattern])


