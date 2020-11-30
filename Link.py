from header import *
from i18n import *
from Comment import *
from datetime import *
from PIL import ImageTk, Image, ImageGrab, ImageDraw
import cv2 as cv

class Link:

	activeWidth = 5

	length = 0.0

	# Distance between two links drawn between the same two nodes (pre-link & post-link)
	preLinkOffset = 10

	def __init__(self, parentSheet, nA, nB, directed, strength,
	label="", comment="", coordOffset=0, draw=False, diffTag=""):
		self.root=parentSheet.root
		self.canvas=parentSheet.canvas

		self.initTime = datetime.now()

		self.linkLine = None

		self.parentSheet = parentSheet

		# Link annotation in aggregated CAMs. Not used in diff CAM version of the script
		self.label = label

		# "A"->Link was added in post-CAM.
		# "D"->Link was deleted in post-CAM.
		# x (int value)->Link was drawn in both CAMs, x=value of link strength in pre-CAM
		self.diffTag = diffTag

		self.cs = self.parentSheet.cs

		self.selected = False

		# Start and end nodes
		self.nA = nA
		self.nB = nB

		self.coordOffset = coordOffset

		self.x0,self.y0,self.x1,self.y1 = self.getCoords()

		self.y_mean =\
			min(self.y1, self.y0)+(max(self.y1, self.y0)-min(self.y1, self.y0))/2
		self.x_mean =\
			min(self.x1, self.x0)+(max(self.x1, self.x0)-min(self.x1, self.x0))/2

		# Positive link strength -> Dashed = ()
		# Negative link strength -> Dashed = (5,5)
		self.dashed = ()

		self.strength = strength

		if strength < 0:
			self.dashed = (5, 5)
			strength = -strength

		# True if link is unidirectional, False if bidirectional
		self.directed = directed

		if directed:
			self.strengthA = strength
			self.strengthB = 0
		else:
			self.strengthA = strength
			self.strengthB = strength

		self.thickness = max(self.strengthA, self.strengthB) * 2

		if diffTag not in ["", "D", "A"]:
			preStrength = int(diffTag)
			if preStrength < 0:
				preStrength = -preStrength
				self.preDashed = (5,5)
			else:
				self.preStrength = preStrength
				self.preDashed = ()
			if directed:
				self.preStrengthA = preStrength
				self.preStrengthB = 0
			else:
				self.preStrengthA = preStrength
				self.preStrengthB = preStrength
			self.preThickness = max(self.preStrengthA, self.preStrengthB) * 2

		if comment == "":
			self.hasComment = False
			self.commentText = ""
		else:
			self.hasComment = True
			self.commentText = comment
			self.initComment(text=self.commentText)

		self._layers = []

		self.colour = self.cs.linkActive

		# Lighter colour for deleted links
		if self.diffTag == "D":
			self.colour = self.cs.linkInactive

		self.lineIndex = -1
		self.preLineIndex = -1

		if draw:
			self.initDrawing()

	def initDrawing(self):
		# Draw main line
		self.lineIndex = self.add_to_layer(self.thickness,
			self.canvas.create_line, (self.x0,self.y0,self.x1,self.y1),
			fill=self.cs.toHex(self.colour), activefill = self.cs.toHex(self.cs.highlight2),
			width=self.thickness, activewidth = self.activeWidth,
			dash=self.dashed)

		# Place arrow(s) according to link direction
		if self.strengthA > self.strengthB:
			self.canvas.itemconfig(self.lineIndex, arrow = LAST, arrowshape=(10,15,7))
		elif self.strengthB > self.strengthA:
			self.canvas.itemconfig(self.lineIndex, arrow = FIRST, arrowshape=(10,15,7))
		elif self.strengthA == self.strengthB:
			self.canvas.itemconfig(self.lineIndex, arrow = BOTH, arrowshape=(10,15,7))

		# If link also exists in pre-CAM, additionally draw pre-CAM line.
		if self.diffTag not in ["", "D", "A"]:
				self.preLineIndex = self.add_to_layer(self.thickness,
				self.canvas.create_line,
				(self.x0+self.preLinkOffset, self.y0+self.preLinkOffset,
				 self.x1+self.preLinkOffset, self.y1+self.preLinkOffset),
				fill=self.cs.toHex(self.cs.lightGrey), activefill=self.cs.toHex(self.cs.highlight2),
				width=self.preThickness, activewidth=self.preThickness,
				dash=self.preDashed)

		# Place arrow(s) according to link direction for pre-CAM link.
		if self.diffTag not in ["", "D", "A"]:
			if self.preStrengthA > self.preStrengthB:
				self.canvas.itemconfig(self.preLineIndex, arrow=LAST,
									   arrowshape=(10, 15, 7))
			elif self.preStrengthB > self.preStrengthA:
				self.canvas.itemconfig(self.preLineIndex, arrow=FIRST,
									   arrowshape=(10, 15, 7))
			elif self.preStrengthA == self.preStrengthB:
				self.canvas.itemconfig(self.preLineIndex, arrow=BOTH,
									   arrowshape=(10, 15, 7))

		self.grow()

	def add_to_layer(self, layer, command, coords, **kwargs):

		layer_tag = "layer %s" % layer
		
		if layer_tag not in self._layers:
			self._layers.append(layer_tag)
		
		tags = kwargs.setdefault("tags", [])
		tags.append(layer_tag)
		item_id = command(coords, **kwargs)
		return item_id

	def updateLine(self):
		x0,y0,x1,y1 = self.getCoords()
		self.y_mean = min(y1, y0)+(max(y1, y0)-min(y1, y0))/2
		self.x_mean = min(x1, x0)+(max(x1, x0)-min(x1, x0))/2

		if self.hasComment:
			self.comment.updatePos((self.x_mean, self.y_mean))

		self.canvas.coords(self.lineIndex, x0, y0, x1, y1)
		self.canvas.itemconfig(self.lineIndex, width=self.thickness,
			dash=self.dashed, fill=self.cs.toHex(self.colour))

		if self.diffTag not in ["", "D", "A"]:
			self.canvas.coords(self.preLineIndex, x0+self.preLinkOffset,
							   y0+self.preLinkOffset, x1+self.preLinkOffset,
							   y1+self.preLinkOffset)
			self.canvas.itemconfig(self.preLineIndex, width=self.thickness,
								   dash=self.preDashed, fill=self.cs.toHex(self.cs.lightGrey))

	def remove(self, event=[]):
		self.parentSheet.dragging = True

		self.canvas.delete(self.lineIndex)

		if self.preLineIndex > -1:
			self.canvas.delete(self.preLineIndex)

		if self.hasComment:
			self.comment.deleteComment(event)

	def endDrag(self, event):
		self.parentSheet.dragging = False

	def grow(self, stage=0):
		totalStages = 10

		f = 1.0 * stage/totalStages

		if stage <= totalStages:
			x0,y0,x1,y1 = self.getCoords()

			x1p = (1.0 - f) * x0 + f * x1
			y1p = (1.0 - f) * y0 + f * y1

			self.canvas.coords(self.lineIndex, x0, y0, x1p, y1p)


			w = self.thickness * f

			self.canvas.itemconfig(self.lineIndex, width=int(w))

		if stage < totalStages:
			t = threading.Timer(0.02, self.grow, [stage+1])
			t.daemon = True
			t.start()

	def getLinkStrength(self):
		if self.dashed == ():
			strength = self.thickness
		else:
			strength = -self.thickness
		return strength

	def setLinkStrength(self, strength):
		s = int(strength) * 2
		if s > 1:
			self.thickness = s
			self.dashed = ()
		else:
			self.thickness = -s
			self.dashed = (5,5)
		self.updateLine()
		self.updateStrengths()
		self.parentSheet.acceptanceNode.calculateAcceptance()

	def updateStrengths(self):
		if self.strengthA > self.strengthB:
			self.strengthA = self.thickness
		if self.strengthA <= self.strengthB:
			self.strengthB = self.thickness

	def getCoords(self):
		try:
			x0,y0,x1,y1 = self.nA.coords[0], self.nA.coords[1] , self.nB.coords[0], self.nB.coords[1]
		except:
			tkinter.messagebox.showerror("Error",
										 "Couldn't read link starting/end coordinates. Perhaps no nodes assigned?")
			return

		l = dist((x0, y0), (x1, y1))

		f0 = (1.0*l - self.nA.r)/l
		x0p = (1.0-f0)*x1 + f0*x0
		y0p = (1.0-f0)*y1 + f0*y0

		f1 = (1.0*l - self.nB.r)/l
		x1p = (1.0-f1)*x0 + f1*x1
		y1p = (1.0-f1)*y0 + f1*y1

		self.length = dist((x0p, y0p), (x1p, y1p))

		return x0p+self.coordOffset, y0p+self.coordOffset, x1p+self.coordOffset, y1p+self.coordOffset

	def initComment(self, text):
		self.comment = CommentBox(self, (self.x_mean, self.y_mean), text)
		self.hasComment = True

	def deleteComment(self, undo=False):
		if self.hasComment:
			self.comment.deleteComment(event=[])
			self.hasComment = False