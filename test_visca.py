from VISCACamera.VISCAInterface import VISCAInterface, usb_to_tty
import time

def test_init(cam):
	cam.cmd_address_set()

	cam.cmd_if_clear()

	cam.cmd_pt_reset()

	info = cam.inquiry_camera_version()

	print(f'Firmware Info:')
	print(f"vendor id: {info['vendor_id_str']}")
	print(f"model  id: {info['model_id_str']}")
	print(f"rom versi: {info['rom_version_str']}")

	cam.cmd_home()

def test_pos(cam):
	fail = False
	for pan_angle in [-90, -45, 0, 45, 90]:
		cam.cmd_pt_pos(pan_angle)
		pan_pos, tilt_pos = cam.inquiry_position()

		if abs(pan_angle - pan_pos) > 10:
			fail |= True

		print(pan_angle, pan_pos)
	return fail


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
		print(zoom_pos, read_zoom_pos)

		if abs(zoom_pos - read_zoom_pos) > 10:
			fail |= True
	
	return fail


def test_zoom_and_focus(cam):
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
		print(focus_pos, read_focus_pos)

		if abs(focus_pos - read_focus_pos) > 10:
			fail |= True

	cam.cmd_focus_auto()
	assert(True == cam.inquiry_is_autofocus())

	return fail


def test_picture(cam):
	print(
		cam.inquiry_picture_settings()
	)
	#cam.cmd_set_red_gain(61)
	print(
		cam.inquiry_picture_settings()
	)



cam = VISCAInterface(
	usb_to_tty(
		vid=0x0403,
		pid=0x6001,
	)
)

cam.cmd_if_clear()
test_init(cam)
test_pos(cam)
test_zoom(cam)
test_zoom_and_focus(cam)
test_picture(cam)


