from smbus2 import SMBus, i2c_msg
from PowerSwitch import PowerSwitch
import subprocess
import time
import pdb


PUMP_ADDR_0 = 0x38
PUMP_ADDR_1 = 0x39
PUMP_ADDR_2 = 0x3A

color2addr = {
   'orange': PUMP_ADDR_0,
   'white' : PUMP_ADDR_1,
   'yellow': PUMP_ADDR_2,
}

class Pump(object):

   def startDispense(self, color):
      addr = '%02x'%color2addr[color]
      cmd = f'i2cset -y 1 0x{addr} 0x44 0x2c 0x2a i'
      subprocess.call(cmd, shell=True)


   def stopDispense(self, color):
      addr = color2addr[color]
      addr = '%02x'%color2addr[color]
      cmd = f'i2cset -y 1 0x{addr} 0x78'
      subprocess.call(cmd, shell=True)



      


if __name__ == '__main__':
   import time
   pwr = PowerSwitch()
   pwr.setPumpPower(True)
   time.sleep(.1)

   pump = Pump()

   pump.startDispense('white')

   pdb.set_trace()

