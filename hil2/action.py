from typing import Optional, Union

HIGH = True
LOW = False

ActionType = Union[
	'SetDo',
	'HiZDo',
	'GetDi',
	'SetAo',
	'HiZAo',
	'GetAi',
	'SetPot',
	# 'CanClear',
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

# class CanClear:
# 	__match_args__ = ("signal",)
# 	def __init__(self, signal: Optional[str | int]):
# 		self.signal: Optional[str | int] = signal

