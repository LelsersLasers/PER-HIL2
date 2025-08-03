

class BoardNet:
	def __init__(self, board: str, net: str):
		self.board: str = board
		self.net: str = net

	def __hash__(self):
		return hash((self.board, self.net))

	def __eq__(self, other):
		return self.board == other.board and self.net == other.net
	
	def __neq__(self, other):
		return not (self == other)