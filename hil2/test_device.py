from typing import Any, Optional

import json
import threading

import cantools.database.can.database as cantools_db

import can_helper
import dut_cons
import action
import commands
import serial_helper


class AdcConfig:
	def __init__(self, adc_config: dict):
		self.bit_resolution: int = adc_config.get("bit_resolution")
		self.adc_reference_v: float = adc_config.get("adc_reference_v")
		self.five_v_reference_v: float = adc_config.get("5v_reference_v")
		self.twenty_four_v_reference_v: float = adc_config.get("24v_reference_v")

	def raw_to_v(self, raw_value: int) -> float:
		return (raw_value / (2 ** self.bit_resolution - 1)) * self.adc_reference_v

	def raw_to_5v(self, raw_value: int) -> float:
		return (self.raw_to_v(raw_value) / self.five_v_reference_v) * 5.0
	
	def raw_to_24v(self, raw_value: int) -> float:
		return (self.raw_to_v(raw_value) / self.twenty_four_v_reference_v) * 24.0


class DacConfig:
	def __init__(self, dac_config: dict):
		self.bit_resolution: int = dac_config.get("bit_resolution")
		self.reference_v: float = dac_config.get("reference_v")

	def v_to_raw(self, value: float) -> int:
		return int((value / self.reference_v) * (2 ** self.bit_resolution - 1))


class PotConfig:
	def __init__(self, pot_config: dict):
		self.bit_resolution: int = pot_config.get("bit_resolution")
		self.reference_ohms: float = pot_config.get("reference_ohms")
		self.wiper_ohms: float = pot_config.get("wiper_ohms")

	def ohms_to_raw(self, value: float) -> int:
		steps = self.bit_resolution ** 2  - 1
		return int((steps * (value - self.wiper_ohms)) / self.reference_ohms)


class Port:
	def __init__(self, port: dict):
		self.name: str = port.get("name")
		self.port: int = port.get("port")
		self.mode: str = port.get("mode")


class Mux:
	def __init__(self, mux: dict):
		self.name: str = mux.get("name")
		self.mode: str = mux.get("mode")
		self.select_ports: list[int] = mux.get("select_ports")
		self.port: int = mux.get("port")

	def select_from_name(self, name: str) -> Optional['MuxSelect']:
		"""Note: returns None when the name does not match."""
		name_parts = name.rsplit('_', 1)
		if len(name_parts) < 2:
			return None
		if name_parts[0] != self.name:
			return None
		try:
			return MuxSelect(self, int(name_parts[1]))
		except ValueError:
			return None


class MuxSelect:
	def __init__(self, mux: Mux, select: int):
		self.mux: Mux = mux
		self.select: int = select


class CanBus:
	def __init__(self, can_bus: dict):
		self.name: str = can_bus.get("name")
		self.bus: int = can_bus.get("bus")


class TestDevice:
	def __init__(self,
		hil_id: int,
		name: str,
		ports: dict[str, Port],
		muxs: dict[str, Mux],
		can_busses: dict[str, CanBus],
		adc_config: AdcConfig,
		dac_config: DacConfig,
		pot_config: PotConfig,
		ser: serial_helper.ThreadedSerial
	):
		self.hil_id: int = hil_id
		self.name: str = name
		self.ports: dict[str, Port] = ports
		self.muxs: dict[str, Mux] = muxs
		self.can_busses: dict[str, CanBus] = can_busses
		self.adc_config: AdcConfig = adc_config
		self.dac_config: DacConfig = dac_config
		self.pot_config: PotConfig = pot_config
		self.ser: serial_helper.ThreadedSerial = ser

		self.device_can_busses: dict[str, can_helper.CanMessageManager] = dict(map(
			lambda c: (c.name, can_helper.CanMessageManager()),
			self.can_busses.values()
		))


	@classmethod
	def from_json(
		cls,
		hil_id: int,
		name: str,
		ser: serial_helper.ThreadedSerial,
		device_config_path: str
	):
		with open(device_config_path, 'r') as device_config_path:
			device_config = json.load(device_config_path)

		ports = dict(map(lambda p: (p.get("name"), Port(p)), device_config.get("ports")))
		muxs = dict(map(lambda m: (m.get("name"), Mux(m)), device_config.get("muxs")))
		can_busses = dict(map(lambda c: (c.get("name"), CanBus(c)), device_config.get("can")))
		
		adc_config = AdcConfig(device_config.get("adc_config"))
		dac_config = DacConfig(device_config.get("dac_config"))
		pot_config = PotConfig(device_config.get("pot_config"))

		return cls(
			hil_id,
			name,
			ports,
			muxs,
			can_busses,
			adc_config,
			dac_config,
			pot_config,
			ser
		)
	
	def close(self) -> None:
		# TODO: close all ports
		self.ser.stop()
	
	def select_mux(self, mux_select: MuxSelect) -> None:
		for i, p in enumerate(mux_select.mux.select_ports):
			select_bit = 1 if (mux_select.select & (1 << i)) else 0
			self.set_do(p, select_bit)
		self.set_ao(mux_select.mux.port, mux_select)
	
	def set_do(self, pin: int, value: bool) -> None:
		commands.write_gpio(self.ser, pin, value)

	def hiZ_do(self, pin: int) -> None:
		commands.read_gpio(self.ser, pin)

	def get_di(self, pin: int) -> bool:
		return commands.read_gpio(self.ser, pin)

	def set_ao(self, pin: int, value: float) -> None:
		raw_value = self.dac_config.v_to_raw(value)
		commands.write_dac(self.ser, pin, raw_value)
	
	def hiZ_ao(self, pin: int) -> None:
		commands.hiZ_dac(self.ser, pin)
	
	def get_ai(self, pin: int, mode: str) -> float:
		raw_value = commands.read_adc(self.ser, pin)
		if mode == 'AI5':
			return self.adc_config.raw_to_5v(raw_value)
		elif mode == 'AI24':
			return self.adc_config.raw_to_24v(raw_value)
		elif mode == 'AI':
			return self.adc_config.raw_to_v(raw_value)
		else:
			raise ValueError(f"Unsupported AI mode: {mode}")

	def set_pot(self, pin: int, value: float) -> None:
		raw_value = self.pot_config.ohms_to_raw(value)
		commands.write_pot(self.ser, pin, raw_value)

	def update_can_messages(self, bus: int, can_dbc: cantools_db.Database) -> None:
		self.device_can_busses[bus].add_multiple(
			commands.parse_can_messages(self.ser, bus, can_dbc)
		)

	def send_can(self, bus: int, signal: str | int, data: dict, can_dbc: cantools_db.Database) -> None:
		raw_data = list(can_dbc.encode_message(signal, data))
		msg_id = can_dbc.get_message_by_name(signal).frame_id
		commands.send_can(self.ser, bus, msg_id, raw_data)

	def do_action(self, action_type: action.ActionType, port: str) -> Any:
		maybe_port = self.ports.get(port, None)
		maybe_mux_select = next(
			(val for m in self.muxs.values() if (val := m.select_from_name(port)) is not None),
			None,
		)
		maybe_can_bus = self.can_busses.get(port, None)

		match (action_type, maybe_port, maybe_mux_select, maybe_can_bus):
			# Set DO + direct port
			case (action.SetDo(value), mp, _, _) if mp is not None and mp.mode == 'DO':
				self.set_do(mp.port, value)
			# Set DO + mux select
			case (action.SetDo(value), _, mms, _) if mms is not None and mms.mux.mode == 'DO':
				self.select_mux(mms)
				self.set_do(mms.mux.port, value)
			# HiZ DO + direct port
			case (action.HiZDo(), mp, _, _) if mp is not None and mp.mode == 'DO':
				self.hiZ_do(mp.port)
			# HiZ DO + mux select
			case (action.HiZDo(), _, mms, _) if mms is not None and mms.mux.mode == 'DO':
				self.select_mux(mms)
				self.hiZ_do(mms.mux.port)
			# Get DI + direct port
			case (action.GetDi(), mp, _, _) if mp is not None and mp.mode == 'DI':
				return self.get_di(mp.port)
			# Get DI + mux select
			case (action.GetDi(), _, mms, _) if mms is not None and mms.mux.mode == 'DI':
				self.select_mux(mms)
				return self.get_di(mms.mux.port)
			# Set AO + direct port
			case (action.SetAo(value), mp, _, _) if mp is not None and mp.mode == 'AO':
				self.set_ao(mp.port, value)
			# HiZ AO + direct port
			case (action.HiZAo(), mp, _, _) if mp is not None and mp.mode == 'AO':
				self.hiZ_ao(mp.port)
			# Get AI + direct port
			case (action.GetAi(), mp, _, _) if mp is not None and mp.mode.startswith('AI'):
				return self.get_ai(mp.port, mms.mux.mode)
			# Get AI + mux select
			case (action.GetAi(), _, mms, _) if mms is not None and mms.mux.mode.startswith('AI'):
				self.select_mux(mms)
				return self.get_ai(mms.mux.port, mms.mux.mode)
			# Set Pot + direct port
			case (action.SetPot(value), mp, _, _) if mp is not None and mp.mode == 'POT':
				self.set_pot(mp.port, value)
			# Send CAN msg + can bus name
			case (action.SendCan(signal, data, can_dbc), _, _, mcb) if mcb is not None:
				self.update_can_messages(mcb.bus, can_dbc)
				self.send_can(mcb.bus, signal, data, can_dbc)
			# Get last CAN msg + can bus name
			case (action.GetLastCan(signal, can_dbc), _, _, mcb) if mcb is not None:
				self.update_can_messages(mcb.bus, can_dbc)
				return self.device_can_busses[mcb.name].get_last(signal)
			# Get all CAN msgs + can bus name
			case (action.GetAllCan(signal, can_dbc), _, _, mcb) if mcb is not None:
				self.update_can_messages(mcb.bus, can_dbc)
				return self.device_can_busses[mcb.name].get_all(signal)
			# Clear CAN msgs + can bus name
			case (action.ClearCan(signal, can_dbc), _, _, mcb) if mcb is not None:
				self.update_can_messages(mcb.bus, can_dbc)
				self.device_can_busses[mcb.name].clear(signal)
			# Unsupported action
			case _:
				raise ValueError(f"Action {type(action)} not supported for port {port} on device {self.name}")


class TestDeviceManager:
	def __init__(self, test_devices: dict[str, TestDevice]):
		self.test_devices: dict[str, TestDevice] = test_devices

	@classmethod
	def from_json(cls, test_config_path: str, device_config_path: str) -> 'TestDeviceManager':
		with open(test_config_path, 'r') as test_config_file:
			test_config = json.load(test_config_file)

		hil_ids = list(map(
			lambda device: device.get("id"),
			test_config.get("hil_devices")
		))
		hil_devices = serial_helper.discover_devices(hil_ids)

		stop_events = dict(map(
			lambda device: (device.get("id"), threading.Event()),
			test_config.get("hil_devices")
		))

		sers = dict(map(
			lambda device: (device.get("id"), serial_helper.ThreadedSerial(
				hil_devices[device.get("id")],
				stop_events[device.get("id")]
			)),
			test_config.get("hil_devices")
		))

		for ser in sers.values():
			t = threading.Thread(target=ser.run)
			t.start()
		
		test_devices = dict(map(
			lambda device: (device.get("name"), TestDevice.from_json(
				device.get("id"),
				device.get("name"),
				hil_devices[device.get("id")],
				device_config_path
			)),
			test_config.get("hil_devices")
		))
		
		return cls(test_devices)
	
	def maybe_hil_con_from_net(self, board: str, net: str) -> Optional[dut_cons.HilDutCon]:
		if board in self.test_devices:
			return dut_cons.HilDutCon(board, net)
		else:
			return None

	def do_action(self, action_type: action.ActionType, hil_dut_con: dut_cons.HilDutCon) -> Any:
		return self.test_devices[hil_dut_con.device].do_action(action_type, hil_dut_con.port)
	
	def close(self) -> None:
		for device in self.test_devices.values():
			device.close()