import subprocess
import pdb
import re
import time
import datetime
import os
import logging


def discover_devs():
	'''
	Use v4l2 to discover PTZOptics USB camera /dev/video file paths.

	Returns FileNotFoundError if PTZOptics is not found
	'''
	output = str(
		subprocess.run(
			f'v4l2-ctl --list-devices', 
			shell=True, 
			capture_output=True
		).stdout, 
		'utf-8'
	)

	device_info_blocks = output.split('\n\n')

	matches = [
		device_info
		for device_info in device_info_blocks
		if device_info.startswith('PTZOptics Move 4K')
	]

	if len(matches) == 0:
		raise FileNotFoundError('Could not find camera')

	match = matches[0]

	devs = [
		line.strip()
		for line in match.split('\n')
		if line.startswith('\t')
	]

	return devs

def default_filename_generator(*args):
	return '__'.join(args) + '__' + datetime.datetime.now().strftime(
		f'%y-%m-%d__%H-%M-%S.jpg'
	)
	


def take_picture(device_path, filename_generator=default_filename_generator, *args):
	'''
	Take a picture using /dev/video file path
	'''
	if os.path.exists('frame.mjpg'):
		os.remove('frame.mjpg')

	if os.path.exists('frame.jpg'):
		os.remove('frame.jpg')
    
	assert(False == os.path.exists('frame.mjpg'))
	assert(False == os.path.exists('frame.jpg'))

	NUM_TRIES = 16


	for k in range(NUM_TRIES):
		try:
			cmd = f'v4l2-ctl -d {device_path} --set-fmt-video=width=3840,height=2160,pixelformat=MJPG --stream-mmap --stream-to=frame.mjpg --stream-count=1'
			logging.info('taking picture...')
			subprocess.run(
				cmd, 
				shell=True, 
				capture_output=True, 
				timeout=1
			).stdout

			if not os.path.exists('frame.mjpg'):
				logging.debug('taking a frame failed...')
				continue
			else:
				logging.info('frame capture success!')

			picture = open('frame.mjpg', 'rb')

			data = picture.read()


			if not (data[0] == 0xff and data[1] == 0xd8):
				logging.debug('file does not start with ffd8')
				continue

			if not(data[-2] == 0xff and data[-1] == 0xd9):
				logging.debug('file does not end with ffd9')
				continue

			break

		except subprocess.TimeoutExpired as te:
			logging.debug('Timeout out occurred...')
			continue

	output_filename = filename_generator(*args)

	subprocess.run(
		f'cp frame.mjpg {output_filename}', 
		shell=True, 
		capture_output=True
	).stdout

	subprocess.run(
		f'cp frame.mjpg frame.jpg', 
		shell=True, 
		capture_output=True
	).stdout

	return output_filename


