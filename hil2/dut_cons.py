import json


class HilDutCon:
	def __init__(self, device: str, port: str):
		self.device: str = device
		self.port: str = port

	@classmethod
	def from_json(cls, hil_dut_con: dict) -> 'HilDutCon':
		return cls(hil_dut_con.get("device"), hil_dut_con.get("port"))


class DutCon:
	def __init__(self, connector: str, pin: int):
		self.connector: str = connector
		self.pin: int = pin

	@classmethod
	def from_json(cls, dut_con: dict) -> 'DutCon':
		return cls(dut_con.get("connector"), dut_con.get("pin"))


class DutBoardCons:
	def __init__(self, harness_connections: list[dict]):
		self.harness_connections: dict[DutCon, HilDutCon] = dict(map(
			lambda con: (DutCon.from_json(con.get("dut")), HilDutCon.from_json(con.get("hil"))),
			harness_connections
		))

	def get_hil_device_connection(self, dut_con: DutCon) -> HilDutCon:
		return self.harness_connections[dut_con]


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
		return self.dut_connections[board].get_hil_device_connection(dut_con)