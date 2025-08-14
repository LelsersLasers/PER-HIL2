from typing import Optional

import threading
import time

import serial
import serial.tools.list_ports

import commands


def discover_devices(hil_ids: list[int]) -> dict[int, serial.Serial]:
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
			read_hil_id = commands.read_id(serial_con)
			if read_hil_id is not None and read_hil_id in hil_ids:
				devices[read_hil_id] = serial_con
				print(f"Discovered HIL device with ID {read_hil_id} on port {cp}")
				break
			time.sleep(1)
		else:
			serial_con.close()

	for hil_id in hil_ids:
		if hil_id not in devices:
			raise ValueError(f"Failed to discover HIL device with ID {hil_id} on any port")
	
	return devices

class ThreadedSerial:
	def __init__(self, serial_con: serial.Serial, stop_event: threading.Event):
		self.serial_con: serial.Serial = serial_con
		self.stop_event: threading.Event = stop_event
		self.readings: list[int] = []
		self.parsed_readings: dict[int, list[int]] = {}
		self.parsed_can_messages: dict[int, list[list[int]]] = {}
		self.lock = threading.Lock()

	def write(self, data: bytes) -> None:
		self.serial_con.write(data)

	def _read(self):
		read_data = self.serial_con.read(1)
		if len(read_data) < 1:
			return
		value = int.from_bytes(read_data, "big")
		self.readings.append(value)

	def _process_readings(self):
		processed = True
		while processed:
			processed, self.readings = commands.parse_readings(self.readings, self.parsed_readings, self.parsed_can_messages)

	def _get_readings(self, command: int) -> Optional[list[int]]:
		with self.lock:
			val = self.parsed_readings.pop(command, None)
			return val
		
	def get_readings_with_timeout(self, command: int, timeout: float = 0.1, sleep_interval = 0.01) -> Optional[list[int]]:
		deadline = time.time() + timeout
		while time.time() < deadline:
			if (reading := self._get_readings(command)) is not None:
				return reading
			time.sleep(sleep_interval)
		return None
	
	def get_parsed_can_messages(self, bus: int) -> list[list[int]]:
		with self.lock:
			return self.parsed_can_messages.pop(bus, [])
		
	def stop(self):
		self.stop_event.set()

	def _close(self):
		self.serial_con.close()
	
	def run(self):
		while not self.stop_event.is_set():
			self._read()
			if len(self.readings) > 0:
				with self.lock:
					self._process_readings()

		self._close()