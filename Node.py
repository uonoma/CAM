import itertools

from Comment import *
from header import *
from i18n import *
from PIL import ImageTk, Image, ImageGrab, ImageDraw
from Tooltip import *

class Node:

	root=[]
	canvas=[]

	# Default node radius
	std_r = 50
	r = 50
	fontSize = 8

	# Cursor position (needed for dragging)
	cursorPos=(0,0)
	dragInit=(0,0)
	dragFontInit=8

	def __init__(self, parentSheet, coords, data={}, diffTag="", comment=""):
		self.root=parentSheet.root
		self.canvas=parentSheet.canvas

		self.parentSheet = parentSheet

		if data=={}:
			# Assign new node index
			self.index=parentSheet.getNewIndex()
		else:
			# Read node index of existing node
			self.index=data['index']

		# Index of polygon-shaped node, -1 per default, is assigned only if applicable
		self.polygonIndex = -1

		# colour scheme
		self.cs = parentSheet.cs
		self.textColour = self.cs.darkText

		# False if text can be edited, true if read-only
		self.textDisabled = True
		self.readOnly = True


		# Valence and respective node shape
		self.valence = 0
		# border attributes according to valence
		self.border = parentSheet.border
		# 0: rectangle, 1: circle, 2: polygon
		self.shape = 0

		# Adjacent nodes sorted by pre/post
		self.neighbors = {'pre': [], 'post': []}

		# Indicates if node was deleted, added, or changed valence
		self.diffTag = diffTag

		# default border colour
		self.bcolour = self.cs.yellow

		# default fill colour
		self.fcolour = self.cs.fyellow

		# default border thickness
		self.thickness = 2

		# location on the screen
		self.coords=(coords[0], coords[1])
		self.loc=(1.0*coords[0]/self.root.winfo_width(), 1.0*coords[1]/self.root.winfo_height())

		# Node text & optional comment text
		self.text = ""
		self.commentText = comment

		# True if node was removed by click (not drawn on the screen but not removed from nodes list).
		self.removed = False

		if data != {}:
			self.text = data['text']

			try:
				self.valence = int(data['valence'])
			except:
				tkMessageBox.showwarning("Warning","Could not find \"valence\" key in map file %s. Using default."
										 %self.parentSheet.fileName)

			self.parseValence(fromFile=True)

			try:
				self.commentText = data['comment']
			except:
				pass

		if self.commentText == "":
			self.hasComment = False
		else:
			self.hasComment = True

	def initDrawing(self):
		self.reDraw(init=True)
		self.setBinds()

	def parseValence(self, fromFile=True, val=""):
		border = {'colour': 'yellow', 'thickness': 0}
		if fromFile:
			if self.valence == 0:
				self.shape = 0
				border = self.border.neutral
			elif self.valence == 1:
				self.shape = 1
				border = self.border.positive1
			elif self.valence == 2:
				border = self.border.positive2
				self.shape = 1
			elif self.valence == 3:
				border = self.border.positive3
				self.shape = 1
			elif self.valence == -1:
				border = self.border.negative1
				self.shape = 2
			elif self.valence == -2:
				border = self.border.negative2
				self.shape = 2
			elif self.valence == -3:
				border = self.border.negative3
				self.shape = 2
			elif self.valence == -99:
				border = self.border.ambivalent
				self.shape = 3
		else:
			if val == "0":
				self.shape = 0
				border = self.border.neutral
			elif val == "1":
				self.shape = 1
				border = self.border.positive1
			elif val == "2":
				border = self.border.positive2
				self.shape = 1
			elif val == "3":
				border = self.border.positive3
				self.shape = 1
			elif val == "-1":
				border = self.border.negative1
				self.shape = 2
			elif val == "-2":
				border = self.border.negative2
				self.shape = 2
			elif val == "-3":
				border = self.border.negative3
				self.shape = 2
			elif val == "-99":
				border = self.border.ambivalent
				self.shape = 3
			self.valence = int(val)
				
		self.thickness = border['thickness']
		self.colour = border['colour']
		self.colour1, self.colour2, self.colour3 = self.parseColours(self.colour)
		return

	def reDraw(self, init=False):
		canvasW=self.root.winfo_width()
		canvasH=self.root.winfo_height()

		r=self.r

		# center of circle
		x = 1.0*canvasW*self.loc[0]
		y = 1.0*canvasH*self.loc[1]
		self.coords=(x,y)

		''' 
		draw shapes of pre and post-nodes
		'''
		fontColour = self.cs.toHex(self.cs.darkText)

		# Polygon coordinates for small nodes (nodes present in pre-CAM and post-CAM)
		hexVertices_small = map(lambda i: \
							  (x - 20 + (self.r - 7) * math.cos(i * 2 * math.pi / 6),
							   y + 30 + (self.r - 7) * math.sin(i * 2 * math.pi / 6)),
						  [i for i in range(0, 6)])

		# Use "big" coordinates for post-CAM nodes
		hexVertices = map(lambda i: \
							  (x + (self.r) * math.cos(i * 2 * math.pi / 6),
							   y + (self.r) * math.sin(i * 2 * math.pi / 6)),
						  [i for i in range(0, 6)])
		x0p, y0p = x - r, y - r
		x1p, y1p = x + r, y + r

		# "Small" coordinates for shapes other than polygons, for pre-CAM nodes also present in post-CAM
		prePosRect_coords = (x0p - 20, y0p + 120, x0p + 60, y0p + 40)
		prePosCircle_coords = (x0p - 15, y0p + 125, x0p + 75, y0p + 35)

		# "Small" coordinates for shapes other than polygons, for pre-CAM nodes that were deleted in post-CAM

		if self.diffTag == "D":
			fontColour="dimgrey"
			hexVertices = map(lambda i: \
										(x + (self.r - 6) * math.cos(i * 2 * math.pi / 6),
										 y + (self.r - 6) * math.sin(i * 2 * math.pi / 6)),
									[i for i in range(0, 6)])
			if self.shape == 0:
				x0p, y0p, x1p, y1p = x - r * 0.9, y - r * 0.9, x + r * 0.9, y + r * 0.9
			elif self.shape == 1 or self.shape == 3:
				x0p, y0p, x1p, y1p = x - r * 0.9, y - r * 0.9, x + r * 0.9, y + r * 0.9

		if init:
			self.fill, self.outline = self.cs.toHex(self.colour2), self.cs.toHex(self.colour1)
			if self.diffTag == "D":
				self.fill = self.cs.toHex(self.colour3)
				self.outline = self.cs.toHex(self.colour2)

			# Draw small pre-nodes (for nodes present in pre- and post-CAM.)
			try:
				diffTag = int(self.diffTag)
				if int(diffTag) == 0:
					thickness = 2
					self.preIndex = self.canvas.create_rectangle(prePosRect_coords,
										fill=self.cs.toHex(self.cs.pyellow),
										outline=self.cs.toHex(self.cs.fyellow),
										activeoutline=self.cs.toHex(self.cs.fyellow),
										width=thickness, activewidth=thickness,
										tags="preRectangle")
				elif int(diffTag) < 0:
					thickness = int(diffTag) * (-2)
					if int(diffTag) == -99:
						thickness = 2
						pcolour = self.cs.ppurple
						fcolour = self.cs.fpurple
						self.preIndex = self.canvas.create_oval(prePosCircle_coords,
										fill=self.cs.toHex(pcolour),
										outline=self.cs.toHex(fcolour),
										activeoutline=self.cs.toHex(fcolour),
										width=thickness, activewidth=thickness,
										tags="circle")
					else:
						pcolour = self.cs.pred
						fcolour = self.cs.fred
					self.prePolygonIndex = self.canvas.create_polygon(*flatten(hexVertices_small), \
									fill=self.cs.toHex(pcolour),
									outline=self.cs.toHex(fcolour),
									activeoutline=self.cs.toHex(fcolour),
									width=thickness, activewidth=thickness,
									tags="hexagon")
				elif int(diffTag) > 0:
					thickness = int(diffTag)*2
					self.preIndex = self.canvas.create_oval(prePosCircle_coords,
									fill=self.cs.toHex(self.cs.pgreen),
									outline=self.cs.toHex(self.cs.fgreen),
									activeoutline=self.cs.toHex(self.cs.fgreen),
									width=thickness, activewidth=thickness,
									tags="circle")

			# Pass if diffTag is not an int value (node not present in pre-CAM)
			except:
				pass

			# Draw main nodes
			if self.shape == 0:
				self.shapeIndex = self.canvas.create_rectangle(x0p, y0p, x1p, y1p, fill=self.fill,
						outline=self.outline, activeoutline=self.outline,
						width=self.thickness, activewidth=self.thickness,
						tags="rectangle")
				self.polygonIndex = -1
			elif self.shape == 1:
				self.shapeIndex = self.canvas.create_oval(x0p, y0p, x1p, y1p, fill=self.fill,
						outline=self.outline, activeoutline=self.outline,
						width=self.thickness, activewidth=self.thickness,
						tags="circle")
				self.polygonIndex = -1
			elif self.shape == 2:
				self.shapeIndex = self.canvas.create_polygon(*flatten(hexVertices),\
					fill=self.fill, outline=self.outline, activeoutline=self.outline,\
					width=self.thickness, activewidth=self.thickness,tags="hexagon")
				self.polygonIndex = -1
			elif self.shape == 3:
				self.shapeIndex = self.canvas.create_oval(x0p, y0p, x1p, y1p, fill=self.fill,
						outline=self.outline, activeoutline=self.outline,
						width=self.thickness, activewidth=self.thickness,
						tags="circle")
				self.polygonIndex = self.canvas.create_polygon(*flatten(hexVertices),\
					fill=self.fill, outline=self.outline, activeoutline=self.outline,\
					width=self.thickness, activewidth=self.thickness,tags="hexagon")

		# Re-draw shapes with updated coordinates
		else:
			if self.shape == 0 or self.shape == 1:
				self.canvas.coords(self.shapeIndex, x0p, y0p, x1p, y1p)
			elif self.shape == 2:
				self.canvas.coords(self.shapeIndex, *flatten(hexVertices))
			elif self.shape == 3:
				self.canvas.coords(self.shapeIndex, x0p, y0p, x1p, y1p)
				self.canvas.coords(self.polygonIndex, *flatten(hexVertices))

			# Re-draw existing pre-shapes
			try:
				diffTag = int(self.diffTag)
				if diffTag < 0:
					if diffTag == -99:
						self.canvas.coords(self.preIndex, prePosCircle_coords)
					self.canvas.coords(self.prePolygonIndex,*flatten(hexVertices_small))
				elif diffTag > 0:
					self.canvas.coords(self.preIndex, prePosCircle_coords)
				elif diffTag == 0:
					self.canvas.coords(self.preIndex, prePosRect_coords)
			except:
				pass

		'''
		draw text box
		'''

		w = 10
		h = 2

		if init:
			self.tk_text = Text(self.root, bd=0, height=h,
				width=w, highlightthickness=0, wrap="word",
				font=(mainFont, int(self.fontSize), "normal"),
				bg=self.fill, fg=fontColour)

			if len(self.text) > 12:
				# Split long text in two lines to fit inside shape
				text1 = self.text[0:12]
				text2 = self.text[12:]
				self.tk_text.insert(END, text1)
				self.tk_text.insert(END, text2)
			else:
				self.tk_text.insert(END, self.text)
			if len(self.text) > 24:
				# Show tooltip with node text, if text too long to be displayed inside shape
				self.tooltip = CreateToolTip(self.tk_text, self.text)

			self.tk_text.tag_configure("center", justify='center')
			self.tk_text.tag_add("center", 1.0, "end")

			if self.readOnly:
				self.tk_text.config(state=DISABLED)

		tx0p, ty0p = x-r*0.7, y-r*0.3
		self.tk_text.place(x=tx0p, y=ty0p)
		self.tk_text.tag_configure("center", justify='center')

		if self.hasComment:
			self.comment.updatePos(self.coords)

	def setBinds(self):
		# Select on double-left click
		self.canvas.tag_bind(self.shapeIndex, '<Double-1>', self.selectToggle)
		if self.polygonIndex > -1:
			self.canvas.tag_bind(self.polygonIndex, '<Double-1>', self.selectToggle)

		# Drag circle/rectangle nodes to change location
		self.canvas.tag_bind(self.shapeIndex, '<Button-1>', self.startDrag)
		self.canvas.tag_bind(self.shapeIndex, '<ButtonRelease-1>', self.endDrag)
		self.canvas.tag_bind(self.shapeIndex, '<B1-Motion>', self.onLeftDrag)

		# Drag polygon nodes to change location
		if self.polygonIndex > -1:
			self.canvas.tag_bind(self.polygonIndex, '<Button-1>', self.startDrag)
			self.canvas.tag_bind(self.polygonIndex, '<ButtonRelease-1>', self.endDrag)
			self.canvas.tag_bind(self.polygonIndex, '<B1-Motion>', self.onLeftDrag)

		self.tk_text.bind('<Key>', self.resizeText)

	def addNeighbor(self, i1="", i2=""):
		if i1 != "":
			self.neighbors['pre'].append(i1)
		if i2 != "":
			self.neighbors['post'].append(i1)
		return

	def selectToggle(self, event=[]):
		if self.parentSheet.selectedNode != self.index:
			self.parentSheet.selectedNode = self.index
			# unselect all nodes
			for n in self.parentSheet.nodes:
				self.canvas.itemconfig(n.shapeIndex, outline=n.outline,
								   activeoutline=n.outline)
				if n.polygonIndex > -1:
					self.canvas.itemconfig(n.polygonIndex, outline= n.outline,
										   activeoutline=n.outline)
			# use highlight color for selected node
			self.canvas.itemconfig(self.shapeIndex, outline=self.cs.toHex(self.cs.highlight2),
								activeoutline=self.cs.toHex(self.cs.highlight2))
			if self.polygonIndex > -1:
				self.canvas.itemconfig(self.polygonIndex, outline=self.cs.toHex(self.cs.highlight2),
									   activeoutline=self.cs.toHex(self.cs.highlight2))
		else:
			self.parentSheet.selectedNode = -99
			self.canvas.itemconfig(self.shapeIndex, outline=self.outline,
								   activeoutline = self.outline)
			if self.polygonIndex > -1:
				self.canvas.itemconfig(self.polygonIndex, outline=self.outline,
									   activeoutline = self.outline)

	def disableText(self, event=[]):
		if not self.textDisabled:
			self.tk_text.config(state=DISABLED)
			self.textDisabled = True
			self.text = self.getText()

	def enableText(self, event=[]):
		if not self.readOnly and self.textDisabled == True:
			self.tk_text.config(state=NORMAL)
			self.textDisabled = False
		for n in self.parentSheet.nodes:
			if not n.index == self.index:
				n.disableText()

	def initComment(self):
		self.comment = CommentBox(self, self.coords, self.commentText)
		self.hasComment = True
		
	def startDrag(self, event):
		canvasW=1.0*self.root.winfo_width()
		canvasH=1.0*self.root.winfo_height()
		self.loc = (self.coords[0]/canvasW, self.coords[1]/canvasH)

		self.dragInit = (event.x, event.y)
		self.cursorPos = (event.x, event.y)
		self.dragFontInit = self.fontSize

		self.parentSheet.dragging = True

	def endDrag(self, event):
		self.parentSheet.dragging = False
		self.reDraw()
		self.root.update()

	def onLeftDrag(self, event):
		delta = (event.x - self.cursorPos[0], event.y - self.cursorPos[1])
		self.cursorPos = (event.x, event.y)
		self.moveBy(1.0*delta[0]/self.root.winfo_width(), 1.0*delta[1]/self.root.winfo_height())
		self.parentSheet.updateNodeEdges(self)
		return

	def onRightDrag(self, event):
		# calculate new radius
		center = self.coords
		curPos = (event.x, event.y)

		d = dist(center, curPos)

		self.r = d

		self.reDraw()

		self.parentSheet.updateNodeEdges(self)

	def updateText(self):
		self.text = self.tk_text.get("1.0", END).rstrip("\n\r")

	def resizeText(self, event):
		self.updateText()
		self.reDraw()

	def moveByPix(self, x, y):
		newX, newY = self.coords[0] + x, self.coords[1]+y

		pixelX=self.root.winfo_width()
		pixelY=self.root.winfo_height()

		self.loc = (1.0*newX/pixelX, 1.0*newY/pixelY)

		self.reDraw()

		self.parentSheet.updateNodeEdges(self)

	def moveBy(self, x, y):
		newX = self.loc[0]+x #max(min(self.loc[0]+x, 1), 0)
		newY = self.loc[1]+y #max(min(self.loc[1]+y, 1), 0)
		
		self.loc = (newX, newY)

		self.reDraw()

	def moveTo(self, x, y):
		# must provide normalized coords (0-1)
		self.moveBy((x - self.loc[0], y - self.loc[1]))

	def removeByClick(self):
		self.removed = True
		self.remove()

	def remove(self, event=[]):
		self.canvas.delete(self.shapeIndex)

		if self.polygonIndex > -1:
			self.canvas.delete(self.polygonIndex)

		self.tk_text.destroy()

		if self.hasComment:
			self.comment.deleteComment(event)
		self.parentSheet.removeNode(self.index)

		try:
			diffTag = int(self.diffTag)

			if diffTag >= 0:
				if self.preIndex > -1:
					self.canvas.delete(self.preIndex)
			if diffTag < 0:
				if self.prePolygonIndex > -1:
					self.canvas.delete(self.prePolygonIndex)
		except:
			pass


	def deleteComment(self, undo=False):
		if self.hasComment:
			self.parentSheet.lastAddedNode = -1
			self.parentSheet.lastAddedLink = ()
			self.parentSheet.lastDeletedLinks = []
			self.parentSheet.lastDeletedLink = {}
			if undo:
				self.parentSheet.onlyComment = 0
				self.parentSheet.lastDeletedNode = {}
			else:
				self.parentSheet.onlyComment = 1
				self.comment.updateText(event=[])
				data = {'index': self.index,
					'coords': self.coords, 'radius': self.r, 'text': self.text,
                	'valence': self.valence, 'read-only': self.readOnly,
					'comment': self.commentText}
				self.parentSheet.lastDeletedNode = data
				self.parentSheet.menu.undoBtn.button.config(state="normal")
			self.comment.deleteComment(event=[])

	def getText(self):
		text = self.tk_text.get("0.0",END)
		text = text.strip()
		return text

	def grow(self, max_r=50, stage=0):
		if self.parentSheet.fastGraphics: return

		total_stages=10#max_r/3

		if stage<=total_stages:
			self.reDraw(r=1.0*max_r*stage / total_stages)

		self.root.update()

		if stage < total_stages:
			#t = threading.Timer(0.01, self.grow, [max_r, stage+1])
			#t.daemon = True
			#t.start()
			time.sleep(0.005)
			self.grow(max_r, stage+1)


	def parseColours(self, string):
		bcolour = self.cs.yellow
		fcolour = self.cs.fyellow
		fcolour_pre = self.cs.pyellow
		if string == "yellow":
			bcolour = self.cs.yellow
			fcolour = self.cs.fyellow
			fcolour_pre = self.cs.pyellow
		elif string == "red":
			bcolour = self.cs.red
			fcolour = self.cs.fred
			fcolour_pre = self.cs.pred
		elif string == "green":
			bcolour = self.cs.green
			fcolour = self.cs.fgreen
			fcolour_pre = self.cs.pgreen
		elif string == "purple":
			bcolour = self.cs.purple
			fcolour = self.cs.fpurple
			fcolour_pre = self.cs.ppurple
		return bcolour, fcolour, fcolour_pre

def split2(string):
	# return list of words with start and end indices of each
	words = []

	inWord=False
	start = 0
	end = 0
	for i in range(len(string)):

		if not inWord and string[i] != ' ':
			inWord = True
			start = i
			end = 0
		elif inWord and not string[i] != ' ':
			inWord = False
			end = i
			words.append([string[start:end], start, end])
		elif inWord and i == len(string)-1:
			end = i+1
			words.append([string[start:end], start, end])

	return words

def flatten(listoftuples):
	return list(itertools.chain.from_iterable(listoftuples))