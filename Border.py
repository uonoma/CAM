import sys

from header import DIR
sys.path.insert(0, DIR+'/GraphicsTools/')

class Border:

	def __init__(self):
		self.neutral = {'colour': 'yellow', 'thickness': 2}
		self.ambivalent = {'colour': 'purple', 'thickness': 2}
		self.positive1 = {'colour': 'green', 'thickness': 2}
		self.positive2 = {'colour': 'green', 'thickness': 4}
		self.positive3 = {'colour': 'green', 'thickness': 9}
		self.negative1 = {'colour': 'red', 'thickness': 2}
		self.negative2 = {'colour': 'red', 'thickness': 4}
		self.negative3 = {'colour': 'red', 'thickness': 9}
		self.ambivalent = {'colour': 'purple', 'thickness': 2}
