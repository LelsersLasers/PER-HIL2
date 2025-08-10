from typing import Optional, Union

import cantools.database.can.database

ActionType = Union[
	'SetDo',
	'HiZDo',
	'GetDi',
	'SetAo',
	'HiZAo',
	'GetAi',
	'SetPot',
	'GetLastCan'
]

class SetDo:
	__match_args__ = ("value",)
	def __init__(self, value: bool):
		self.value: bool = value

class HiZDo:
	def __init__(self):
		pass

class GetDi:
	def __init__(self):
		pass

class SetAo:
	__match_args__ = ("value",)
	def __init__(self, value: float):
		self.value: float = value

class HiZAo:
	def __init__(self):
		pass
       
class GetAi:
	def __init__(self):
		pass

class SetPot:
	__match_args__ = ("value",)
	def __init__(self, value: int):
		self.value: int = value

class SendCan:
	__match_args__ = ("signal", "data", "can_dbc")
	def __init__(self, signal: str | int, data: dict, can_dbc: cantools.database.can.database.Database):
		self.signal: str | int = signal
		self.data: dict = data
		self.can_dbc: cantools.database.can.database.Database = can_dbc

class GetLastCan:
	__match_args__ = ("signal", "can_dbc")
	def __init__(self, signal: Optional[str | int], can_dbc: cantools.database.can.database.Database):
		self.signal: Optional[str | int] = signal
		self.can_dbc: cantools.database.can.database.Database = can_dbc

class GetAllCan:
	__match_args__ = ("signal", "can_dbc")
	def __init__(self, signal: Optional[str | int], can_dbc: cantools.database.can.database.Database):
		self.signal: Optional[str | int] = signal
		self.can_dbc: cantools.database.can.database.Database = can_dbc

class ClearCan:
	__match_args__ = ("signal", "can_dbc")
	def __init__(self, signal: Optional[str | int], can_dbc: cantools.database.can.database.Database):
		self.signal: Optional[str | int] = signal
		self.can_dbc: cantools.database.can.database.Database = can_dbc

