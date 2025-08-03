import json

class DutCon:
	def __init__(self, dut_con: dict):
		self.dut_connector: str = dut_con.get("dut").get("connector")
		self.dut_pin: int = dut_con.get("dut").get("pin")
		self.hil_device: str = dut_con.get("hil").get("device")
		self.hil_port: str = dut_con.get("hil").get("port")

class DutBoardCons:
	def __init__(self, harness_connections: list[dict]):
		self.harness_connections: list[DutCon] = list(map(DutCon, harness_connections))

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