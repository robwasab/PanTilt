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


def test_aperature(cam):
	'''
	This example shows how to set the aperature

	Setting aperature seems to work in both
	manual and auto exposure mode
	'''

	for value in range(1):
		print('Testing aperature: ', value)

		cam.cmd_aperature_gain_set_value(value)
		settings = cam.inquiry_picture_settings()
		assert(settings['aperature'] == value)

	cam.cmd_aperature_gain_reset()
	print(cam.inquiry_picture_settings())
	return True


def test_gain(cam):
	cam.cmd_set_exposure_mode(ExposureMode.MANUAL)
	for gain in [0, 16, 32, 64]:
		print('testing gain: ', gain)
		cam.cmd_gain_set_value(gain)
		print(cam.inquiry_picture_settings())
	return True


def test_exposure_comp(cam):
	# Test enable compensation
	cam.cmd_exposure_comp_enable()
	assert(True == cam.inquiry_exposure_comp_is_enabled())

	# Test disabling compensation
	cam.cmd_exposure_comp_disable()
	assert(False == cam.inquiry_exposure_comp_is_enabled())

	# Enable compensation or else set commands wont work
	cam.cmd_exposure_comp_enable()
	assert(True == cam.inquiry_exposure_comp_is_enabled())

	for value in range(15):
		cam.cmd_exposure_comp_set_value(value)

		read_val = cam.inquiry_exposure_comp_get_value()
		print(f"Set exposure comp to: {value}, read {read_val}")
		assert(read_val == value)

	print('resetting exposure compensation')
	cam.cmd_exposure_comp_reset()
	print('reset value: ', cam.inquiry_exposure_comp_get_value())
	return True


def test_shutter(cam):
	for value in range(1, 18):
		cam.cmd_shutter_set_value(value)

		read_val = cam.inquiry_shutter_get_value()

		print(f'setting shutter to: {value}, read: {read_val}') 
		assert(read_val == value)

	print('resetting shutter')
	cam.cmd_shutter_reset()
	print('read shutter value: ', cam.inquiry_shutter_get_value())
	return True


cam = VISCAInterface(
	usb_to_tty(
		vid=0x0403,
		pid=0x6001,
	)
)

init = False

restarts = 3

for k in range(restarts):
	try:
		cam.cmd_if_clear()

		if init:
			print('initializing')
			cam.init()

		def evaluate(test_func):
			print(f'Testing {test_func.__name__}...')
			print('PASS' if test_func(cam) else 'FAIL')

		evaluate(test_pos)
		evaluate(test_zoom)
		evaluate(test_focus)
		evaluate(test_picture)
		evaluate(test_aperature)
		evaluate(test_gain)
		evaluate(test_exposure_comp)
		evaluate(test_shutter)
		break


	except VISCATimeout:
		init = True
		print('VISCA timeout')


