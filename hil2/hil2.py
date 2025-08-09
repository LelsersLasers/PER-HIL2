from typing import Optional
import os
import cantools.database.can.database

import test_device
import action
import dut_cons
import component
import net_map

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

	def _map_to_hil_device_con(self, board: str, net: str) -> dut_cons.HilDutCon:
		maybe_hil_dut_con = self.test_device_manager.maybe_hil_con_from_net(board, net)
		match maybe_hil_dut_con:
			case None:
				net_map_entry = self.net_map.get_entry(board, net)
				dut_con = dut_cons.DutCon(net_map_entry.connector_name, net_map_entry.designator)
				return self.dut_cons.get_hil_device_connection(board, dut_con)
			case hil_dut_con:
				return hil_dut_con

	def set_ao(self, board: str, net: str, value: float) -> None:
		self.test_device_manager.do_action(action.SetAo(value), self._map_to_hil_device_con(board, net))

	def hiZ_ao(self, board: str, net: str) -> None:
		...

	def ao(self, board: str, net: str) -> component.AO:
		return component.AO(
			set_fn=lambda value: self.set_ao(board, net, value),
			hiZ_fn=lambda: self.hiZ_ao(board, net)
		)
	
	def get_last_can(self, hil_board: str, can_bus: str, signal: Optional[str | int]) -> Optional[dict]:
		return self.test_device_manager.do_action(
			action.GetLastCan(signal),
			self._map_to_hil_device_con(hil_board, can_bus)
		)