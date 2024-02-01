import RPi.GPIO as GPIO

PUMP_PWR_EN = 11
CAMERA_PWR_EN = 13

class PowerSwitch(object):
   def __init__(self):
      GPIO.setmode(GPIO.BOARD)
      for pin in [PUMP_PWR_EN, CAMERA_PWR_EN]:
         GPIO.setup(pin, GPIO.OUT)
         GPIO.output(pin, 0)

   def setCameraPower(self, val):
      GPIO.output(CAMERA_PWR_EN, val)

   def setPumpPower(self, val):
      GPIO.output(PUMP_PWR_EN, val)

