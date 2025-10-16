from typing import Optional

import time
import logging

import cantools.database.can.database as cantools_db
import serial

from . import can_helper
from . import hil_errors
from . import serial_helper


# Command constants -------------------------------------------------------------------#
# fmt: off
READ_ID    = 0  # command                    -> SYNC_BYTES (4), READ_ID, id
WRITE_GPIO = 1  # command, pin, value        -> []
HIZ_GPIO   = 2  # command, pin               -> []
READ_GPIO  = 3  # command, pin               -> READ_GPIO, value
WRITE_DAC  = 4  # command, pin/offset, value -> []
HIZ_DAC    = 5  # command, pin/offset        -> []
READ_ADC   = 6  # command, pin               -> READ_ADC, value high, value low
WRITE_POT  = 7  # command, pin/offset, value -> []
SEND_CAN   = 8  # command, bus, signal bytes: 3-0, length, data (8 bytes) -> []
RECV_CAN   = 9  # <async>                    -> RECV_CAN, bus, signal bytes: 3-0,
                #                               length, data (length bytes)
ERROR      = 10 # <async/any>                -> ERROR, command
# fmt: on

READ_ID_RESPONSE_LENGTH = 6  # SYNC_BYTES (4) + READ_ID (1) + ID (1)
SYNC_BYTES = [0xDE, 0xAD, 0xBE, 0xEF]

SERIAL_RESPONSES = [READ_ID, READ_GPIO, READ_ADC, RECV_CAN, ERROR]


# Simple commands ---------------------------------------------------------------------#
def read_id(
    ser_raw: serial.Serial, response_wait: float
) -> Optional[tuple[int, list[int]]]:
    """
    Attempts to connect and read the HIL ID from a device.
    Sends a READ_ID command and waits for a response.

    :param ser_raw: The raw serial connection to use (raw Serial object).
    :return: The HIL ID and any bytes received after the ID, or None if not a HIL device.
    """
    command = [READ_ID]
    logging.debug(f"Sending - READ_ID: {command}")
    ser_raw.reset_input_buffer()
    ser_raw.write(bytearray(command))
    read_buffer = []

    try:
        start_time = time.time()

        while time.time() - start_time < response_wait:
            to_read = max(ser_raw.in_waiting, 1)
            chunk = ser_raw.read(to_read)
            if not chunk:
                continue
            read_buffer.extend([int(b) for b in chunk])

            if len(read_buffer) >= READ_ID_RESPONSE_LENGTH:
                # Look for SYNC_BYTES in the buffer
                for i in range(len(read_buffer) - 5):
                    if read_buffer[i : i + 4] == SYNC_BYTES:
                        logging.debug(f"SYNC_BYTES found at position {i}")
                        # Check if the next byte is READ_ID
                        if read_buffer[i + 4] == READ_ID:
                            read_hil_id = read_buffer[i + 5]
                            remaining_bytes = read_buffer[i + 6 :]
                            logging.debug(
                                f"Received - READ_ID: {read_hil_id},"
                                f"remaining bytes: {len(remaining_bytes)}"
                            )
                            return read_hil_id, remaining_bytes
                # If SYNC_BYTES not found, remove bytes before the last 3 bytes
                read_buffer = read_buffer[-3:]

    except serial.SerialException as e:
        logging.error(f"Serial exception occurred: {e}")
        return None


def write_gpio(ser: serial_helper.ThreadedSerial, pin: int, value: bool) -> None:
    """
    Writes a GPIO value to a device.
    Sends a WRITE_GPIO command with the specified pin and value.

    :param ser: The serial connection to use.
    :param pin: The GPIO pin number.
    :param value: The value to write (low = false, high = true).
    """
    command = [WRITE_GPIO, pin, int(value)]
    logging.debug(f"Sending - WRITE_GPIO: {command}")
    ser.write(bytearray(command))


def hiZ_gpio(ser: serial_helper.ThreadedSerial, pin: int) -> None:
    """
    Set a GPIO pin to high impedance (HiZ).
    (This is equivalent to setting the pin as an input.)
    Sends a HIZ_GPIO command with the specified pin.

    :param ser: The serial connection to use.
    :param pin: The GPIO pin number.
    """
    command = [HIZ_GPIO, pin]
    logging.debug(f"Sending - HIZ_GPIO: {command}")
    ser.write(bytearray(command))


def read_gpio(ser: serial_helper.ThreadedSerial, pin: int) -> bool:
    """
    Reads a GPIO value from a device.
    Sends a READ_GPIO command with the specified pin and waits for a response.

    :param ser: The serial connection to use.
    :param pin: The GPIO pin number.
    :return: The value read from the GPIO pin (low = false, high = true).
    """

    command = [READ_GPIO, pin]
    logging.debug(f"Sending - READ_GPIO: {command}")
    ser.write(bytearray(command))
    match ser.get_readings_with_timeout(READ_GPIO):
        case None:
            raise hil_errors.SerialError("Failed to read GPIO value, no response")
        case [read_value]:
            logging.debug(f"Received - READ_GPIO: {read_value}")
            return bool(read_value)
        case x:
            error_msg = f"Failed to read GPIO value, expected 1 byte: {x}"
            raise hil_errors.EngineError(error_msg)


def write_dac(ser: serial_helper.ThreadedSerial, pin: int, raw_value: int) -> None:
    """
    Writes a DAC value to a device.
    Sends a WRITE_DAC command with the specified pin and raw value.

    :param ser: The serial connection to use.
    :param pin: The DAC pin number.
    :param raw_value: The raw value to write (0-255).
    """
    command = [WRITE_DAC, pin, raw_value]
    logging.debug(f"Sending - WRITE_DAC: {command}")
    ser.write(bytearray(command))


def hiZ_dac(ser: serial_helper.ThreadedSerial, pin: int) -> None:
    """
    Sets a DAC pin to high impedance mode.
    Sends a HIZ_DAC command with the specified pin.

    :param ser: The serial connection to use.
    :param pin: The DAC pin number.
    """
    command = [HIZ_DAC, pin]
    logging.debug(f"Sending - HIZ_DAC: {command}")
    ser.write(bytearray(command))


def read_adc(ser: serial_helper.ThreadedSerial, pin: int) -> int:
    """
    Reads an ADC value from a device.
    Sends a READ_ADC command with the specified pin and waits for a response.

    :param ser: The serial connection to use.
    :param pin: The ADC pin number.
    :return: The raw ADC value read from the specified pin.
    """

    command = [READ_ADC, pin]
    logging.debug(f"Sending - READ_ADC: {command}")
    ser.write(bytearray(command))
    match ser.get_readings_with_timeout(READ_ADC):
        case None:
            raise hil_errors.SerialError("Failed to read ADC value, no response")
        case [read_value_high, read_value_low]:
            logging.debug(f"Received - READ_ADC: {read_value_high}, {read_value_low}")
            return (read_value_high << 8) | read_value_low
        case x:
            error_msg = f"Failed to read ADC value, expected 2 bytes: {x}"
            raise hil_errors.EngineError(error_msg)


def write_pot(ser: serial_helper.ThreadedSerial, pin: int, raw_value: int) -> None:
    """
    Writes a potentiometer value to a device.
    Sends a WRITE_POT command with the specified pin and raw value.

    :param ser: The serial connection to use.
    :param pin: The potentiometer pin number.
    :param raw_value: The raw value to write (0-255).
    """
    command = [WRITE_POT, pin, raw_value]
    logging.debug(f"Sending - WRITE_POT: {command}")
    ser.write(bytearray(command))


# CAN commands/parsing ----------------------------------------------------------------#
def send_can(
    ser: serial_helper.ThreadedSerial,
    bus: int,
    signal: int,
    data: list[int],
) -> None:
    """
    Sends a CAN message over the specified bus.

    :param ser: The serial connection to use.
    :param bus: The CAN bus number.
    :param signal: The CAN signal ID.
    :param data: The data to send (up to 8 bytes). When sent, will be padded with zeros.
    """
    signal_3 = (signal >> 24) & 0xFF
    signal_2 = (signal >> 16) & 0xFF
    signal_1 = (signal >> 8) & 0xFF
    signal_0 = signal & 0xFF
    length = len(data)
    padding = [0] * (8 - len(data))
    command = [
        SEND_CAN,
        bus,
        signal_3,
        signal_2,
        signal_1,
        signal_0,
        length,
        *data,
        *padding,
    ]
    logging.debug(f"Sending - SEND_CAN: {command}")
    print(f"Sending - SEND_CAN: {command}")
    ser.write(bytearray(command))


def parse_can_messages(
    ser: serial_helper.ThreadedSerial, bus: int, can_dbc: cantools_db.Database
) -> list[can_helper.CanMessage]:
    """
    Parses received CAN messages from the serial connection for the specified bus.

    :param ser: The serial connection to use.
    :param bus: The CAN bus number.
    :param can_dbc: The DBC database to use for decoding messages.
    :return: A list of parsed CAN messages.
    """

    def decode(values):
        signal = (
            (values[1] << 24) | (values[2] << 16) | (values[3] << 8) | values[4]
        ) & 0x1FFFFFFF
        data = bytes(values[6 : 6 + values[5]])
        try:
            decoded = can_dbc.decode_message(signal, data)
            return can_helper.CanMessage(signal, decoded)
        except Exception as e:
            logging.error(f"Failed to decode CAN message with ID {signal} ({e})")
            return None

    return [
        msg
        for values in ser.get_parsed_can_messages(bus)
        if (msg := decode(values)) is not None
    ]


# Serial parsing/spliting -------------------------------------------------------------#
def parse_readings(
    readings: list[int],
    parsed_readings: dict[int, list[int]],
    parsed_can_messages: dict[int, list[list[int]]],
) -> tuple[bool, list[int]]:
    """
    Parse the first serial reading if possible.
    Does not do conversion, just separates and saves the raw bytes for the corresponding
    reading.

    :param readings: The entire list of readings (bytes received from serial) to parse
    :param parsed_readings: The dictionary to store parsed readings.
    :param parsed_can_messages: The dictionary to store parsed CAN messages.
    :return: A tuple:
             - A boolean indicating if anything was parsed (and maybe this function
               should be called again)
             - The remaining unparsed readings.
    """

    logging.debug(f"Current readings to parse: {readings}")
    match readings:
        case []:
            return False, []
        case [cmd, value, *rest] if cmd == READ_ID:
            logging.debug(f"Parsed - READ_ID: {value}")
            parsed_readings[READ_ID] = [value]
            return True, rest
        case [cmd, value, *rest] if cmd == READ_GPIO:
            logging.debug(f"Parsed - READ_GPIO: {value}")
            parsed_readings[READ_GPIO] = [value]
            return True, rest
        case [cmd, value_high, value_low, *rest] if cmd == READ_ADC:
            logging.debug(f"Parsed - READ_ADC: {value_high}, {value_low}")
            parsed_readings[READ_ADC] = [value_high, value_low]
            return True, rest
        case [cmd, bus, signal_3, signal_2, signal_1, signal_0, length, *rest] if (
            cmd == RECV_CAN and len(rest) >= length
        ):
            logging.debug(
                f"Parsed - RECV_CAN: {bus}, {signal_3}, {signal_2}, {signal_1}, "
                + f"{signal_0}, {length}, {rest[:length]}"
            )
            data, remaining = rest[:length], rest[length:]
            if bus not in parsed_can_messages:
                parsed_can_messages[bus] = []
            parsed_can_messages[bus].append(
                [bus, signal_3, signal_2, signal_1, signal_0, length, *data]
            )
            return True, remaining
        case [cmd, command, *rest] if cmd == ERROR:
            logging.critical(f"Parsed - ERROR for command: {command}. Rest={rest}")
            raise hil_errors.SerialError(f"HIL reported error for command {command}")
        case [first, *rest] if first not in SERIAL_RESPONSES:
            logging.critical(f"Unexpected response: {first}. Rest={rest}")
            raise hil_errors.SerialError(f"Unexpected response. Command error: {first}")
        case _:
            return False, readings
