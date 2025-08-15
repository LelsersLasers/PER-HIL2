from typing import Optional

import cantools.database.can.database as cantools_db

import can_helper
import hil_errors
import serial_helper


READ_ID    = 0 # command                    -> READ_ID, id
WRITE_GPIO = 1 # command, pin, value        -> []
READ_GPIO  = 2 # command, pin               -> READ_GPIO, value
WRITE_DAC  = 3 # command, pin/offset, value -> []
HIZ_DAC    = 4 # command, pin/offset        -> []
READ_ADC   = 5 # command, pin               -> READ_ADC, value high, value low
WRITE_POT  = 6 # command, pin/offset, value -> []
SEND_CAN   = 7 # command, bus, signal high, signal low, length, data (8 bytes) -> []
RECV_CAN   = 8 # <async>                    -> CAN_MESSAGE, bus, signal high,
               #                               signal low, length, data (length bytes)
ERROR      = 9 # <async/any>                -> ERROR, command

SERIAL_RESPONSES = [READ_ID, READ_GPIO, READ_ADC, RECV_CAN, ERROR]


def read_id(ser: serial_helper.ThreadedSerial) -> Optional[int]:
    command = [READ_ID]
    ser.write(bytearray(command))
    match ser.get_readings_with_timeout(READ_ID):
        case None:
            return None
        case [read_hil_id]:
            return read_hil_id
        case _:
            raise hil_errors.EngineError("Failed to read HIL ID, expected 1 byte")

def write_gpio(ser: serial_helper.ThreadedSerial, pin: int, value: bool) -> None:
    command = [WRITE_GPIO, pin, int(value)]
    ser.write(bytearray(command))

def read_gpio(ser: serial_helper.ThreadedSerial, pin: int) -> bool:
    command = [READ_GPIO, pin]
    ser.write(bytearray(command))
    match ser.get_readings_with_timeout(READ_GPIO):
        case None:
            raise hil_errors.SerialError("Failed to read GPIO value, no response")
        case [read_value]:
            return bool(read_value)
        case _:
            raise hil_errors.EngineError("Failed to read GPIO value, expected 1 byte")

def write_dac(ser: serial_helper.ThreadedSerial, pin: int, raw_value: int) -> None:
    command = [WRITE_DAC, pin, raw_value]
    ser.write(bytearray(command))

def hiZ_dac(ser: serial_helper.ThreadedSerial, pin: int) -> None:
    command = [HIZ_DAC, pin]
    ser.write(bytearray(command))

def read_adc(ser: serial_helper.ThreadedSerial, pin: int) -> int:
    command = [READ_ADC, pin]
    ser.write(bytearray(command))
    match ser.get_readings_with_timeout(READ_ADC):
        case None:
            raise hil_errors.SerialError("Failed to read ADC value, no response")
        case [read_value_high, read_value_low]:
            return (read_value_high << 8) | read_value_low
        case _:
            raise hil_errors.EngineError("Failed to read ADC value, expected 2 bytes")

def write_pot(ser: serial_helper.ThreadedSerial, pin: int, raw_value: int) -> None:
    command = [WRITE_POT, pin, raw_value]
    ser.write(bytearray(command))

def send_can(
    ser: serial_helper.ThreadedSerial, bus: int, signal: int, data: list[int],
) -> None:
    signal_high = (signal >> 8) & 0xFF
    signal_low = signal & 0xFF
    length = len(data)
    padding = [0] * (8 - len(data))
    command = [SEND_CAN, bus, signal_high, signal_low, length, *data, *padding]
    ser.write(bytearray(command))


def parse_can_messages(
    ser: serial_helper.ThreadedSerial,
    bus: int, can_dbc: cantools_db.Database
) -> list[can_helper.CanMessage]:
    return [
        can_helper.CanMessage(
            signal=signal,
            data=can_dbc.decode_message(signal, data)
        )
        for values in ser.get_parsed_can_messages(bus)
        for signal, data in [((values[1] << 8) | values[2], values[4:4 + values[3]])]
    ]


def parse_readings(
    readings: list[int],
    parsed_readings: dict[int, list[int]],
    parsed_can_messages: dict[int, list[list[int]]]
) -> tuple[bool, list[int]]:
    match readings:
        case []:
            return False, []
        case [READ_ID, value, *rest]:
            parsed_readings[READ_ID] = [value]
            return True, rest
        case [READ_GPIO, value, *rest]:
            parsed_readings[READ_GPIO] = [value]
            return True, rest
        case [READ_ADC, value_high, value_low, *rest]:
            parsed_readings[READ_ADC] = [value_high, value_low]
            return True, rest
        case [
            RECV_CAN, bus, signal_high, signal_low, length, *rest
        ] if len(rest) >= length:
            data, remaining = rest[:length], rest[length:]
            if bus not in parsed_can_messages:
                parsed_can_messages[bus] = []
            parsed_can_messages[bus].append([
                bus, signal_high, signal_low, length, *data
            ])
            return True, remaining
        case [ERROR, command, *rest]:
            raise hil_errors.SerialError(f"HIL reported error for command {command}")
        case [first, *rest] if first not in SERIAL_RESPONSES:
            raise hil_errors.SerialError(f"Unexpected response {first}")
        case _:
            return False, readings