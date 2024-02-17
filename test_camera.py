from VISCACamera.VISCACamera import VISCACamera
import subprocess
import pdb
import re
import time
import datetime
import os
import logging

logging.basicConfig(level=logging.DEBUG)


# cleanup misc jpg files
subprocess.run('rm *.jpg', shell=True).stdout


cam = VISCACamera(init=False)


# Take a picture
print(cam.capture_image())


def tilt_example():
	'''
	Example: Sweep various tilt angles,
	'''
	# taking a picture for each one
	for tilt_angle in [0, 22.5, 45, 90]:
		pan_angle = 0
		cam.visca.cmd_pt_pos(
			pan_angle=pan_angle, 
			tilt_angle=tilt_angle
		)

		# this is just to demonstrate
		# we can add a light color to the output
		# filename
		color = 'WHITE'

		filename = cam.capture_image(
			f'COLOR={color}',
			f'PAN={pan_angle:.2f}',
			f'TILT={tilt_angle:.2f}',
		)

		print(filename)


def zoom_example():
	'''
	Sweep through various zoom positions:
	'''
	cam.visca.cmd_pt_pos(
		pan_angle=0,
		tilt_angle=90,
	)

	for zoom_pos in [0x000, 0x100, 0x200, 0x300]:
		cam.visca.cmd_zoom_position(zoom_pos)
		print('Read zoom pos:', cam.visca.inquiry_zoom_position())

		filename = cam.capture_image(
			'ZOOM=0x%x'%zoom_pos,
		)

		print(filename)


def focus_example():
	'''
	Sweep through various focus positions
	Note, we have to put the camera in manual mode first
	'''
	cam.visca.cmd_pt_pos(
		pan_angle=0,
		tilt_angle=90,
	)

	# reset zoom
	cam.visca.cmd_zoom_position(0)

	# see if we are in auto focus mode
	print('Autofocus: ', cam.visca.inquiry_is_autofocus())

	# go to manual mode
	cam.visca.cmd_focus_manual()

	for focus_pos in [0x000, 0x0010, 0x100, 0x0f00]:
		cam.visca.cmd_focus_position(focus_pos)
		print('Read focus pos: ', cam.visca.inquiry_focus_position())

		filename = cam.capture_image(
			'FOCUS=0x%x'%focus_pos,
		)

		print(filename)

	# restore autofocus
	cam.visca.cmd_focus_auto()
		

def picture_settings_example():
	'''
	This shows how to read the current exposure settings
	'''
	print(
		cam.visca.inquiry_picture_settings()
	)



tilt_example()
zoom_example()
focus_example()
picture_settings_example()


