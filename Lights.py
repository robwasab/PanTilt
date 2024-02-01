import RPi.GPIO as GPIO
import pdb

UV_PIN     = 29
VIOLET_PIN = 31
BLUE_PIN   = 33
CYAN_PIN   = 35
WHITE_PIN  = 37

colors = {
   'uv': UV_PIN,
   'violet': VIOLET_PIN,
   'blue': BLUE_PIN,
   'cyan': CYAN_PIN,
   'white': WHITE_PIN,
}

class Lights(object):
   def __init__(self):
      GPIO.setmode(GPIO.BOARD)
      for color in colors:
         GPIO.setup(colors[color], GPIO.OUT)
         GPIO.output(colors[color], 0)

   def __del__(self):
      self.allOff()


   def allOff(self):
      for color in colors:
         GPIO.output(colors[color], 0)


   def on(self, color):
      self.allOff()
      GPIO.output(colors[color], 1)

if __name__ == '__main__':
   lights = Lights()

   pdb.set_trace()
   
