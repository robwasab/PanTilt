from Lights import Lights
from PowerSwitch import PowerSwitch
#from Pump import Pump

from pan_tilt import take_picture, move_camera
import subprocess
import time

# clear the pictures
subprocess.run('rm *.jpg', shell=True).stdout

lights = Lights()
switch = PowerSwitch()

switch.setCameraPower(True)
switch.setPumpPower(True)

pan_degs = [0, 0]
tilt_degs = [90, 45]


for color in ['blue', 'cyan', 'white']:
   lights.on(color)

   for pan_deg, tilt_deg in zip(pan_degs, tilt_degs):
      move_camera(pan_deg, tilt_deg)
      prefix = f'{color}__{pan_deg}__{tilt_deg}'
      picture = take_picture(prefix=color)
      print(picture)



move_camera(0, 90)
