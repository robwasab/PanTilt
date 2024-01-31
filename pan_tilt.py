import subprocess
import pdb
import re
import time
import datetime
import os

PAN_MIN = -612000
PAN_MAX = +612000

TILT_MIN = -108000
TILT_MAX = 324000


def move_camera(pan_deg, tilt_deg):
	'''
	pan_deg ranges from -180 to 180 degrees
	tilt_deg ranges from +90 to -30
	'''
	pan_val = int(pan_deg / 180 * PAN_MAX)
	pan_val = min(PAN_MAX, pan_val)
	pan_val = max(PAN_MIN, pan_val)

	tilt_val = int(tilt_deg / 90 * TILT_MAX)
	tilt_val = min(TILT_MAX, tilt_val)
	tilt_val = max(TILT_MIN, tilt_val)

	cmd = f'v4l2-ctl -d /dev/video0 --set-ctrl pan_absolute={pan_val},tilt_absolute={tilt_val}'
	subprocess.call(cmd, shell=True)

	time.sleep(1)


def get_pan_tilt():
	cmd = f'v4l2-ctl -d /dev/video0 --get-ctrl tilt_absolute,pan_absolute'
	output = subprocess.run(
		cmd, 
		shell=True, 
		capture_output=True, 
		encoding='utf-8'
	).stdout

	match = re.search(r'tilt_absolute: ([-\d]+)\s+pan_absolute: ([-\d]+)', output)

	assert(match)

	print(match.group(0))

	tilt = int( int(match.group(1)) / TILT_MAX * 90 )
	pan = int( int(match.group(2)) / PAN_MAX * 180 )
	
	print(tilt)
	print(pan)

	return pan, tilt



def set_auto_focus():
	cmd = f'v4l2-ctl -d /dev/video0 --set-ctrl focus_automatic_continuous=1'
	subprocess.run(cmd, shell=True, capture_output=True).stdout
	


def take_picture():
	if os.path.exists('frame.mjpg'):
		os.remove('frame.mjpg')

	if os.path.exists('frame.jpg'):
		os.remove('frame.jpg')
	
	assert(False == os.path.exists('frame.mjpg'))
	assert(False == os.path.exists('frame.jpg'))

	NUM_TRIES = 16
	basename = datetime.datetime.now().strftime('%y-%m-%d__%H-%M-%S')

	for k in range(NUM_TRIES):
		cmd = f'v4l2-ctl -d /dev/video0 --set-fmt-video=width=3840,height=2160,pixelformat=MJPG --stream-mmap --stream-to=frame.mjpg --stream-count=1'
		print('taking picture...')
		subprocess.run(cmd, shell=True, capture_output=True, timeout=1).stdout

		if not os.path.exists('frame.mjpg'):
			print('taking a frame failed...')
			continue

		convert_cmd = f'ffmpeg -y -i frame.mjpg -bsf:v mjpeg2jpeg frame.jpg'
		print('converting picture...')
		subprocess.run(convert_cmd, shell=True, capture_output=True, timeout=1).stdout

		if not os.path.exists('frame.jpg'):
			print('converting failed...')
			continue

		break

	subprocess.run(f'mv frame.jpg {basename}.jpg', shell=True, capture_output=True).stdout

	subprocess.run(f'rm frame.mjpg', shell=True, capture_output=True).stdout

	print(basename)



pan, tilt = get_pan_tilt()

tilt += 10
if tilt > 90:
	tilt = (tilt - 90) + -30

print('setting tilt to: ', tilt)

move_camera(pan_deg=0, tilt_deg=tilt)
set_auto_focus()
take_picture()

