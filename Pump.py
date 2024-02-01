from smbus2 import SMBus, i2c_msg

bus = SMBus(0)

PUMP_ADDR_0 = 0x38
PUMP_ADDR_1 = 0x39
PUMP_ADDR_2 = 0x3A



def send_cmd(addr, cmd_data, num2read):
   
   with SMBus(1) as bus:
      # write the command data
      cmd_msg = i2c_msg.write(addr, cmd_data)

      # read data + 1 for a status byte back
      rsp_msg = i2c_msg.read(addr, num2read + 1)

      bus.i2c_rdwr(cmd_msg, rsp_msg)

      print(rsp_msg)

   return bytearray(rsp_msg)


def get_fw_version():
   rsp = send_cmd(PUMP_ADDR_2, [ord('i')], 16)
   print(rsp)

get_fw_version()

