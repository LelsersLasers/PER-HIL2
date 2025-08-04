import time

import serial
import serial.tools.list_ports

class SerialManager:
	def __init__(self, devices: dict[int, serial.Serial]):
		self.devices: dict[int, serial.Serial] = devices

	@classmethod
	def from_discovery(cls, hil_ids: list[int]) -> 'SerialManager':
		devices = {}

		com_ports = [
			port.device for port in serial.tools.list_ports.comports()
			if "USB Serial" in port.description
		]

		for cp in com_ports:
			serial_con = serial.Serial(
				cp,
				115200,
				timeout=0.1,
				bytesize=serial.EIGHTBITS,
				parity=serial.PARITY_NONE,
				stopbits=serial.STOPBITS_ONE,
				xonxoff=0,
				rtscts=0
			)
			serial_con.setDTR(False)
			time.sleep(1)
			serial_con.flushInput()
			serial_con.setDTR(True)
			
			for _ in range(5):
				# 4 = HIL_CMD_READ_ID
				serial_con.write(b'\x04')
				read_hil_id_raw = serial_con.read(1)
				
				if len(read_hil_id_raw) == 1:
					read_hil_id = int.from_bytes(read_hil_id_raw, "big")
					if read_hil_id in hil_ids:
						devices[read_hil_id] = serial_con
						print(f"Discovered HIL device with ID {read_hil_id} on port {cp}")
						break
				time.sleep(1)
			else:
				serial_con.close()

		for hil_id in hil_ids:
			if hil_id not in devices:
				raise ValueError(f"Failed to discover HIL device with ID {hil_id} on any port")
		
		return cls(devices)