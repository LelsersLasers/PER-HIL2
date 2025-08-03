import os
import cantools.database.can.database

import test_device
import dut_cons
import component
import net_map

HIGH = True
LOW = False

class Hil2:
	def __init__(self,
		test_config_path: str,
		device_config_path: str,
		net_map_path: str,
		can_dbc_path: str
	):
		self.net_map: net_map.NetMap = net_map.NetMap.from_csv(net_map_path)
		self.test_device_manager: test_device.TestDeviceManager = test_device.TestDeviceManager.from_json(
			test_config_path,
			device_config_path
		)
		self.dut_cons: dut_cons.DutCons = dut_cons.DutCons.from_json(test_config_path)
		self.can_dbc: cantools.database.can.database.Database = cantools.db.load_file(os.path.join(can_dbc_path))

	def set_ao(self, board: str, net: str, value: float) -> None:
		net_map_entry = self.net_map.get_entry(board, net)
		net_map_entry.component
		net_map_entry.designator

	def hiZ_ao(self, board: str, net: str) -> None:
		...

	def ao(self, board: str, net: str) -> component.AO:
		return component.AO(
			set_fn=lambda value: self.set_ao(board, net, value),
			hiZ_fn=lambda: self.hiZ_ao(board, net)
		)