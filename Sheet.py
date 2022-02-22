# -*- coding: utf-8 -*-

import os
import csv
import cv2
import json
import numpy
import zipfile
from io import StringIO
from header import *
from Node import *
from Link import *
from Menu import *
from Colours import *
from Border import *
from tkinter import filedialog
from random import choice, randint
from PIL import ImageGrab

class Sheet:

	sheet = None

	cursorPos=(0,0)
	dragInit=(0,0) 

	# Node indices to current link
	linkA, linkB = -1,-1

	activeNode = -1

	dragging = False

	def __init__(self, root, canvas, fileName):
		self.root=root
		self.canvas=canvas

		for i in range(0,3):
			self.root.columnconfigure(i, weight=1)
		self.root.rowconfigure(1, weight=1)

		# pre-defined colours
		self.cs=ColourScheme()

		# pre-defined node borders
		self.border=Border()

		self.fileOpen = False

		# Delete currently selected node on <Delete>
		self.canvas.bind_all('<Delete>', self.deleteSelected)

		# Update radius of selected node on up/down key
		self.canvas.bind_all('<Up>', lambda x: self.updateNodeRadius(1))
		self.canvas.bind_all('<Down>', lambda x: self.updateNodeRadius(-1))

		# drag nodes on mouse click/release
		self.canvas.bind('<Button-1>', self.startDrag)
		self.canvas.bind('<B1-Motion>', self.onDrag)
		self.canvas.bind('<ButtonRelease-1>', self.endNodeDrag)

		# save sheet on Ctrl + S
		self.root.bind('<Control-Key-s>', self.saveFileAs)

		# delete node on double right click
		self.canvas.bind('<ButtonRelease-1>', self.endNodeDrag)

		# set default background colour
		self.canvas.configure(bg=self.cs.toHex(self.cs.background))

		# keep track of most recently assigned index (first node=1)
		self.curIndex=1

		# name of current sheet file
		self.fileName=fileName

		self.imageList=[]

		self.root.update()
		
		self.resize()

		self.nodes = []
		self.links = []

		# Index of currently selected node. -99 per default (no selected node)
		self.selectedNode = -99

		# Tuple of indices of currently selected link. () per default (no link selected)
		self.selectedLink = ()

		# Adjacent nodes dictionaries
		self.neighborsPre = {}
		self.neighborsPost = {}

		self.menu = MainMenu(self)
		self.menu.initMenu()

	def startDrag(self, event):
		# start dragging a node on left mouse button click
		self.dragInit = (event.x, event.y)
		self.cursorPos = (event.x, event.y)

	def endNodeDrag(self, event):
		# stop dragging node on left mouse button release
		self.dragging = False
		self.root.update()

	def locInNode(self, event):
		# return index of the node at the current cursor position, or -1 if
		# there is no node
		ind = -1
		for t in self.nodes:
			coords = t.coords
			if (event.x - coords[0])**2 + (event.y - coords[1])**2 < t.r**2:
				ind = t.index
		return ind
	
	def locInLink(self, event):
		index = (-1, -1)
		for l in self.links:
			[x_0, y_0, x_1, y_1] = l.canvas.coords(l.lineIndex)
			slope_line = round((y_1-y_0)/(x_1-x_0), 1)
			slope_atCursorPos = round((event.y - y_0)/(event.x - x_0), 1)
			if slope_atCursorPos - 1 <= slope_line and slope_line <= slope_atCursorPos + 1:
				return (l.nA.index, l.nB.index)
		return index

	def updateCurIndex(self):
		indices = []
		for n in self.nodes:
			indices.append(n.index)
		self.curIndex = max(indices)

	def onDrag(self, event):
		if not self.dragging:
			# move all canvas objects
			delta = (event.x - self.cursorPos[0], event.y - self.cursorPos[1])

			self.cursorPos = (event.x, event.y)

			for t in self.nodes:
				t.moveByPix(delta[0],delta[1])
			for l in self.links:
				l.updateLine()

	def deleteSelected(self, event=[]):
		if not self.selectedNode == -99:
			n = self.getNodeByIndex(self.selectedNode)
			n.removeByClick()
		if not self.selectedLink == ():
			l = self.getLinkByIndex(self.selectedLink[0], self.selectedLink[1])
			l.removeByClick()

	def updateNodeRadius(self, add, event=[]):
		if not self.selectedNode == -99:
			n = self.getNodeByIndex(self.selectedNode)
			if n.r + add < 0:
				return
			n.r += add
			n.reDraw()
			self.updateNodeEdges(n)

	def resetNodeSizes(self, event=[]):
		for n in self.nodes:
			n.r = n.std_r
			n.reDraw()

	def openJSON(self):
		"""
		Open a JSON file.
		"""
		if self.fileOpen:
			if tkinter.messagebox.askyesno(SAVESTR, ASKSAVESTR):
				self.saveFileAs()
			self.closeFile()

		fileName = tkinter.filedialog.askopenfilename(initialdir = FILEDIR,title =
			SELECTFILESTR,filetypes = [("CAMEL file","*.txt")])

		with open(fileName) as file:
			try:
				data = json.load(file)
				self.fileOpen = True
				return data
			except:
				messagebox.showerror("Reading error", "File doesn't contain a valid JSON string.")
				return {}

	def parseCAMFromJson(self):
		"""
		Open and draw a CAM file serialized in JSON format, created by CAMEL.
		"""
		data = self.openJSON()
		try:
			nodesList=data['nodes']
			linksList = data['connectors']
			for n in nodesList:
				id = n['id']
				title = n['text']
				valence = n['value']
				x = n['position']['x']
				y = n['position']['y']
				self.addNode((x, y), data={'index': id, 'valence': valence, 'text': title, 'radius': 50,
										'coords': [x, y], 'read-only':1, 'acceptance': False}, draw=True)
			for c in linksList:
				self.linkA = c['motherID']
				self.linkB = c['daughterID']

				### TODO: Is this interpretation correct? ###
				strength = c['intensity']/3
				bidir = 0 if c['isBidirectional'] == "False" else 1
				self.addLink(directed=bidir, strength=strength, comment="",
							 draw=True)
		except DecodeError:
			messagebox.showerror("Decode error", "Not a valid JSON CAM.")

	def createDiffCAMFromZippedCSVs(self):
		""""""
		'''
        Open pre-CAM archive
        '''
		cam1, cam2 = self.openFilesForDiff()
		archive1 = zipfile.ZipFile(cam1, 'r')
		names1 = archive1.namelist()
		names1.sort()
		nodesFile1 = ""
		linksFile1 = ""
		for n in names1:
			if n.endswith("blocks.csv"):
				nodesFile1 = archive1.open(n)
			elif n.endswith("links.csv"):
				linksFile1 = archive1.open(n)

		'''
		Open post-CAM archive
		'''
		archive2 = zipfile.ZipFile(cam2, 'r')
		names2 = archive2.namelist()
		nodesFile2 = ""
		linksFile2 = ""
		for n in names2:
			if n.endswith("blocks.csv"):
				nodesFile2 = archive2.open(n)
			elif n.endswith("links.csv"):
				linksFile2 = archive2.open(n)

		'''
		Read nodes from blocks.csv (pre-CAM)
        '''
		nodes1 = StringIO(nodesFile1.read().decode('utf-8'))
		nodesReader1 = csv.DictReader(nodes1, delimiter=',')
		nodesData1 = self.readNodesDataFromCSV(list(nodesReader1))

		'''
		Read nodes from blocks.csv (post-CAM)
		'''
		nodes2 = StringIO(nodesFile2.read().decode('utf-8'))
		nodesReader2 = csv.DictReader(nodes2, delimiter=',')
		nodesData2 = self.readNodesDataFromCSV(list(nodesReader2))

		'''
		Create diff-CAM nodes
		'''
		pixelX = self.root.winfo_width()
		pixelY = self.root.winfo_height()
		for (t1, (i1, v1)) in nodesData1.items():
			# Node both in pre and post CAM
			if t1 in nodesData2:
				diffVal = nodesData2[t1][1]
				diffTag = str(v1)
				# Draw deleted nodes in middle third of the window
				rand_y = randint(int((pixelY-150)/3), int((pixelY-150)*2/3))
			# Node deleted in post CAM
			else:
				diffVal = v1
				diffTag = "D"
				# Draw deleted nodes in lower third of the window
				rand_y = randint(int((pixelY - 150)*2/3), pixelY - 150)
			rand_x = randint(10, pixelX - 300)
			self.addNode((rand_x, rand_y), data={'index': self.getNewIndex(), 'valence': diffVal,
												 'text': t1 , 'radius': 50, 'coords': [rand_x, rand_y],
												 'read-only': 1, 'acceptance': False}, diffTag=diffTag, draw=True)

		for (t2, (i2, v2)) in nodesData2.items():
			# New node added in post CAM:
			if t2 not in nodesData1:
				diffVal = v2
				diffTag = "A"
				rand_y = randint(100, int((pixelY - 150) / 3))
				# Draw added nodes in upper third of the window
				rand_x = randint(10, pixelX - 300)
				self.addNode((rand_x, rand_y), data={'index': self.getNewIndex(), 'valence': diffVal,
													 'text': t2 , 'radius': 50, 'coords': [rand_x, rand_y],
													 'read-only': 1, 'acceptance': False}, diffTag=diffTag, draw=True)


		''' 
		Read links from links.csv (pre-CAM)
		'''
		links1 = StringIO(linksFile1.read().decode('utf-8'))
		linksReader1 = csv.DictReader(links1, delimiter=',')
		linksData1 = self.readLinksDataFromCSV(list(linksReader1), nodesData1)

		'''
        Read links from links.csv (post-CAM)
        '''
		links2 = StringIO(linksFile2.read().decode('utf-8'))
		linksReader2 = csv.DictReader(links2, delimiter=',')
		linksData2 =  self.readLinksDataFromCSV(list(linksReader2), nodesData2)

		'''
		Create diff-CAM links
		'''
		for (k,v) in linksData1.items():
			if k in linksData2:
				strength = linksData2[k]
				diffTag = v
			else:
				strength = v
				diffTag ="D"
			self.linkA = k[0]
			self.linkB = k[1]
			self.addLink(directed=k[2], strength=strength, comment="",
						 draw=True, diffTag=diffTag)

		for (k,v) in linksData2.items():
				if not k in linksData1:
					strength = v
					diffTag = "A"
					self.linkA = k[0]
					self.linkB = k[1]
					self.addLink(directed=k[2], strength=strength, comment="",
						draw=True, diffTag=diffTag)

		''' 
		Calculate statistics 
		'''

		# Statistics dictionaries for pre- and post-CAMs
		preNodes = {}
		postNodes = {}

		# Number of nodes, total & sorted by valence
		preNodes['total number'] = 0
		preNodes['positives number'] = 0
		preNodes['negatives number'] = 0
		preNodes['neutrals number'] = 0
		preNodes['ambivalents number'] = 0
		# Mean valence
		preNodes['AVG valence'] = 0
		# Standard deviation
		preNodes['SD valence'] = 0

		# Same for post-CAM
		postNodes['total number'] = 0
		postNodes['positives number'] = 0
		postNodes['negatives number'] = 0
		postNodes['neutrals number'] = 0
		postNodes['ambivalents number'] = 0
		postNodes['AVG valence'] = 0
		postNodes['SD valence'] = 0

		# Dictionary keys: 'total', 'pos', 'neg'
		preLinks = {}
		preLinks['total number'] = 0
		preLinks['positives number'] = 0
		preLinks['negatives number'] = 0

		postLinks = {}
		postLinks['total number'] = 0
		postLinks['positives number'] = 0
		postLinks['negatives number'] = 0

		# Calculate statistical parameters & fill dictionaries
		for (_, (_,v)) in nodesData1.items():
			preNodes['total number'] = preNodes['total number'] + 1
			# For calculation of mean: Use 0 as valence for ambivalent nodes (instead of -99)
			if v == -99:
				v0 = 0
			else:
				v0 = v
			preNodes['AVG valence'] += v0

		preNodes['AVG valence'] = preNodes['AVG valence'] / preNodes['total number']

		squaredDiff = 0
		for (_, (_, v)) in nodesData1.items():
			if int(v) > 0:
				preNodes['positives number'] = preNodes['positives number'] + 1
			elif int(v) < 0 and int(v) > -99:
				preNodes['negatives number'] = preNodes['negatives number'] + 1
			elif int(v) == 0:
				preNodes['neutrals number'] = preNodes['neutrals number'] + 1
			elif int(v) == -99:
				preNodes['ambivalents number'] = preNodes['ambivalents number'] + 1

			# For calculation of SD: Use 0 as valence for ambivalent nodes (instead of -99)
			if int(v) == -99:
				v0 = 0
			else:
				v0 = int(v)
			squaredDiff += (v0 - preNodes['AVG valence']) ** 2

		preNodes['SD valence'] = math.sqrt(squaredDiff / (preNodes['total number'] - 1))

		# Calculate average degree
		degreeSum = 0
		for (t, (_, v)) in nodesData1.items():
			degree = 0
			# If node is connected to neighbor nodes calculate degree
			try:
				neighbors = self.neighborsPre[t]
				degree = len(neighbors)
			except:
				pass
			finally:
				degreeSum += degree
		meanDegreePre = degreeSum / len(nodesData1)

		# Link no in pre-CAM
		for (_, s) in linksData1.items():
			preLinks['total number'] = preLinks['total number'] + 1
			if s > 0:
				preLinks['positives number'] = preLinks['positives number'] + 1
			else:
				preLinks['negatives number'] = preLinks['negatives number'] + 1

		# Calculate density
		preDensity = preLinks['total number']/binomial(preNodes['total number'], 2)

		'''
		Same for post-CAM
		'''
		for (t, (_, v)) in nodesData2.items():
			postNodes['total number'] = postNodes['total number'] + 1
			if v == -99:
				v0 = 0
			else:
				v0 = v
			postNodes['AVG valence'] += v0

		postNodes['AVG valence'] = postNodes['AVG valence'] / postNodes['total number']

		squaredDiff = 0

		for (_, (_, v)) in nodesData2.items():
			if int(v) > 0:
				postNodes['positives number'] = postNodes['positives number'] + 1
			elif int(v) < 0 and int(v) > -99:
				postNodes['negatives number'] = postNodes['negatives number'] + 1
			elif int(v) == 0:
				postNodes['neutrals number'] = postNodes['neutrals number'] + 1
			elif int(v) == -99:
				postNodes['ambivalents number'] = postNodes['ambivalents number'] + 1

			if int(v) == -99:
				v0 = 0
			else:
				v0 = int(v)
			squaredDiff += (v0 - postNodes['AVG valence']) ** 2

		postNodes['SD valence'] = math.sqrt(squaredDiff / (postNodes['total number'] - 1))

		degreeSum = 0
		for (t, (_, v)) in nodesData2.items():
			degree = 0
			# If node has connected neighbor nodes calculate degree.
			try:
				neighbors = self.neighborsPost[t]
				degree = len(neighbors)
			except:
				pass
			finally:
				degreeSum += degree
		meanDegreePost = degreeSum / len(nodesData2)

		# Link no in post-CAM
		for (_, s) in linksData2.items():
			postLinks['total number'] = postLinks['total number'] + 1
			if s > 0:
				postLinks['positives number'] = postLinks['positives number'] + 1
			else:
				postLinks['negatives number'] = postLinks['negatives number'] + 1

		# Calculate density
		postDensity = postLinks['total number']/binomial(postNodes['total number'], 2)

		'''
		Create statistics table
		'''
		# Toplevel window for statistics table
		self.top = tkinter.Toplevel()
		self.top.title("Statistics")
		self.top.geometry("800x400")
		self.top.protocol("WM_DELETE_WINDOW", passEvent)

		#### PRE-CAM STATISTICS	####

		# Number fields
		pairs1 = {k: preNodes[k] for k in list(preNodes)[:5]}
		# Aggregate fields
		pairs2 = {k: preNodes[k] for k in list(preNodes)[-2:]}

		row = 0

		e = Entry(self.top, relief=SOLID, bg="cyan")
		e.grid(row=row, column=0, sticky=NSEW)
		e.insert(END, "PRE-CAM: NODES")

		for (k,v) in pairs1.items():
			row += 1
			# First column: field name
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=0, sticky=NSEW)
			e.insert(END, k)
			# Second column: value
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=1, sticky=NSEW)
			e.insert(END, v)
		for (k,v) in pairs2.items():
			row += 1
			# First column: field name
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=0, sticky=NSEW)
			e.insert(END, k)
			# Second column: value
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=1, sticky=NSEW)
			# Round aggregate values to 2 decimals
			e.insert(END, round(v, 2))

		# PRE-CAM: Average degree
		row += 1
		# First column: field name
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=0, ipadx=60, sticky=NSEW)
		e.insert(END, "AVG degree")
		# Second column: value
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=1, sticky=NSEW)
		e.insert(END, round(meanDegreePre, 2))

		# PRE-CAM: LINKS
		row += 1
		e = Entry(self.top, relief=SOLID, bg="cyan")
		e.grid(row=row, column=0, ipadx=25, sticky=NSEW)
		e.insert(END, "PRE-CAM: LINKS")

		for (k,v) in preLinks.items():
			row += 1
			# First column: field name
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=0, sticky=NSEW)
			e.insert(END, k)
			# Second column: value
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=1, sticky=NSEW)
			# Round aggregate values to 2 decimals
			e.insert(END, round(v, 2))

		row += 1
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=0, ipadx=25, sticky=NSEW)
		e.insert(END, "density")
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=1, ipadx=25, sticky=NSEW)
		e.insert(END, round(preDensity, 2))

		#### POST-CAM STATISTICS	####

		# Number fields
		pairs1 = {k: postNodes[k] for k in list(postNodes)[:5]}
		# Aggregate fields
		pairs2 = {k: postNodes[k] for k in list(postNodes)[-2:]}

		row = 0
		e = Entry(self.top, relief=SOLID, bg="cyan")
		e.grid(row=row, column=2, sticky=NSEW)
		e.insert(END, "POST-CAM: NODES")

		for (k,v) in pairs1.items():
			row += 1
			# First column: field name
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=2, sticky=NSEW)
			e.insert(END, k)
			# Second column: value
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=3, sticky=NSEW)
			e.insert(END, v)
		for (k,v) in pairs2.items():
			row += 1
			# First column: field name
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=2, sticky=NSEW)
			e.insert(END, k)
			# Second column: value
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=3, sticky=NSEW)
			# Round aggregate values to 2 decimals
			e.insert(END, round(v, 2))

		# Post-CAM average degree
		row += 1
		# First column: field name
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=2, ipadx=60, sticky=NSEW)
		e.insert(END, "AVG degree")
		# Second column: value
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=3, sticky=NSEW)
		e.insert(END, round(meanDegreePost, 2))

		# POST-CAM: LINKS
		row += 1
		e = Entry(self.top, relief=SOLID, bg="cyan")
		e.grid(row=row, column=2, ipadx=25, sticky=NSEW)
		e.insert(END, "POST-CAM: LINKS")

		for (k,v) in postLinks.items():
			row += 1
			# First column: field name
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=2, sticky=NSEW)
			e.insert(END, k)
			# Second column: value
			e = Entry(self.top, relief=GROOVE)
			e.grid(row=row, column=3, sticky=NSEW)
			# Round aggregate values to 2 decimals
			e.insert(END, round(v, 2))

		row += 1
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=2, ipadx=25, sticky=NSEW)
		e.insert(END, "density")
		e = Entry(self.top, relief=GROOVE)
		e.grid(row=row, column=3, ipadx=25, sticky=NSEW)
		e.insert(END, round(postDensity, 2))
		self.top.mainloop()

	def lookupNodeIndex(self, text):
		for n in self.nodes:
			pureText=n.text.split(': ', 1)[0]
			if text == pureText:
				return n.index
		return 1

	def allIndices(self):
		indices = [n.index for n in self.nodes]
		return indices

	def getIndex(self, text):
		for n in self.nodes:
			if n.text == text:
				return n.index

	def exportAsCsv(self):
		delim = ';'
		fnBaseLong, fnExt = os.path.splitext(self.filename)[0], os.path.splitext(self.filename)[1]
		fnBase = os.path.basename(fnBaseLong)
		nodesFileName = fnBaseLong + "_blocks" + fnExt
		csvFileNodes = open(nodesFileName, mode = 'w+',  newline='')
		csvWriterNodes = csv.writer(csvFileNodes, delimiter=delim, quoting=csv.QUOTE_NONE,
			escapechar='\\')
		csvWriterNodes.writerow(CSVFIELDS_NODES_V4)

		for n in self.nodes:
			val = self.parseValence(n.valence)

			# Add fields for pre-/post-CAM valence
			if n.diffTag == "A":
				val_post = val
				val_pre = ""
			elif n.diffTag == "D":
				val_pre = val
				val_post = ""
			else:
				try:
					val_pre_int = int(n.diffTag)
					val_pre = self.parseValence(val_pre_int)
					val_post = val
				except:
					val_pre = ""
					val_post = ""

			r = [n.index, n.text, n.coords[0], n.coords[1], 2*n.r, 2*n.r, val, 0, n.index, "", "", 1, fnBase,
				 val_pre, val_post, n.removed]
			csvWriterNodes.writerow(r)

		linksFileName = fnBaseLong + "_links" + fnExt
		csvFileLinks = open(linksFileName, mode='w+', newline='')
		csvWriterLinks = csv.writer(csvFileLinks, delimiter=delim, quoting=csv.QUOTE_NONE,
									escapechar='\\')
		csvWriterLinks.writerow(CSVFIELDS_LINKS_V3)

		i = 0
		for l in self.links:
			if l.strength == 3:
				strength = "Solid-Strong"
			elif l.strength == 2:
				strength = "Solid"
			elif l.strength == 1:
				strength = "Solid-Weak"
			elif l.strength == -1:
				strength = "Dashed-Weak"
			elif l.strength == -2:
				strength = "Dashed"
			elif l.strength == -3:
				strength = "Dashed-Strong"

			if l.directed == 1:
				dir = "uni"
			elif l.directed == 0:
				dir = "none"

			if l.diffTag == "A":
				strength_post = strength
				strength_pre = ""
			elif l.diffTag == "D":
				strength_pre = strength
				strength_post = ""
			else:
				try:
					strength_pre_int = int(n.diffTag)
					strength_pre = self.parseStrength(strength_pre_int)
					strength_post = strength
				except:
					strength_pre = ""
					strength_post = ""

		#	CSVFIELDS_LINKS_V3 = ['id', 'starting_block', 'ending_block', 'line_style', 'creator', 'num', 'arrow_type',
		#						  'timestamp', 'CAM', 'strength_pre', 'strength_post', 'deleted_by_user']
			r = [i, l.nA.index, l.nB.index, strength, "", i, dir, "", fnBase, strength_pre, strength_post, l.removed]
			csvWriterLinks.writerow(r)
			i = i + 1

	def readNodesDataFromCSV(self, nodesReader):

	#   DEPRECATED:
	#   Check for older versions.
	#	Versions with node id referred to as "id" are not supported anymore.

	#	firstLnNodes = next(nodesReader)

	#	version = 0

	# Check if .csv header format corresponds to first two Empathica versions, in which case index field name
	# is different from later versions
	#if firstLnNodes == CSVFIELDS_NODES_V1:
	#	version = 1
	#elif firstLnNodes == CSVFIELDS_NODES_V2:
	#	version = 2
	#if version == 1 or 2:
	#	idKey = 'id'
	#else:
	#	idKey = 'num'

		nodesData = {}

		for row in nodesReader:
			# Read node index
			index = float(row['id'])

			# Read & parse node valence
			valenceName = row['shape']
			valence = 0
			if valenceName == "neutral":
				valence = 0
			elif valenceName == "negative weak":
				valence = -1
			elif valenceName == "negative":
				valence = -2
			elif valenceName == "negative strong":
				valence = -3
			elif valenceName == "positive weak":
				valence = 1
			elif valenceName == "positive":
				valence = 2
			elif valenceName == "positive strong":
				valence = 3
			elif valenceName == "ambivalent":
				valence = -99

			# Read node text
			text = row['title']

			nodesData.update({text: (index, valence)})

		return nodesData

	def readLinksDataFromCSV(self, linksReader, nodesData):
		linksData = {}
		for row in linksReader:
			strength = 0
			if row['arrow_type'] == "uni":
				directed = 1
			else:
				directed = 0

			# Parse link strength
			if row['line_style'] == "Solid-Strong":
				strength = 3
			elif row['line_style'] == "Solid":
				strength = 2
			elif row['line_style'] == "Solid-Weak":
				strength = 1
			elif row['line_style'] == "Dashed-Strong":
				strength = -3
			elif row['line_style'] == "Dashed":
				strength = -2
			elif row['line_style'] == "Dashed-Weak":
				strength = -1

			startingNodeIndex = None
			endNodeIndex = None

			startingNodeText =""
			endNodeText = ""

			for (t, (i, v)) in nodesData.items():
				if float(row['starting_block']) == i:
					startingNodeText = t
					startingNodeIndex = self.lookupNodeIndex(startingNodeText)
				elif float(row['ending_block']) == i:
					endNodeText = t
					endNodeIndex = self.lookupNodeIndex(endNodeText)

			linksData.update({(startingNodeIndex, endNodeIndex, directed): strength})

			# Update node neighbors

			self.getNodeByText(startingNodeText).addNeighbor(i1=endNodeText)
			self.getNodeByText(endNodeText).addNeighbor(i1=startingNodeText)

			if self.neighborsPre.get(startingNodeText) is None:
				self.neighborsPre[startingNodeText] = [endNodeText]
			else:
				self.neighborsPre[startingNodeText].append(endNodeText)

			if self.neighborsPre.get(endNodeText) is None:
				self.neighborsPre[endNodeText] = [startingNodeText]
			else:
				self.neighborsPre[endNodeText].append(startingNodeText)

		return linksData

	def exportToPng(self):
		x=self.root.winfo_rootx()+self.canvas.winfo_x()
		y=self.root.winfo_rooty()+self.canvas.winfo_y()
		x1=x+self.canvas.winfo_width()
		y1=y+self.canvas.winfo_height()
		# minimize statistics window before capturing canvas
		self.top.withdraw()
		fileString = tkinter.filedialog.asksaveasfilename(initialdir=FILEDIR, defaultextension=".png",
														  filetypes=[("All Files", "*.*"), ("PNG files", "*.png")])
		# Capture canvas and save to .png
		ImageGrab.grab().crop((x,y,x1,y1)).save(fileString)
		# restore statistics window
		self.top.deiconify()

	def openFilesForDiff(self):
		if self.fileOpen:
			if tkinter.messagebox.askyesno(SAVESTR, ASKSAVESTR):
				self.saveFileAs()
			self.closeFile()

		fileNamePre = tkinter.filedialog.askopenfilename(initialdir = FILEDIR,title =
			SELECTPREFILESTR,filetypes = [("Empathica/Valence CAM","*.zip")])
		fileNamePost = tkinter.filedialog.askopenfilename(initialdir = FILEDIR,title =
			SELECTPOSTFILESTR,filetypes = [("Empathica/Valence CAM","*.zip")])

		# don't proceed if no two files were selected
		if fileNamePre == "" or fileNamePost == "":
			return

		self.fileOpen = True
		return fileNamePre, fileNamePost

	def reInitNodes(self):
		for n in self.nodes:
			n.canvas.delete(n.shapeIndex)
			n.tk_text.destroy()
			n.initDrawing()

	def closeFile(self, drawn=True):
		if drawn:
			for node in self.nodes:
				node.remove()
			self.closeStatistics()
			self.canvas.delete("all")
			self.fileOpen = False
			self.curIndex = 1
			self.fileName = ""
		self.nodes = []
		self.links = []

	def saveFileAs(self):
		self.filename = tkinter.filedialog.asksaveasfilename(initialdir =
					FILEDIR,title = SELECTFILESTR, defaultextension=".csv", filetypes =
					(("CSV "+ FILESSTR,"*.csv"),(ALLFILESSTR,"*.*")))
		if self.fileName != "":
			self.exportAsCsv()

	def nodeDist(self, nA, nB):
		return dist(nA.coords, nB.coords)

	def resize(self, event=[]):
		pixelX=self.root.winfo_screenwidth()
		pixelY=self.root.winfo_screenheight()
		self.root.geometry("%dx%d+0+0" % (pixelX, pixelY))

		canvasW = pixelX
		canvasH = pixelY-0

		self.canvas.place(x=0, y=0, width=canvasW, height=canvasH)

	def unselectNodes(self):
		for n in self.nodes:
			n.unselect(event=[])

	def unselectLinks(self):
		for l in self.links:
			l.unselect(event=[])

	def addNode(self, coords, data={}, draw=False, diffTag=""):
		for n in self.nodes:
			n.disableText()
		node = Node(self, coords, data, diffTag=diffTag)
		if draw == True:
			node.initDrawing()
		node.enableText()
		self.nodes.append(node)
		return node.index

	def removeNode(self, index):
		n = self.getNodeByIndex(index)

		# remove all links connected to node
		ls = len(self.links)
		for i in range(ls):
			l = self.links[ls - i - 1]
			if l.nA == n or l.nB == n:
				self.links.remove(l)
				l.remove()

	def removeLink(self, nA, nB):
		# remove link associated with nA and nB
		for l in self.links:
			if l.nA.index == nA and l.nB.index == nB or l.nA.index == nB and l.nB.index == nA:
				self.links.remove(l)
				l.remove()
				break

	def getNewIndex(self):
		self.curIndex += 1
		return self.curIndex

	def addLink(self, directed, strength, label="", comment="",
				draw=False, diffTag=""):
		nA = self.linkA
		nB = self.linkB

		if nA == -1 or nB == -1:
			tkinter.messagebox.showerror("Error",
										 "A link end was not assigned")
			return

		if nA != nB:
			if self.hasLink(nA, nB):
				offset = min(self.getNodeByIndex(nB).r, self.getNodeByIndex(nA).r)/2
			else:
				offset = 0
			self.links.append(Link(self, self.getNodeByIndex(nA), self.getNodeByIndex(nB),
			directed, strength, label, coordOffset=offset,
			comment=comment, draw=draw, diffTag=diffTag))

		TA = self.getNodeByIndex(nA)
		TA.canvas.itemconfig(TA.index)
		
		# reset link assignments
		self.resetLinkData()

	def getNodeByIndex(self, index):
		for n1 in self.nodes:
			if n1.index == index:
				return n1

	def getNodeByText(self, text):
		for n in self.nodes:
			if n.text == text:
				return n

	def getLinkByIndex(self, indexA, indexB):
		nodeA = self.getNodeByIndex(indexA)
		nodeB = self.getNodeByIndex(indexB)
		for l in self.links:
			if (nodeA == l.nA and nodeB == l.nB):
				return l

	def updateNodeEdges(self, node):
		for l in self.links:
	
			if node == l.nA or node == l.nB:
			
				l.updateLine()		

	def hasLink(self, nA, nB):

		TA = self.getNodeByIndex(nA)
		TB = self.getNodeByIndex(nB)

		for l in self.links:

			if (l.nA == TA and l.nB==TB) or (l.nA == TB and l.nB==TA):
				return True
		return False

	def resetLinkData(self):
		self.linkA = -1
		self.linkB = -1
		self.linkImportance=-1

	def lookupNodeTexts(self, nlist, llist):
		linksWithTexts = []
		for l in llist:
			ltextA = ""
			ltextB = ""
			for n in nlist:
				if n.index == l.nA:
					ltextA = n.text
				elif n.index == l.nB:
					ltextB = n.text
			linksWithTexts.append({(ltextA, ltextB): l})
		return linksWithTexts

	def openInfoBox(self, text):
		self.infobox.config(text=text)
		self.sidebar.grid(row=2, column=3, sticky='e')
		self.infobox.grid(row=2, column=3, padx=0)
		self.sidebar.lift()
		return

	def closeStatistics(self):
		self.top.destroy()

	def parseValence(self, valence):
		if valence == 0:
			valStr = "neutral"
		elif valence == -1:
			valStr = "negative weak"
		elif valence == -2:
			valStr = "negative"
		elif valence == -3:
			valStr = "negative strong"
		elif valence == 1:
			valStr = "positive weak"
		elif valence == 2:
			valStr = "positive"
		elif valence == 3:
			valStr = "positive strong"
		elif valence == -99:
			valStr = "ambivalent"
		return valStr

	def parseStrength(self, strength):
		if strength == -1:
			strengthStr = "Dashed-Weak"
		elif strength == -2:
			strengthStr = "Dashed"
		elif strength == -3:
			strengthStr = "Dashed-Strong"
		elif strength == 1:
			strengthStr = "Solid-Weak"
		elif strength == 2:
			strengthStr = "Solid"
		elif strength == 3:
			strengthStr = "Solid-Strong"
		return strengthStr

def passEvent():
	pass

