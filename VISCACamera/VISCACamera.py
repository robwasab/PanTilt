from .VISCAInterface import VISCAInterface, usb_to_tty
from .usb_camera_utils import take_picture, discover_devs
import logging
import datetime


class VISCACamera(object):
	'''
	@param init [bool]: If True, the camera performs a homing sequence
	to calibrate its positioning encoders. This can take a few seconds.
	'''
	def __init__(self, init=True):
		devices = discover_devs()
		for device in devices:
			logging.info(device)

		self.dev = devices[0]

		self.visca = VISCAInterface(
			usb_to_tty(
				vid=0x0403,
				pid=0x6001,
			)
		)

		if init:
			self.visca.init()

		self.visca.cmd_pt_pos(
			pan_angle=0, 
			tilt_angle=90
		)


	def filename_generator(self, *args):
		return (
			'__'.join(args) + 
			'__' + datetime.datetime.now().strftime(
				f'%y-%m-%d__%H-%M-%S.jpg'
			)
		)


	def capture_image(self, *args):
		return take_picture(
			self.dev, 
			self.filename_generator,
			*args,
		)

