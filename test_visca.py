from VISCACamera.VISCAInterface import VISCAInterface, usb_to_tty, ExposureMode, VISCATimeout

import time

def test_pos(cam):
	fail = False
	for pan_angle in [-90, -45, 0, 45, 90]:
		cam.cmd_pt_pos(pan_angle)
		pan_pos, tilt_pos = cam.inquiry_position()

		if abs(pan_angle - pan_pos) > 10:
			fail |= True

		#print(pan_angle, pan_pos)
	return not fail


def test_zoom(cam):
	zoom_positions = [
		0x000,
		0x100,
		0x200,
		0x300,
		0x400,
	]

	fail = False

	for zoom_pos in zoom_positions:
		cam.cmd_zoom_position(zoom_pos)
		time.sleep(1)
		read_zoom_pos = cam.inquiry_zoom_position()
		#print(zoom_pos, read_zoom_pos)

		if abs(zoom_pos - read_zoom_pos) > 10:
			fail |= True
	
	return not fail


def test_focus(cam):
	cam.cmd_focus_manual()
	assert(False == cam.inquiry_is_autofocus())

	focus_positions = [
		0x0000,
		0x0010,
		0x0100,
		0x0f00,
	]

	fail = False

	for focus_pos in focus_positions:
		cam.cmd_focus_position(focus_pos)
		read_focus_pos = cam.inquiry_focus_position()
		#print(focus_pos, read_focus_pos)

		if abs(focus_pos - read_focus_pos) > 10:
			fail |= True

	cam.cmd_focus_auto()
	assert(True == cam.inquiry_is_autofocus())

	return not fail


def test_picture(cam):
	cam.cmd_set_exposure_mode(ExposureMode.MANUAL)
	assert(ExposureMode.MANUAL == cam.inquiry_auto_exposure_mode())
	settings = cam.inquiry_picture_settings()
	cam.cmd_set_exposure_mode(ExposureMode.AUTO)
	print(settings)
	return True



cam = VISCAInterface(
	usb_to_tty(
		vid=0x0403,
		pid=0x6001,
	)
)

init = True

restarts = 3

for k in range(restarts):
	try:
		cam.cmd_if_clear()

		if init:
			cam.init()

		def evaluate(test_func):
			print(f'Testing {test_func.__name__}...')
			print('PASS' if test_func(cam) else 'FAIL')

		evaluate(test_pos)
		evaluate(test_zoom)
		evaluate(test_focus)
		evaluate(test_picture)
		break


	except VISCATimeout:
		init = True


