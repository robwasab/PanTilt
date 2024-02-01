from Lights import Lights
from PowerSwitch import PowerSwitch
from Pump import Pump

from pan_tilt import take_picture, move_camera
import subprocess
import time

# clear the pictures
subprocess.run('rm *.jpg', shell=True).stdout

lights = Lights()
switch = PowerSwitch()
pump = Pump()

switch.setCameraPower(True)
switch.setPumpPower(True)

pan_degs = [0, 0]
tilt_degs = [90, 45]

toggle = False

pan_offset = 0

for color in ['violet', 'blue', 'cyan', 'white']:
   lights.on(color)


   for pan_deg, tilt_deg in zip(pan_degs, tilt_degs):
      if toggle:
         pump.startDispense('white')
         pump.stopDispense('orange')
      else:
         pump.startDispense('orange')
         pump.stopDispense('white')

      move_camera(
         ((pan_offset + pan_deg) % 360) - 180, 
         tilt_deg
      )
      prefix = f'{color}__{pan_deg}__{tilt_deg}'
      picture = take_picture(prefix=color)
      print(picture)

      pan_offset += 45
      toggle ^= True

pump.stopDispense('white')
pump.stopDispense('orange')

move_camera(0, 90)
