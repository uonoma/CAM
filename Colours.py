import sys

from header import DIR
sys.path.insert(0, DIR+'/GraphicsTools/')

class ColourScheme:
	fontOpacity = 0.87

	def __init__(self):

		self.darkGrey=(0.2,0.2,0.2)
		self.lightGrey=(0.8,0.8,0.8)
		self.white=(1,1,1)

		self.background=self.white

		self.linkActive = self.darkGrey
		self.linkInactive = self.lightGrey

		self.red = tuple([i/255.0 for i in [255,102,102]])
		self.fred = tuple([i/255.0 for i in [255,188,188]])
		self.pred = tuple([i/255.0 for i in [246,227,227]])

		self.yellow=tuple([i/255.0 for i in [255,255,51]])
		self.fyellow=tuple([i/255.0 for i in [255,244,135]])
		self.pyellow = tuple([i/255.0 for i in [249,252,190]])

		self.green=tuple([i/255.0 for i in [51, 255, 51]])
		self.fgreen=tuple([i/255.0 for i in [192, 255, 179]])
		self.pgreen=tuple([i/255.0 for i in [218, 252, 220]])

		self.purple=tuple([i/255.0 for i in [199,21,133]])
		self.fpurple=tuple([i/255.0 for i in [255,198,252]])
		self.ppurple=tuple([i/255.0 for i in [250,231,250]])
		self.black=(0,0,0)

		self.lightText=(1,1,1)
		self.darkText=(0,0,0)

		# node colour when selected
		self.highlight = tuple([i*0.5 + 0.5 for i in self.darkGrey])

		# link colour when selected
		self.highlight2 = tuple([i/255.0 for i in [255,140,0]])

		# default colour for comment box background
		self.commentBg = (252, 178, 102)

	def toHexf255(self,colour):
		return '#%02x%02x%02x' % tuple([int(v) for v in colour])

	def toHex(self, colour):
		return self.toHexf255([int(255*v) for v in colour])
