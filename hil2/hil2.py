from typing import Optional
import os
import cantools.database.can.database

import test_device
import can_helper
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

	# DO ----------------------------------------------------------------------#
	def set_do(self, board: str, net: str, value: bool) -> None:
		self.test_device_manager.do_action(action.SetDo(value), self._map_to_hil_device_con(board, net))
		
	def hiZ_do(self, board: str, net: str) -> None:
		self.test_device_manager.do_action(action.HiZDo(), self._map_to_hil_device_con(board, net))

	def do(self, board: str, net: str) -> component.DO:
		return component.DO(
			set_fn=lambda value: self.set_do(board, net, value),
			hiZ_fn=lambda: self.hiZ_do(board, net)
		)
	#--------------------------------------------------------------------------#

	# DI ----------------------------------------------------------------------#
	def get_di(self, board: str, net: str) -> bool:
		return self.test_device_manager.do_action(action.GetDi(), self._map_to_hil_device_con(board, net))
	
	def di(self, board: str, net: str) -> component.DI:
		return component.DI(
			get_fn=lambda: self.get_di(board, net)
		)
	#--------------------------------------------------------------------------#

	# AO ----------------------------------------------------------------------#
	def set_ao(self, board: str, net: str, value: float) -> None:
		self.test_device_manager.do_action(action.SetAo(value), self._map_to_hil_device_con(board, net))

	def hiZ_ao(self, board: str, net: str) -> None:
		self.test_device_manager.do_action(action.HiZAo(), self._map_to_hil_device_con(board, net))

	def ao(self, board: str, net: str) -> component.AO:
		return component.AO(
			set_fn=lambda value: self.set_ao(board, net, value),
			hiZ_fn=lambda: self.hiZ_ao(board, net)
		)
	#--------------------------------------------------------------------------#

	# AI ----------------------------------------------------------------------#
	def get_ai(self, board: str, net: str) -> float:
		return self.test_device_manager.do_action(action.GetAi(), self._map_to_hil_device_con(board, net))
	
	def ai(self, board: str, net: str) -> component.AI:
		return component.AI(
			get_fn=lambda: self.get_ai(board, net)
		)
	#--------------------------------------------------------------------------#

	# POT ---------------------------------------------------------------------#
	def set_pot(self, board: str, net: str, value: int) -> None:
		self.test_device_manager.do_action(action.SetPot(value), self._map_to_hil_device_con(board, net))

	def pot(self, board: str, net: str) -> component.POT:
		return component.POT(
			set_fn=lambda value: self.set_pot(board, net, value)
		)
	#--------------------------------------------------------------------------#

	# CAN ---------------------------------------------------------------------#
	def send_can(self, hil_board: str, can_bus: str, signal: str | int, data: dict) -> None:
		self.test_device_manager.do_action(
			action.SendCan(signal, data, self.can_dbc),
			self.test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)

	def get_last_can(self, hil_board: str, can_bus: str, signal: Optional[str | int] = None) -> Optional[can_helper.CanMessage]:
		return self.test_device_manager.do_action(
			action.GetLastCan(signal, self.can_dbc),
			self.test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)
	
	def get_all_can(self, hil_board: str, can_bus: str, signal: Optional[str | int] = None) -> list[can_helper.CanMessage]:
		return self.test_device_manager.do_action(
			action.GetAllCan(signal, self.can_dbc),
			self.test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)
	
	def clear_can(self, hil_board: str, can_bus: str, signal: Optional[str | int] = None) -> None:
		self.test_device_manager.do_action(
			action.ClearCan(signal, self.can_dbc),
			self.test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)

	def can(self, hil_board: str, can_bus: str) -> component.CAN:
		return component.CAN(
			lambda signal, data: self.send_can(hil_board, can_bus, signal, data),
			lambda signal: self.get_last_can(hil_board, can_bus, signal),
			lambda signal: self.get_all_can(hil_board, can_bus, signal),
			lambda signal: self.clear_can(hil_board, can_bus, signal)
		)
	#--------------------------------------------------------------------------#
