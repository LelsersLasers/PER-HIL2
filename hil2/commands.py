from typing import Optional

import serial


READ_ID    = 0  # command                    -> id
WRITE_GPIO = 1  # command, pin, value        -> []
READ_GPIO  = 2  # command, pin               -> value
WRITE_DAC  = 3  # command, pin/offset, value -> []
HIZ_DAC    = 4  # command, pin/offset        -> []
READ_ADC   = 5  # command, pin               -> value high, value low
WRITE_POT  = 6  # command, pin/offset, value -> []


def read_id(serial_con: serial.Serial) -> Optional[int]:
	command = [READ_ID]
	serial_con.write(bytearray(command))
	read_hil_id_raw = serial_con.read(1)
	if len(read_hil_id_raw) != 1:
		None
	return int.from_bytes(read_hil_id_raw, "big")

def write_gpio(self, serial_con: serial.Serial, pin: int, value: bool) -> None:
	command = [WRITE_GPIO, pin, int(value)]
	serial_con.write(bytearray(command))

def read_gpio(serial_con: serial.Serial, pin: int) -> bool:
	command = [READ_GPIO, pin]
	serial_con.write(bytearray(command))
	read_value_raw = serial_con.read(1)
	if len(read_value_raw) != 1:
		raise ValueError("Failed to read GPIO value, expected 1 byte")
	return bool(int.from_bytes(read_value_raw, "big"))

def write_dac(serial_con: serial.Serial, pin: int, raw_value: int) -> None:
	command = [WRITE_DAC, pin, raw_value]
	serial_con.write(bytearray(command))

def hiZ_dac(serial_con: serial.Serial, pin: int) -> None:
	command = [HIZ_DAC, pin]
	serial_con.write(bytearray(command))

def read_adc(serial_con: serial.Serial, pin: int) -> int:
	command = [READ_ADC, pin]
	serial_con.write(bytearray(command))
	read_value_raw = serial_con.read(2)
	if len(read_value_raw) != 2:
		raise ValueError("Failed to read ADC value, expected 2 bytes")
	return int.from_bytes(read_value_raw, "big")

def write_pot(serial_con: serial.Serial, pin: int, raw_value: int) -> None:
	command = [WRITE_POT, pin, raw_value]
	serial_con.write(bytearray(command))