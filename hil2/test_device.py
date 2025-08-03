import json

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
		self.port: int = port.get("port")
		self.name: str = port.get("name")
		self.mode: str = port.get("mode")

class Mux:
	def __init__(self, mux: dict):
		self.name: str = mux.get("name")
		self.mode: str = mux.get("mode")
		self.select_ports: list[int] = mux.get("select_ports")
		self.port: int = mux.get("port")

class CanBus:
	def __init__(self, can_bus: dict):
		self.port: int = can_bus.get("port")
		self.name: str = can_bus.get("name")


class TestDevice:
	def __init__(self,
		hil_id: int,
		name: str,
		ports: list[Port],
		muxs: list[Mux],
		can_busses: list[CanBus],
		adc_config: AdcConfig,
		dac_config: DacConfig,
		pot_config: PotConfig
	):
		self.hil_id: int = hil_id
		self.name: str = name
		self.ports: list[Port] = ports
		self.muxs: list[Mux] = muxs
		self.can_busses: list[CanBus] = can_busses
		self.adc_config: AdcConfig = adc_config
		self.dac_config: DacConfig = dac_config
		self.pot_config: PotConfig = pot_config


	@classmethod
	def from_json(cls, hil_id: int, name: str, device_config_path: str):
		with open(device_config_path, 'r') as device_config_path:
			device_config = json.load(device_config_path)

		muxs = list(map(Mux, device_config.get("muxs")))
		ports = list(map(Port, device_config.get("ports")))
		can_busses = list(map(CanBus, device_config.get("can")))
		
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