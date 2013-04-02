import itertools


def segment(iterable, segment_size):
	iterator = iter(iterable)
	def get_segment():
		seg = []
		for _ in range(segment_size):
			try:
				seg.append(iterator.next())
			except StopIteration:
				break
		if seg:
			return seg
	seg = get_segment()
	while seg is not None:
		yield seg
		seg = get_segment()


class InactiveNodeError(Exception): pass


class InactiveNode(object):

	coordinates = None

	@property
	def is_occupied(self):
		raise InactiveNodeError()

	@is_occupied.setter
	def is_occupied(self, value):
		raise InactiveNodeError()

	@property
	def is_valid(self):
		return False

	def __str__(self):
		return " "


class ActiveNode(object):

	def __init__(self, board, column_index, row_index):
		self.column_index = column_index
		self.row_index = row_index
		self._board = board

	@property
	def coordinates(self):
		return self.row_index, self.column_index

	@property
	def is_occupied(self):
		return self._board.is_occupied(self.row_index, self.column_index)

	@is_occupied.setter
	def is_occupied(self, value):
		self._board.set_occupancy(self.row_index, self.column_index, value)

	@property
	def is_valid(self):
		return True

	def __str__(self):
		if self.is_occupied:
			return "X"
		return "O"

	@property
	def up(self):
		return self._board.get_node(self.row_index - 1, self.column_index)

	@property
	def down(self):
		return self._board.get_node(self.row_index + 1, self.column_index)

	@property
	def left(self):
		return self._board.get_node(self.row_index, self.column_index - 1)

	@property
	def right(self):
		return self._board.get_node(self.row_index, self.column_index + 1)

	@property
	def moves(self):
		moves = []
		if self.is_occupied:
			try:
				if self.up.is_occupied:
					if not self.down.is_occupied:
						moves.append((self.up.coordinates, self.down.coordinates))
				else:
					if self.down.is_occupied:
						moves.append((self.down.coordinates, self.up.coordinates))
			except InactiveNodeError:
				pass
			try:
				if self.left.is_occupied:
					if not self.right.is_occupied:
						moves.append((self.left.coordinates, self.right.coordinates))
				else:
					if self.right.is_occupied:
						moves.append((self.right.coordinates, self.left.coordinates))
			except InactiveNodeError:
				pass
		return moves


class Board(object):

	inactive_node = InactiveNode()

	def __init__(self, row_widths):
		# Make sure that we have odd parties and thus that there is a center node.
		self.width = max(row_widths)
		self.height = len(row_widths)
		assert self.width & 0b1
		assert self.height & 0b1

		self._nodes = []
		for row_index, row_width in enumerate(row_widths):
			assert self.width >= row_width and row_width % 2 == 1
			padding = (self.width - row_width)/2
			for column_index in range(self.width):
				self._nodes.append(
					self.build_node(
						column_index,
						row_index,
						padding <= column_index < (self.width - padding)
					)
				)

		self.center_row_index, self.center_column_index = self.width/2, self.height/2
		self.configuration = self.build_default_configuration()
		self.symmetry_functions = self.build_symmetry_functions()

	def build_symmetry_functions(self):
		return [
			lambda i, j: (i, j),
			lambda i, j: (j, i),
			lambda i, j: (i, self.width-1-j),
			lambda i, j: (j, self.width-1-i),
			lambda i, j: (self.width-1-i, j),
			lambda i, j: (self.width-1-j, i),
			lambda i, j: (self.width-1-i, self.width-1-j),
			lambda i, j: (self.width-1-j, self.width-1-i),
		]

	def build_default_configuration(self):
		val = [True for _ in range(self.width*self.height)]
		val[self.center_row_index*self.width + self.center_column_index] = False
		return val

	def build_node(self, column_index, row_index, active):
		if active:
			return ActiveNode(self, column_index, row_index)
		return self.inactive_node

	def get_node(self, row_index, column_index):
		if 0 <= column_index < self.width and 0 <= row_index < self.height:
			return self._nodes[row_index*self.width + column_index]
		else:
			return self.inactive_node

	def is_occupied(self, row_index, column_index):
		return self.configuration[row_index*self.width + column_index]

	def set_occupancy(self, row_index, column_index, value):
		self.configuration[row_index*self.width + column_index] = value

	@property
	def yield_moves(self):
		return itertools.chain(*[node.moves for node in self._nodes if node.is_valid])

	def __str__(self):
		return "\n".join(' '.join(map(str, row)) for row in segment(self._nodes, self.width))

	def get_symmetric_configuration_strings(self):
		# This assumes symmetry
		configuration_strings = []
		for symmetry_function in self.symmetry_functions:
			nodes = [
				self.get_node(*symmetry_function(i, j))
				for i in range(self.width) for j in range(self.width)
			]
			configuration_strings.append(''.join(map(str, nodes)))
		return configuration_strings

	@property
	def configuration_string(self):
		return ''.join(map(str, self._nodes))

	def _check_node(self, node):
		if not node.is_valid: return True
		return not node.is_occupied \
			if node.coordinates != (self.center_row_index, self.center_column_index) \
			   else node.is_occupied

	@property
	def winning(self):
		return all(self._check_node(node) for node in self._nodes)


class Solver(object):

	call_count = 0
	hit_count = 0
	
	def __init__(self, board):
		self._board = board
		self.known_losing_positions = set()

	def solve(self):
		self.call_count += 1
		if self.call_count & 0b111111111111 == 0b100000000000:
			print len(self.known_losing_positions)
			print "call_count " + str(self.call_count)
			print "hit_count " + str(self.hit_count)
			print str(self._board)
		if self._board.configuration_string in self.known_losing_positions:
			self.hit_count += 1
			return None

		this_configuration = self._board.configuration
		if self._board.winning:
			return []

		for ((src_row, src_clm), (dst_row, dst_clm)) in self._board.yield_moves:
			self._board.configuration = this_configuration[:]
			self._board.set_occupancy(src_row, src_clm, False)
			self._board.set_occupancy(
				(src_row + dst_row) >> 1, # These averages give us the jumped peg.
				(src_clm + dst_clm) >> 1,
				False
			)
			self._board.set_occupancy(dst_row, dst_clm, True)
			move_result = self.solve()
			if move_result is not None:
				self._board.configuration = this_configuration
				print str(self._board)
				print ''
				move_result.append(((src_row, src_clm), (dst_row, dst_clm)))
				return move_result
		self._board.configuration = this_configuration
		self.known_losing_positions.update(
			self._board.get_symmetric_configuration_strings()
		)
		return None
			
		


if __name__ == '__main__':
	european = Board([3, 5, 7, 7, 7, 5, 3])
	english = Board([3, 3, 7, 7, 7, 3, 3])
	print Solver(english).solve()
	print Solver(european).solve()