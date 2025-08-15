from typing import Optional


class CanMessage:
	def __init__(self, signal: str | int, data: dict):
		self.signal: str | int = signal
		self.data: dict = data


class CanMessageManager:
	def __init__(self):
		self.messages: list[CanMessage] = []

	def add_multiple(self, messages: list[CanMessage]) -> None:
		self.messages.extend(messages)

	def get_last(self, signal: Optional[str | int]) -> Optional[CanMessage]:
		return next(
			filter(lambda msg: msg.signal == signal, reversed(self.messages)),
			None
		)
	
	def get_all(self, signal: Optional[str | int] = None) -> list[CanMessage]:
		return list(filter(
			lambda msg: signal is None or msg.signal == signal,
			self.messages
		))
	
	def clear(self, signal: Optional[str | int] = None) -> None:
		if signal is None:
			self.messages.clear()
		else:
			self.messages = list(filter(
				lambda msg: msg.signal != signal,
				self.messages
			))