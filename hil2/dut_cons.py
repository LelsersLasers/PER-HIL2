import json

import hil_errors


class HilDutCon:
	def __init__(self, device: str, port: str):
		self.device: str = device
		self.port: str = port

	@classmethod
	def from_json(cls, hil_dut_con: dict) -> 'HilDutCon':
		match hil_dut_con:
			case { "device": device, "port": port }:
				return cls(device, port)
			case _:
				error_msg = f"Invalid HIL DUT connection configuration: {hil_dut_con}"
				raise hil_errors.ConfigurationError(error_msg)


class DutCon:
	def __init__(self, connector: str, pin: int):
		self.connector: str = connector
		self.pin: int = pin

	@classmethod
	def from_json(cls, dut_con: dict) -> 'DutCon':
		match dut_con:
			case { "connector": connector, "pin": pin }:
				return cls(connector, pin)
			case _:
				error_msg = f"Invalid DUT connection configuration: {dut_con}"
				raise hil_errors.ConfigurationError(error_msg)


class DutBoardCons:
	def __init__(self, harness_connections: list[dict]):
		self._harness_connections: dict[DutCon, HilDutCon] = dict(map(
			lambda con: (
				DutCon.from_json(con.get("dut")),
				HilDutCon.from_json(con.get("hil"))
			),
			harness_connections
		))

	def get_hil_device_connection(self, dut_con: DutCon) -> HilDutCon:
		if dut_con in self._harness_connections:
			return self._harness_connections[dut_con]
		else:
			error_msg = (
				"No HIL connection found for DUT connection: "
				f"({dut_con.connector}, {dut_con.pin})"
			)
			raise hil_errors.ConnectionError(error_msg)


class DutCons:
	def __init__(self, dut_connections: dict[DutBoardCons]):
		self.dut_connections: dict[str, DutBoardCons] = dut_connections

	@classmethod
	def from_json(cls, test_config_path: str) -> 'DutCons':
		with open(test_config_path, 'r') as test_config_file:
			test_config = json.load(test_config_file)

		board_cons = {}
		for board, connections in test_config.get("dut_connections").items():
			board_cons[board] = DutBoardCons(connections.get("harness_connections"))

		return cls(board_cons)
	
	def get_hil_device_connection(self, board: str, dut_con: DutCon) -> HilDutCon:
		if board in self.dut_connections:
			return self.dut_connections[board].get_hil_device_connection(dut_con)
		else:
			error_msg = f"No HIL connection found for DUT board: {board}"
			raise hil_errors.ConnectionError(error_msg)
