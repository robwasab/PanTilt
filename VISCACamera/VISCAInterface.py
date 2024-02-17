from serial.tools import list_ports
import serial
import pdb
import time
import os
import logging

from enum import Enum
from enum import auto


'''
class logging(object):
	@classmethod
	def debug(cls, *args, **kwargs):
		print(*args, **kwargs)
'''

#cmd = bytearray.fromhex('FF 01 00 04 3F 00 44')
#ser = serial.Serial('COM3', 9600)

def hexstr(arr):
	return ' '.join(
		'%02x'%b for b in arr
	)


def hex_alphanum(value, nibble_pos):
	'''
	Examples:
	hex_alphanum(value=0x1234, nibble_pos=0) -> '4'
	hex_alphanum(value=0x1234, nibble_pos=1) -> '3'
	hex_alphanum(value=0x1234, nibble_pos=2) -> '2'
	hex_alphanum(value=0x1234, nibble_pos=3) -> '1'
	
	'''
	mask = 0x0f << (4 * nibble_pos)
	return '%x'%(
		(value & mask) >> (4 * nibble_pos)
	)



# VISCA Response codes, per specification
RSP_TYPE_ACK = 4
RSP_TYPE_COMPLETE = 5
RSP_TYPE_ERR = 6
# this is my own response type
RSP_TYPE_INQUIRY = 100
TIMEOUT_SEC = 20


class VISCAError(Enum):
	'''
	Enum object representing the possible VISCA error codes if
	RSP_TYPE_ERR is returned by a command
	'''
	NONE = auto()
	UNK_RECV_ADDR = auto()
	UNK_RSP_TYPE = auto()


class ExposureMode(Enum):
	AUTO = auto()
	MANUAL = auto()
	SHUTTER_PRIORITY = auto()
	IRIS_PRIORITY = auto()
	BRIGHT = auto()


class VISCATimeout(Exception):
	pass


def usb_to_tty(vid, pid, serial_number=None): 
	'''
	Given USB Vendor ID, and Product ID, return the associated dev path
	If there are two of the same type of USB to serial converters connected
	Use serial_number to distinguish between the two.
	'''
	for port in list_ports.comports():
		if port.vid and port.pid:
			if (vid == port.vid) and (pid == port.pid):
				if serial_number:
					if serial_number == port.serial_number:
						return os.path.join('/dev', port.name)
				else:
					return os.path.join('/dev', port.name)


class VISCAInterface(object):
	'''
	All commands can raise a VISCATimeout exception.
	Since the interface is RS232, it is possible for a
	command to get either corrupted or lost in either 
	the camera system or our own OS.

	Therefore, if we are sitting, waiting for a response
	for too much time, we raise a VISCATimeout exception,
	which you can use to restart the camera and walk up 
	the stack to a point where you can begin your routine
	again, potentially resetting the camera at the beginning
	to a known stage.
	'''
	def __init__(self, serial_address, baud_rate=9600):
		self.ser = serial.Serial(
			serial_address,
			baud_rate,
			timeout=5,
		)

	def send_bytes(self, payload):
		'''
		Use this method to send bytes object via serial port
		- prints out sent data
		- waits for 200ms
		- read serial port and format raw data responses into dictionary objects
		'''
		#logging.debug('>> ', hexstr(payload))
		self.ser.write(payload)
		# per VISCA standard, wait for 200 ms
		time.sleep(.5)
		return self.process_rx()


	def send_hex_str(self, hex_str):
		'''
		convenience method to send data formatted as hex string
		'''
		return self.send_bytes(
			bytearray.fromhex(hex_str)
		)


	def send_and_block(self, payload, wait_for=RSP_TYPE_COMPLETE):
		'''
		blocks until response complete has been received

		payload may be either bytearray or hexstring
		'''
		if type(payload) is str:
			payload = bytearray.fromhex(payload)

		assert(type(payload) is bytearray)

		self.ser.write(payload)
		time.sleep(0.5)

		start_time = time.time()
		last_time = start_time
		done = False

		responses = []

		while not done:
			responses.extend(
				self.process_rx()
			)

			for rsp in responses:
				if rsp['error'] == VISCAError.NONE:
					if rsp['rsp_type'] == wait_for:
						done=True

			if time.time() > (last_time + 1):
				last_time = time.time()
				sec_elapsed = time.time() - start_time
				logging.debug('%.3f sec elapsed...'%sec_elapsed)

			if time.time() > (start_time + TIMEOUT_SEC):
				raise VISCATimeout()

		return responses


	def process_rx(self):
		'''
		read receive serial buffer
		each packet is terminated with 0xff byte
		'''
		packets = []
		packet_no = 0

		while 0 < self.ser.in_waiting:
			raw_data = self.ser.read_until(
				expected=b'\xFF'
			)

			#logging.debug(f'<<  [raw packet {packet_no}] [{hexstr(raw_data)}]')
			packet_no += 1

			packets.append(raw_data)

		responses = [
			VISCAInterface.process_header(packet)
			for packet in packets
		]

		return responses


	@classmethod
	def process_header(cls, data):
		'''
		classmethod because this is stateless
		'''

		header = data[0]
		sender_addr = (header & 0x70) >> 4
		receiv_addr = (header & 0x3)

		if receiv_addr != 0:
			#print('not addressed to us, ignoring...')
			return {
				'error': VISCAError.UNK_RECV_ADDR,
				'data': data[2:],
			}

		rsp_type = data[1] >> 4
		sock_num = data[1] & 0xf

		rsp_type_map = {
			RSP_TYPE_ACK: 'ack',
			RSP_TYPE_COMPLETE: 'completion/inquiry',
			RSP_TYPE_ERR: 'error'
		}
		try:
			rsp_type_str = rsp_type_map[rsp_type]
		except KeyError:
			#print('Unknown response type..')
			return {
				'error': VISCAError.UNK_RSP_TYPE,
				'data': data[2:],
			}

		#print("sender: %d"%sender_addr)
		#print("receiv: %d"%receiv_addr)
		#print("resp_type: %d (%s)"%(rsp_type, rsp_type_str))
		#print("socket: %d"%sock_num)


		if RSP_TYPE_ERR == rsp_type:
			err_type = data[2]
			err_type_map = {
				1: 'msg len',
				2: 'syntax err',
				3: 'cmd buf full',
				4: 'cmd cancelled',
				5: 'no socket to be cancelled',
				0x41: 'cmd not executable',
			}
			#print('error: %s'%err_type_map[err_type])
			return {
				'error': VISCAError.NONE,
				'data': data[2:],
				'rsp_type': rsp_type,
				'rsp_type_str': rsp_type_str,
				'error_str': err_type_map[err_type],
				'sock_num': sock_num,
			}
		else:
			if (rsp_type == RSP_TYPE_COMPLETE) and (1 < len(data[2:])):
				rsp_type = RSP_TYPE_INQUIRY

			return {
				'error': VISCAError.NONE,
				'data': data[2:],
				'rsp_type': rsp_type,
				'rsp_type_str': rsp_type_str,
				'sock_num': sock_num,
			}


	def cmd_address_set(self):
		logging.debug("cmd_address_set()")
		data = bytes([0x88, 0x30, 0x01, 0xff])
		self.send_bytes(data)


	def cmd_home(self):
		logging.debug("cmd_home()")
		self.send_and_block(
			'81 01 06 04 FF',
		)


	def cmd_if_clear(self):
		logging.debug("cmd_if_clear()")
		self.send_bytes(
			bytearray.fromhex('88 01 00 01 FF')
		)


	@classmethod
	def filter_responses(cls, responses, **search_dict):
		'''
		Commands can return multiple responses, this method helps
		filter out a single response given some search terms
		'''
		for rsp in responses:
			for key in search_dict:
				if rsp[key] != search_dict[key]:
					break
			else:
				# made it through all of the search terms, return this
				return rsp


	def inquiry_camera_version(self):
		logging.debug("inquiry_camera_version()")
		camera = 1
		hex_str = f'8{camera} 09 00 02 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type = RSP_TYPE_INQUIRY
		)

		data = rsp['data']

		if len(data) < 7:
			logging.debug('could not parse inquiry')
			return

		vendor_id = data[:2]
		model_id = data[2:4]
		rom_version = data[4:6]
		max_sockets = int(data[6])

		#logging.debug(f'vendor_id: {hexstr(vendor_id)}')
		#logging.debug(f' model_id: {hexstr(model_id)}')
		#logging.debug(f' rom_vers: {hexstr(rom_version)}')
		#logging.debug(f' max_sock: {max_sockets}')

		return {
			'vendor_id'      : vendor_id,
			'vendor_id_str'  : hexstr(vendor_id),
			'model_id'       : model_id,
			'model_id_str'   : hexstr(model_id),
			'rom_version'    : rom_version,
			'rom_version_str': hexstr(rom_version),
		}


	@classmethod
	def convert_to_signed(cls, val):
		'''
		Converts a signed 16 bit number into a signed
		system integer number.
		'''
		if val & (1 << 15):
			return -(1 + (0xffff - val))
		else:
			return val


	def inquiry_position(self):
		logging.debug('inquiry_position()')
		hex_str = f'81 09 06 12 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type=RSP_TYPE_INQUIRY,
		)

		assert(rsp)

		data = rsp['data']

		pan_hex_str = ''.join(
			'%x'%c
			for c in data[:4]
		)
		tilt_hex_str = ''.join(
			'%x'%c
			for c in data[4:8]
		)

		pan_val = VISCAInterface.convert_to_signed(
			int(pan_hex_str, 16)
		) / 5120 * 360

		tilt_val = VISCAInterface.convert_to_signed(
			int(tilt_hex_str, 16)
		) / 5120 * 360

		return pan_val, tilt_val



	def cmd_pt_reset(self):
		logging.debug("cmd_pt_reset()")
		hex_str = '81 01 06 05 FF'
		self.send_and_block(hex_str)


	"""
	def cmd_pan_up(self, pan_speed=1, tilt_speed=0):
		logging.debug("cmd_pan_up()")
		hex_str = '81 01 06 01 %02x %02x 03 01 FF'%(pan_speed, tilt_speed)
		logging.debug(hex_str)
		self.send_and_block(hex_str)


	def cmd_pan_down(self, pan_speed=1, tilt_speed=0):
		logging.debug("cmd_pan_down()")
		hex_str = '81 01 06 01 %02x %02x 03 02 FF'%(pan_speed, tilt_speed)
		logging.debug(hex_str)
		self.send_and_block(hex_str)


	def cmd_pan_right(self, pan_speed=1, tilt_speed=0):
		logging.debug("cmd_pan_right()")
		hex_str = '81 01 06 01 %02x %02x 01 03 FF'%(pan_speed, tilt_speed)
		logging.debug(hex_str)
		self.send_and_block(hex_str)


	def cmd_pan_left(self, pan_speed=1, tilt_speed=0):
		logging.debug("cmd_pan_left()")
		hex_str = '81 01 06 01 %02x %02x 02 03 FF'%(pan_speed, tilt_speed)
		#logging.debug(hex_str)
		self.send_and_block(hex_str)
	"""


	def cmd_pt_pos(self, pan_angle, tilt_angle=0, pan_speed=0x14):
		'''
		Absolute positioning function
		'''
		logging.debug("cmd_pt_pos()")

		assert(abs(pan_angle) <= 180)
		assert(abs(tilt_angle) <= 180)

		pan_angle /= 2
		tilt_angle /=2

		def value_to_hexstr(angle):
			value = int(5120 / 180 * angle)

			value = min(value, 5120)
			value = max(value, -5120)

			value &= 0xffff

			hex_str = '%x' % value

			num_zero_pad = 4 - len(hex_str)

			hex_str = ('0' * num_zero_pad) + hex_str

			return hex_str

		pan_hex_str = value_to_hexstr(pan_angle)
		tilt_hex_str = value_to_hexstr(tilt_angle)


		hex_str = '81 01 06 02 %02x %02x %s %s FF'%(
			pan_speed,
			pan_speed,
			' '.join(['0' + v for v in pan_hex_str]),
			' '.join(['0' + v for v in tilt_hex_str]),
		)

		#hex_str = '81 01 06 03 01 00 01 01 01 01 01 01 01 01 01 FF'
		#self.send_hex_str(hex_str)
		self.send_and_block(hex_str)


	def cmd_power_on(self):
		hex_str = '81 01 04 00 02 FF'
		self.send_and_block(hex_str)


	def cmd_power_off(self):
		hex_str = '81 01 04 00 03 FF'
		self.send_and_block(hex_str)


	"""
	def cmd_zoom_stop(self):
		hex_str = '81 01 04 07 00 FF'
		self.send_and_block(hex_str)


	def cmd_zoom_tele_standard(self):
		hex_str = '81 01 04 07 02 FF'
		self.send_and_block(hex_str)


	def cmd_zoom_wide_standard(self):
		hex_str = '81 01 04 07 03 FF'
		self.send_and_block(hex_str)


	def cmd_zoom_tele_variable(self, value):
		'''
		Focus into the subject. Must call cmd_zoom_stop()
		To stop zooming
		'''
		assert(0 <= value);
		assert(value <= 7)
		hex_str = f'81 01 04 07 2{value} FF'
		self.send_and_block(hex_str)


	def cmd_zoom_wide_variable(self, value):
		'''
		Focus out of a subject. Must call cmd_zoom_stop()
		To stop zooming
		'''
		assert(0 <= value);
		assert(value <= 7)
		hex_str = f'81 01 04 07 3{value} FF'
		self.send_and_block(hex_str)

	def cmd_focus_stop(self):
		hex_str = '81 01 04 08 00 FF'
		self.send_and_block(hex_str)

	def cmd_focus_far(self):
		hex_str = '81 01 04 08 02 FF'
		self.send_and_block(hex_str)

	def cmd_focus_near(self):
		hex_str = '81 01 04 08 03 FF'
		self.send_and_block(hex_str)
	"""


	def cmd_zoom_position(self, position):
		'''
		Try these commands to test zooming

		cmd_zoom_position(0x100)
		cmd_zoom_position(0x200)
		cmd_zoom_position(0x300)
		cmd_zoom_position(0x400)
		...
		seems to max out at about 0x3000...
		'''
		pval = hex_alphanum(position, 3)
		qval = hex_alphanum(position, 2)
		rval = hex_alphanum(position, 1)
		sval = hex_alphanum(position, 0)
		#print("cmd_zoom_position()")

		hex_str = f'81 01 04 47 0{pval} 0{qval} 0{rval} 0{sval} FF'
		#print(hex_str)
		self.send_and_block(hex_str)


	def inquiry_zoom_position(self):
		hex_str = f'81 09 04 47 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type=RSP_TYPE_INQUIRY,
		)

		data = rsp['data']

		pval = data[0] & 0x0f
		qval = data[1] & 0x0f
		rval = data[2] & 0x0f
		sval = data[3] & 0x0f

		zoom_position = 0
		zoom_position |= pval << (3 * 4)
		zoom_position |= qval << (2 * 4)
		zoom_position |= rval << (1 * 4)
		zoom_position |= sval << (0 * 4)
		return zoom_position



	def cmd_focus_position(self, position):
		'''
		position ranges from:
		0x0000 to
		0x4000

		Note, you must call cmd_focus_manual()!
		Or the camera will ignore commands

		This command can take a long time if the current
		focus position if FAR away from the requested one
		'''
		min_zoom_pos = 0x0000
		max_zoom_pos = 0x4000

		assert(min_zoom_pos <= position)
		assert(position <= max_zoom_pos)
		#print("cmd_focus_position()")

		pval = hex_alphanum(position, 3)
		qval = hex_alphanum(position, 2)
		rval = hex_alphanum(position, 1)
		sval = hex_alphanum(position, 0)
		hex_str = f'81 01 04 48 0{pval} 0{qval} 0{rval} 0{sval} FF'
		#print(hex_str)
		self.send_and_block(hex_str)



	def cmd_focus_manual(self):
		hex_str = '81 01 04 38 03 FF'
		self.send_and_block(hex_str)


	def cmd_focus_auto(self):
		hex_str = '81 01 04 38 02 FF'
		self.send_and_block(hex_str)


	def inquiry_is_autofocus(self):
		hex_str = f'81 09 04 38 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type=RSP_TYPE_INQUIRY,
		)

		data = rsp['data']

		if data[0] == 0x02:
			return True
		elif data[0] == 0x03:
			return False
		else:
			assert(False)


	def inquiry_focus_position(self):
		hex_str = f'81 09 04 48 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type=RSP_TYPE_INQUIRY,
		)

		data = rsp['data']
		
		pval = data[0] & 0x0f
		qval = data[1] & 0x0f
		rval = data[2] & 0x0f
		sval = data[3] & 0x0f

		focus_position = 0
		focus_position |= pval << (3 * 4)
		focus_position |= qval << (2 * 4)
		focus_position |= rval << (1 * 4)
		focus_position |= sval << (0 * 4)
		return focus_position


	'''
	def cmd_set_red_gain(self, red):
		p = hex_alphanum(red, 1)
		q = hex_alphanum(red, 0)

		hex_str = f'81 01 04 43 00 00 0{p} 0{q} FF'
		self.send_and_block(hex_str)
	'''


	'''
	def cmd_set_blue_gain(self, blue):
		p = hex_alphanum(blue, 1)
		q = hex_alphanum(blue, 0)

		hex_str = f'81 01 04 44 00 00 0{p} 0{q} FF'
		self.send_and_block(hex_str)
	'''


	def cmd_set_exposure_mode(self, exposure_mode):
		mode2int = {
			ExposureMode.AUTO  : '00',
			ExposureMode.MANUAL: '03',
			ExposureMode.SHUTTER_PRIORITY: '0A',
			ExposureMode.IRIS_PRIORITY: '0B',
			ExposureMode.BRIGHT: '0D',

		}
		hex_str = f'81 01 04 39 {mode2int[exposure_mode]} FF'
		self.send_and_block(hex_str)

	


	def inquiry_auto_exposure_mode(self):
		hex_str = f'81 09 04 39 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type=RSP_TYPE_INQUIRY,
		)

		auto_exposure_mode_map = {
			0x00: ExposureMode.AUTO,
			0x03: ExposureMode.MANUAL,
			0x0A: ExposureMode.SHUTTER_PRIORITY,
			0x0B: ExposureMode.IRIS_PRIORITY,
			0x0D: ExposureMode.BRIGHT,
		}

		return auto_exposure_mode_map[rsp['data'][0]]




	def inquiry_picture_settings(self):
		hex_str = f'81 09 7E 7E 01 FF'
		responses = self.send_and_block(
			hex_str,
			wait_for=RSP_TYPE_INQUIRY,
		)

		rsp = VISCAInterface.filter_responses(
			responses,
			rsp_type=RSP_TYPE_INQUIRY,
		)

		data = rsp['data']

		red_gain  = ((data[0] & 0x0f) << 4) | (data[1] & 0x0f)
		blue_gain = ((data[2] & 0x0f) << 4) | (data[3] & 0x0f)
		wb_mode   = (data[4] & 0x0f)
		aperature = (data[5] & 0x0f)
		auto_exp_mode = data[6]
		shutter_pos = data[8]
		iris_pos = data[9]
		assert(0 == data[10])
		bright_pos = data[11]

		'''
		print('red gain:', red_gain)
		print('blue gain:', blue_gain)
		print('wb mode:', wb_mode)
		print('aperature:', aperature)
		print('auto exp mode:', auto_exp_mode)
		print('shutter pos:', shutter_pos)
		print('iris pos:', iris_pos)
		print('bright pos:', bright_pos)
		'''

		return {
			'red_gain': red_gain,
			'blue_gain': blue_gain,
			'wb_mode': wb_mode,
			'aperature': aperature,
			'auto_exp_mode': auto_exp_mode,
			'shutter_pos': shutter_pos,
			'iris_pos': iris_pos,
			'bright_pos': bright_pos,
		}


	def init(self):
		self.cmd_address_set()
		self.cmd_if_clear()
		self.cmd_pt_reset()
		self.cmd_set_exposure_mode(ExposureMode.AUTO)
		self.cmd_focus_auto()
		info = self.inquiry_camera_version()
		logging.debug(f'Firmware Info:')
		logging.debug(f"vendor id: {info['vendor_id_str']}")
		logging.debug(f"model  id: {info['model_id_str']}")
		logging.debug(f"rom versi: {info['rom_version_str']}")
		self.cmd_home()





if __name__ == '__main__':


	# you can run 'python -m serial.tools.list_ports -v'
	# to list serial ports and usb vendor and product ids

	cam = VISCAInterface(
		usb_to_tty(
			vid=0x0403,
			pid=0x6001,
		)
	)

	print('Begin...')

	cam.cmd_address_set()

	cam.cmd_if_clear()

	cam.cmd_pt_reset()

	cam.inquiry_camera_version()

	cam.cmd_home()

	time.sleep(2)

	cam.cmd_pan_left(pan_speed=0x10)

	while True:
		time.sleep(1)
		pan_pos, tilt_pos = cam.inquiry_position()

		print(f'pan: {pan_pos} tilt: {tilt_pos}')

		if abs(pan_pos) > 85:
			break

	input('press enter to position using absolute function')

	cam.cmd_pt_pos(0, 0)

	pdb.set_trace()
