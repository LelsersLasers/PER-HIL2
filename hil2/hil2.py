from typing import Optional

import os

import cantools
import cantools.database.can.database as cantools_db

import action
import can_helper
import component
import dut_cons
import net_map
import test_device


class Hil2:
	def __init__(self,
		test_config_path: str,
		device_config_path: str,
		net_map_path: str,
		can_dbc_path: str
	):
		self._net_map: net_map.NetMap = net_map.NetMap.from_csv(net_map_path)
		self._test_device_manager: test_device.TestDeviceManager = (
            test_device.TestDeviceManager.from_json(
                test_config_path, device_config_path
            )
        )
		self._dut_cons: dut_cons.DutCons = dut_cons.DutCons.from_json(test_config_path)
		self._can_dbc: cantools_db.Database = cantools.db.load_file(
			os.path.join(can_dbc_path)
		)

	def _map_to_hil_device_con(self, board: str, net: str) -> dut_cons.HilDutCon:
		maybe_hil_dut_con = self._test_device_manager.maybe_hil_con_from_net(board, net)
		match maybe_hil_dut_con:
			case None:
				net_map_entry = self._net_map.get_entry(board, net)
				dut_con = dut_cons.DutCon(
					net_map_entry.connector_name, net_map_entry.designator
				)
				return self._dut_cons.get_hil_device_connection(board, dut_con)
			case hil_dut_con:
				return hil_dut_con

	# DO ------------------------------------------------------------------------------#
	def set_do(self, board: str, net: str, value: bool) -> None:
		self._test_device_manager.do_action(
			action.SetDo(value), self._map_to_hil_device_con(board, net)
		)
		
	def hiZ_do(self, board: str, net: str) -> None:
		self._test_device_manager.do_action(
			action.HiZDo(), self._map_to_hil_device_con(board, net)
		)

	def do(self, board: str, net: str) -> component.DO:
		return component.DO(
			set_fn=lambda value: self.set_do(board, net, value),
			hiZ_fn=lambda: self.hiZ_do(board, net)
		)
	#----------------------------------------------------------------------------------#

	# DI ------------------------------------------------------------------------------#
	def get_di(self, board: str, net: str) -> bool:
		return self._test_device_manager.do_action(
			action.GetDi(), self._map_to_hil_device_con(board, net)
		)

	def di(self, board: str, net: str) -> component.DI:
		return component.DI(
			get_fn=lambda: self.get_di(board, net)
		)
	#----------------------------------------------------------------------------------#

	# AO ------------------------------------------------------------------------------#
	def set_ao(self, board: str, net: str, value: float) -> None:
		self._test_device_manager.do_action(
			action.SetAo(value), self._map_to_hil_device_con(board, net)
		)

	def hiZ_ao(self, board: str, net: str) -> None:
		self._test_device_manager.do_action(
			action.HiZAo(), self._map_to_hil_device_con(board, net)
		)

	def ao(self, board: str, net: str) -> component.AO:
		return component.AO(
			set_fn=lambda value: self.set_ao(board, net, value),
			hiZ_fn=lambda: self.hiZ_ao(board, net)
		)
	#----------------------------------------------------------------------------------#

	# AI ------------------------------------------------------------------------------#
	def get_ai(self, board: str, net: str) -> float:
		return self._test_device_manager.do_action(
			action.GetAi(), self._map_to_hil_device_con(board, net)
		)

	def ai(self, board: str, net: str) -> component.AI:
		return component.AI(
			get_fn=lambda: self.get_ai(board, net)
		)
	#----------------------------------------------------------------------------------#

	# POT -----------------------------------------------------------------------------#
	def set_pot(self, board: str, net: str, value: float) -> None:
		self._test_device_manager.do_action(
			action.SetPot(value), self._map_to_hil_device_con(board, net)
		)

	def pot(self, board: str, net: str) -> component.POT:
		return component.POT(
			set_fn=lambda value: self.set_pot(board, net, value)
		)
	#----------------------------------------------------------------------------------#

	# CAN -----------------------------------------------------------------------------#
	def send_can(
		self, hil_board: str, can_bus: str, signal: str | int, data: dict
	) -> None:
		self._test_device_manager.do_action(
			action.SendCan(signal, data, self._can_dbc),
			self._test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)

	def get_last_can(
        self, hil_board: str, can_bus: str, signal: Optional[str | int] = None
	) -> Optional[can_helper.CanMessage]:
		return self._test_device_manager.do_action(
			action.GetLastCan(signal, self._can_dbc),
			self._test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)
	
	def get_all_can(
		self, hil_board: str, can_bus: str, signal: Optional[str | int] = None
	) -> list[can_helper.CanMessage]:
		return self._test_device_manager.do_action(
			action.GetAllCan(signal, self._can_dbc),
			self._test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)
	
	def clear_can(
        self, hil_board: str, can_bus: str, signal: Optional[str | int] = None
	) -> None:
		self._test_device_manager.do_action(
			action.ClearCan(signal, self._can_dbc),
			self._test_device_manager.maybe_hil_con_from_net(hil_board, can_bus)
		)

	def can(self, hil_board: str, can_bus: str) -> component.CAN:
		return component.CAN(
			lambda signal, data: self.send_can(hil_board, can_bus, signal, data),
			lambda signal: self.get_last_can(hil_board, can_bus, signal),
			lambda signal: self.get_all_can(hil_board, can_bus, signal),
			lambda signal: self.clear_can(hil_board, can_bus, signal)
		)
	#----------------------------------------------------------------------------------#
