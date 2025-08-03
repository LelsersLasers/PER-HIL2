import component
import net_map

HIGH = True
LOW = False

class Hil2:
	# h = hil2.Hil2("config.json", "device_config.json", "netmap.csv", "can.dbc")
	def __init__(self,
		test_config_path: str,
		device_config_path: str,
		net_map_path: str,
		can_dbc_path: str
	):
		...

	def set_ao(self, board: str, net: str, value: float) -> component.AO:
		...

	def hiZ_ao(self, board: str, net: str) -> None:
		...

	def ao(self, board: str, net: str) -> component.AO:
		...
		return component.AO(
			set_fn=lambda value: self.set_ao(board, net, value),
			hiZ_fn=lambda: self.hiZ_ao(board, net)
		)