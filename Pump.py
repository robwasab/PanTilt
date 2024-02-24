from smbus2 import SMBus, i2c_msg
from PowerSwitch import PowerSwitch
import subprocess
import time
import pdb

NUM_TRIES = 16

PUMP_ADDR_0 = 0x38
PUMP_ADDR_1 = 0x39
PUMP_ADDR_2 = 0x3A

color2addr = {
   'orange': PUMP_ADDR_0,
   'white' : PUMP_ADDR_1,
   'yellow': PUMP_ADDR_2,
}


class Pump(object):

	def startDispense(self, color):
		'''
		addr = '%02x'%color2addr[color]
		cmd = f'i2cset -y 1 0x{addr} 0x44 0x2c 0x2a i'
		subprocess.call(cmd, shell=True)
		'''
		with SMBus(1) as bus:
			msg = i2c_msg.write(
				color2addr[color], 
				bytes(
					f'D,*', 
					'utf8'
				),
			)
			bus.i2c_rdwr(msg)


	def dispense_ml(self, color, ml):
		with SMBus(1) as bus:
			msg = i2c_msg.write(
				color2addr[color], 
				bytes(
					f'D,{ml}',
					'utf8',
				),
			)
			bus.i2c_rdwr(msg)


	def dispenseStatus(self, color):
		with SMBus(1) as bus:

			for k in range(NUM_TRIES):
				#if 0 < k:
				#	print('Retry: ', k)

				bus.i2c_rdwr(
					i2c_msg.write(
						color2addr[color], 
						bytes(
							'D,?',
							'utf8',
						),
					)
				)

				time.sleep(0.5)

				read_msg = i2c_msg.read(
					color2addr[color],
					16
				)

				bus.i2c_rdwr(read_msg)

				read_bytes = bytes(read_msg)

				try:
					#print(read_bytes)

					# find the null terminator
					index = read_bytes.find(0x00)

					if index < len(read_bytes):
						# truncate
						read_bytes = read_bytes[:index]
						#print('truncated: ', read_bytes)

					prefix = bytes([0x01, ord('?'), ord('D'), ord(',')])

					if not read_bytes.startswith(prefix):
						time.sleep(.1)
						continue
					else:
					
						rsp = str(
							read_bytes.removeprefix(prefix),
							'utf8',
						)

						req_amt, pump_active = rsp.split(',')

						return {
							'req_ml': req_amt,
							'pump_status': pump_active,
							'pump_on': True if '1' == pump_active else False,
						}

				except UnicodeDecodeError:
					print('unicode decode error')
					time.sleep(.1)
					continue

		# couldn't read from pump
		raise IOError('Could not read from pump')


	def stopDispense(self, color):
		'''
		addr = color2addr[color]
		addr = '%02x'%color2addr[color]
		cmd = f'i2cset -y 1 0x{addr} 0x78'
		subprocess.call(cmd, shell=True)
		'''
		with SMBus(1) as bus:
			msg = i2c_msg.write(
				color2addr[color], 
				bytes(
					f'x',
					'utf8',
				),
			)
			bus.i2c_rdwr(msg)




if __name__ == '__main__':
	from smbus2 import SMBus, i2c_msg

	pump = Pump()

	#pump.startDispense('white')
	pump.stopDispense('white')

	time.sleep(1)

	pump.dispense_ml('white', 30)
	pump.dispense_ml('orange', 50)


	for _ in range(100):
		white_status = pump.dispenseStatus('white')
		orange_status = pump.dispenseStatus('orange')

		print(white_status)
		print(orange_status)

		if white_status['pump_on'] or orange_status['pump_on']:
			continue
		else:
			break






'''

if __name__ == '__main__':
   import time
   pwr = PowerSwitch()
   pwr.setPumpPower(True)
   time.sleep(.1)

   pump = Pump()

   pump.startDispense('white')

   pdb.set_trace()
'''
