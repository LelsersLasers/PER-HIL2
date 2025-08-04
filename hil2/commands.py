READ_ID = 0    # command                    -> maybe id
WRITE_GPIO = 1 # command, pin, value        -> []
READ_GPIO = 2  # command, pin               -> value
WRITE_DAC = 3  # command, pin/offset, value -> []
READ_ADC = 4   # command, pin               -> value high, value low
WRITE_POT = 5  # command, pin/offset, value -> []

def read_id(serial_con: serial.Serial) -> Optional[int]:
	command = [READ_ID]
	serial_con.write(bytearray(command))
	read_hil_id_raw = serial_con.read(1)
	if len(read_hil_id_raw) != 1:
		None
	return int.from_bytes(read_hil_id_raw, "big")

