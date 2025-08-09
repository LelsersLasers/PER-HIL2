from typing import Optional


class CanMessage:
	def __init__(self, signal: str | int, data: dict):
		self.signal: str | int = signal
		self.data: dict = data

class DeviceCanBus:
	def __init__(self):
		self.messages: list[CanMessage] = []

	# def send(self, signal: str | int, data: dict) -> None:
	# 	...
	
	def get_last(self, signal: Optional[str | int]) -> Optional[dict]:
		if signal is None:
			return self.messages[-1] if self.messages else None
		return next(
			filter(lambda msg: msg.signal == signal, reversed(self.messages)),
			None
		)
	
	def get_all(self, signal: Optional[str | int] = None) -> list[dict]:
		return list(filter(
			lambda msg: msg.signal == signal,
			self.messages
		))
	
	def clear(self, signal: Optional[str | int] = None) -> None:
		if signal is None:
			self.messages.clear()
		else:
			self.messages = list(filter(lambda msg: msg.signal != signal, self.messages))