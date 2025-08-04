from typing import Any, Optional

import enum
import json

import dut_cons
import action

class AdcConfig:
	def __init__(self, adc_config: dict):
		self.bit_resolution: int = adc_config.get("bit_resolution")
		self.adc_reference_v: float = adc_config.get("adc_reference_v")
		self.five_v_reference_v: float = adc_config.get("5v_reference_v")
		self.twenty_four_v_reference_v: float = adc_config.get("24v_reference_v")

	def raw_to_5v(self, raw_value: int) -> float:
		...
	def raw_to_24v(self, raw_value: int) -> float:
		...

class DacConfig:
	def __init__(self, dac_config: dict):
		self.bit_resolution: int = dac_config.get("bit_resolution")
		self.reference_v: float = dac_config.get("reference_v")

	def v_to_raw(self, value: float) -> int:
		...

class PotConfig:
	def __init__(self, pot_config: dict):
		self.bit_resolution: int = pot_config.get("bit_resolution")

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
		self.port: int = can_bus.get("port")


class TestDevice:
	def __init__(self,
		hil_id: int,
		name: str,
		ports: dict[str, Port],
		muxs: dict[str, Mux],
		can_busses: dict[str, CanBus],
		adc_config: AdcConfig,
		dac_config: DacConfig,
		pot_config: PotConfig
	):
		self.hil_id: int = hil_id
		self.name: str = name
		self.ports: dict[str, Port] = ports
		self.muxs: dict[str, Mux] = muxs
		self.can_busses: dict[str, CanBus] = can_busses
		self.adc_config: AdcConfig = adc_config
		self.dac_config: DacConfig = dac_config
		self.pot_config: PotConfig = pot_config


	@classmethod
	def from_json(cls, hil_id: int, name: str, device_config_path: str):
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
			pot_config
		)
	
	def select_mux(self, mux_select: MuxSelect) -> None:
		for i, p in enumerate(mux_select.mux.select_ports):
			select_bit = 1 if (mux_select.select & (1 << i)) else 0
			self.set_do(p, select_bit)
		self.set_ao(mux_select.mux.port, mux_select)
	
	def set_do(self, port: str, value: bool) -> None:
		...

	def hiZ_do(self, port: str) -> None:
		...

	def get_di(self, port: str) -> bool:
		...

	def set_ao(self, pin: int, value: float) -> None:
		...
	
	def hiZ_ao(self, port: str) -> None:
		...
	
	def get_ai(self, port: str) -> float:
		...

	def set_pot(self, port: str, value: int) -> None:
		...
	
	def do_action(self, action: action.ActionType, port: str) -> Any:
		maybe_port = self.ports.get(port, None)
		maybe_mux_select = next(
			(val for m in self.muxs.values() if (val := m.select_from_name(port)) is not None),
			None,
		)
		maybe_can_bus = self.can_busses.get(port, None)

		match (action, maybe_port, maybe_mux_select, maybe_can_bus):
			# Set DO + direct port
			case (action.SetDo(value), mp, None, None) if mp is not None and mp.mode == 'DO':
				self.set_do(mp.port, value)
			# Set DO + mux select
			case (action.SetDo(value), None, mms, None) if mms is not None and mms.mux.mode == 'DO':
				self.select_mux(mms)
				self.set_do(mms.mux.port, value)
			# HiZ DO + direct port
			case (action.HiZDo(), mp, None, None) if mp is not None and mp.mode == 'DO':
				self.hiZ_do(mp.port)
			# HiZ DO + mux select
			case (action.HiZDo(), None, mms, None) if mms is not None and mms.mux.mode == 'DO':
				self.select_mux(mms)
				self.hiZ_do(mms.mux.port)
			# Get DI + direct port
			case (action.GetDi(), mp, None, None) if mp is not None and mp.mode == 'DI':
				return self.get_di(mp.port)
			# Get DI + mux select
			case (action.GetDi(), None, mms, None) if mms is not None and mms.mux.mode == 'DI':
				self.select_mux(mms)
				return self.get_di(mms.mux.port)
			# Set AO + direct port
			case (action.SetAo(value), mp, None, None) if mp is not None and mp.mode == 'AO':
				self.set_ao(mp.port, value)
			# HiZ AO + direct port
			case (action.HiZAo(), mp, None, None) if mp is not None and mp.mode == 'AO':
				self.hiZ_ao(mp.port)
			# Get AI + direct port
			case (action.GetAi(), mp, None, None) if mp is not None and mp.mode == 'AI':
				return self.get_ai(mp.port)
			# Get AI + mux select
			case (action.GetAi(), None, mms, None) if mms is not None and mms.mux.mode == 'AI':
				self.select_mux(mms)
				return self.get_ai(mms.mux.port)
			# Set Pot + direct port
			case (action.SetPot(value), mp, None, None) if mp is not None and mp.mode == 'POT':
				self.set_pot(mp.port, value)
			case _:
				raise ValueError(f"Action {type(action)} not supported for port {port} on device {self.name}")
	
class TestDeviceManager:
	def __init__(self, test_devices: dict[str, TestDevice]):
		self.test_devices: dict[str, TestDevice] = test_devices

	@classmethod
	def from_json(cls, test_config_path: str, device_config_path: str) -> 'TestDeviceManager':
		with open(test_config_path, 'r') as test_config_file:
			test_config = json.load(test_config_file)
		
		test_devices = dict(map(
			lambda device: (device.get("name"), TestDevice.from_json(
				device.get("id"),
				device.get("name"),
				device_config_path
			)),
			test_config.get("hil_devices")
		))
		
		return cls(test_devices)
	
	def do_action(self, action_type: action.ActionType, hil_dut_con: dut_cons.HilDutCon) -> Any:
		return self.test_devices[hil_dut_con.device].do_action(action_type, hil_dut_con.port)