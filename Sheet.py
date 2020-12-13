# -*- coding: utf-8 -*-

import os
import csv
import cv2
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
from PIL import ImageTk, Image, ImageGrab, ImageDraw


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

		# Adjacent nodes dictionaries
		self.neighborsPre = {}
		self.neighborsPost = {}

		# Side bar with numeric data/aggregated information
		self.sidebar = Frame(root, width=50, bg='white', height=200,
			borderwidth=2, highlightthickness=1, highlightbackground="black")
		self.infobox = Label(self.sidebar, text="Statistics:")

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
		if self.selectedNode == -99:
			return
		else:
			n = self.getNodeByIndex(self.selectedNode)
			n.removeByClick()

	def computeDiffCam(self, cam1, cam2):
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
        Read nodes from blocks.csv (pre-CAM)
        '''
		nodes1 = StringIO(nodesFile1.read().decode('utf-8'))
		nodesReader1 = csv.reader(nodes1)
		firstLnNodes = next(nodesReader1)

		nodesversion = 3
		assert firstLnNodes in [CSVFIELDS_NODES_V1, CSVFIELDS_NODES_V2, CSVFIELDS_NODES_V3],\
			("Wrong column names in nodes .csv file " + str(cam1))
		if firstLnNodes == CSVFIELDS_NODES_V1:
			nodesversion = 1
		elif firstLnNodes == CSVFIELDS_NODES_V2:
			nodesversion = 2
		elif firstLnNodes == CSVFIELDS_NODES_V3:
			nodesversion = 3
		links = StringIO(linksFile1.read().decode('utf-8'))
		linksReader1 = csv.reader(links)
		firstLnLinks = next(linksReader1)
		assert firstLnLinks in [CSVFIELDS_LINKS_V1, CSVFIELDS_LINKS_V2],\
			"Wrong column names in links .csv file"
		version = nodesversion
		nodesData1 = {}
		linksData1 = {}

		for row in nodesReader1:
			valence = 0
			if version == 3:
				shapeCol = 6
			else:
				shapeCol = 4
			if row[4] == "neutral":
				valence = 0
			elif row[shapeCol] == "negative weak":
				valence = -1
			elif row[shapeCol] == "negative":
				valence = -2
			elif row[shapeCol] == "negative strong":
				valence = -3
			elif row[shapeCol] == "positive weak":
				valence = 1
			elif row[shapeCol] == "positive":
				valence = 2
			elif row[shapeCol] == "positive strong":
				valence = 3
			elif row[shapeCol] == "ambivalent":
				valence = -99
			index = float(row[0])
			if version == 1:
				index = float(row[7])
			text = row[1]

			# Neighbors list updated later
			neighbors = []

			nodesData1.update({text: (index, valence)})

		'''
		Read nodes from blocks.csv (post-CAM)
		'''
		nodesData2 = {}
		linksData2 = {}
		archive2 = zipfile.ZipFile(cam2, 'r')
		names2 = archive2.namelist()
		nodesFile2 = ""
		linksFile2 = ""
		for n in names2:
			if n.endswith("blocks.csv"):
				nodesFile2 = archive2.open(n)
			elif n.endswith("links.csv"):
				linksFile2 = archive2.open(n)
		nodes2 = StringIO(nodesFile2.read().decode('utf-8'))
		nodesReader2 = csv.reader(nodes2)
		firstLnNodes = next(nodesReader2)

		assert firstLnNodes in [CSVFIELDS_NODES_V1, CSVFIELDS_NODES_V2, CSVFIELDS_NODES_V3], \
			"Wrong column names in nodes .csv file."
		if firstLnNodes == CSVFIELDS_NODES_V1:
			nodesversion = 1
		elif firstLnNodes == CSVFIELDS_NODES_V2:
			nodesversion = 2
		elif firstLnNodes == CSVFIELDS_NODES_V3:
			nodesversion = 3
		links = StringIO(linksFile2.read().decode('utf-8'))
		linksReader2 = csv.reader(links)
		firstLnLinks = next(linksReader2)
		version = nodesversion
		"Wrong column names in nodes .csv file."

		for row in nodesReader2:
			valence = 0
			if version == 3:
				shapeCol = 6
			else:
				shapeCol = 4
			if row[4] == "neutral":
				valence = 0
			elif row[shapeCol] == "negative weak":
				valence = -1
			elif row[shapeCol] == "negative":
				valence = -2
			elif row[shapeCol] == "negative strong":
				valence = -3
			elif row[shapeCol] == "positive weak":
				valence = 1
			elif row[shapeCol] == "positive":
				valence = 2
			elif row[shapeCol] == "positive strong":
				valence = 3
			elif row[shapeCol] == "ambivalent":
				valence = -99
			index = float(row[0])
			if version == 1:
				index = float(row[7])
			text = row[1]
			nodesData2.update({text : (index, valence)})

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

		for row in linksReader1:
			strength = 0
			directed = 1
			if row[3] == "Solid-Strong":
				strength = 3
			elif row[3] == "Solid":
				strength = 2
			elif row[3] == "Solid-Weak":
				strength = 1
			elif row[3] == "Dashed-Strong":
				strength = -3
			elif row[3] == "Dashed":
				strength = -2
			elif row[3] == "Dashed-Weak":
				strength = -1

			if version == 2:
				if row[6] == "uni":
					directed = 1
				elif row[6] == "none":
					directed = 0
			elif version == 1:
				if row[10] == "uni":
					directed = 1
				elif row[10] == "none":
					directed = 0
			startingNodeIndex = None
			endNodeIndex = None

			for (t,(i, v)) in nodesData1.items():
				if int(row[1]) == i:
					startingNodeText = t
					startingNodeIndex = self.lookupNodeIndex(startingNodeText)
				elif int(row[2]) == i:
					endNodeText = t
					endNodeIndex = self.lookupNodeIndex(endNodeText)

			directed = directed
			strength = strength

			linksData1.update({(startingNodeIndex, endNodeIndex, directed) : strength})

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

		'''
		Read links from links.csv (post-CAM)
		'''

		for row in linksReader2:
			strength = 0
			directed = 1
			if row[3] == "Solid-Strong":
				strength = 3
			elif row[3] == "Solid":
				strength = 2
			elif row[3] == "Solid-Weak":
				strength = 1
			elif row[3] == "Dashed-Strong":
				strength = -3
			elif row[3] == "Dashed":
				strength = -2
			elif row[3] == "Dashed-Weak":
				strength = -1

			if version == 2:
				if row[6] == "uni":
					directed = 1
				elif row[6] == "none":
					directed = 0
			elif version == 1:
				if row[10] == "uni":
					directed = 1
				elif row[10] == "none":
					directed = 0
			startingNodeIndex = None
			endNodeIndex = None

			for (t, (i, v)) in nodesData2.items():
				if int(row[1]) == i:
					startingNodeText = t
					startingNodeIndex = self.lookupNodeIndex(endNodeText)
				elif int(row[2]) == i:
					endNodeText = t
					endNodeIndex = self.lookupNodeIndex(endNodeText)

			directed = directed
			strength = strength
			linksData2.update({(startingNodeIndex, endNodeIndex, directed) : strength})

			# Update node neighbors
			self.getNodeByText(startingNodeText).addNeighbor(i2=endNodeText)
			self.getNodeByText(endNodeText).addNeighbor(i2=startingNodeText)

			if self.neighborsPost.get(startingNodeText) is None:
				self.neighborsPost[startingNodeText] = [endNodeText]
			else:
				self.neighborsPost[startingNodeText].append(endNodeText)

			if self.neighborsPost.get(endNodeText) is None:
				self.neighborsPost[endNodeText] = [startingNodeText]
			else:
				self.neighborsPost[endNodeText].append(startingNodeText)
			print(self.neighborsPost)
		'''
		Draw diff-CAM links
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
		preNodes['total'] = 0
		preNodes['pos'] = 0
		preNodes['neg'] = 0
		preNodes['neutral'] = 0
		preNodes['amb'] = 0
		# Mean valence
		preNodes['avgValence'] = 0
		# Standard deviation
		preNodes['SDValence'] = 0

		# Mean by degree
		preMeanByDegree = []

		# Same for post-CAM
		postNodes['total'] = 0
		postNodes['pos'] = 0
		postNodes['neg'] = 0
		postNodes['neutral'] = 0
		postNodes['amb'] = 0
		postNodes['avgValence'] = 0
		postNodes['SDValence'] = 0

		# TODO: Create link dictionaries
		# Dictionary keys: 'total', 'pos', 'neg'
		preLinks = {}
		postLinks = {}

		# Calculate statistical parameters & fill dictionaries
		for (_, (_,v)) in nodesData1.items():
			preNodes['total'] = preNodes['total'] + 1
			# For calculation of mean: Use 0 as valence for ambivalent nodes (instead of -99)
			if v == -99:
				v0 = 0
			else:
				v0 = v
			preNodes['avgValence'] += v0

		preNodes['avgValence'] = preNodes['avgValence'] / preNodes['total']

		squaredDiff = 0
		for (_, (_, v)) in nodesData1.items():
			if int(v) > 0:
				preNodes['pos'] = preNodes['pos'] + 1
			elif int(v) < 0 and int(v) > -99:
				preNodes['neg'] = preNodes['neg'] + 1
			elif int(v) == 0:
				preNodes['neutral'] = preNodes['neutral'] + 1
			elif int(v) == -99:
				preNodes['amb'] = preNodes['amb'] + 1

			# For calculation of SD: Use 0 as valence for ambivalent nodes (instead of -99)
			if int(v) == -99:
				v0 = 0
			else:
				v0 = int(v)
			squaredDiff += (v0 - preNodes['avgValence']) ** 2

		preNodes['SDValence'] = math.sqrt(squaredDiff / (preNodes['total'] - 1))

		valsByDegree = {}
		meansByDegreePre = {}

		for (t, (_, v)) in nodesData1.items():
			try:
				neighbors = self.neighborsPre[t]
				degree = len(neighbors)
			except:
				degree = 0
			if valsByDegree.get(degree) is None:
				valsByDegree[degree] = [v]
			else:
				valsByDegree[degree].append(v)

		for (d, vs) in valsByDegree.items():
			vs1 = [0 if x == -99 else x for x in vs]
			meanVal = sum(vs1)/len(vs1)
			meansByDegreePre[d] = meanVal


		'''
		Same for post-CAM
		'''
		for (t, (_, v)) in nodesData2.items():
			postNodes['total'] = postNodes['total'] + 1
			if v == -99:
				v0 = 0
			else:
				v0 = v
			print(v0)
			postNodes['avgValence'] += v0

		postNodes['avgValence'] = postNodes['avgValence'] / postNodes['total']

		squaredDiff = 0

		for (_, (_, v)) in nodesData2.items():
			if int(v) > 0:
				postNodes['pos'] = postNodes['pos'] + 1
			elif int(v) < 0 and int(v) > -99:
				postNodes['neg'] = postNodes['neg'] + 1
			elif int(v) == 0:
				postNodes['neutral'] = postNodes['neutral'] + 1
			elif int(v) == -99:
				postNodes['amb'] = postNodes['amb'] + 1

			if int(v) == -99:
				v0 = 0
			else:
				v0 = int(v)
			squaredDiff += (v0 - postNodes['avgValence']) ** 2

		postNodes['SDValence'] = math.sqrt(squaredDiff / (postNodes['total'] - 1))

		valsByDegree = {}
		meansByDegreePost = {}
		for (t, (_, v)) in nodesData2.items():
			try:
				neighbors = self.neighborsPost[t]
				degree = len(neighbors)
			except:
				degree = 0
			if valsByDegree.get(degree) is None:
				valsByDegree[degree] = [v]
			else:
				valsByDegree[degree].append(v)

		for (d, vs) in valsByDegree.items():
			vs1 = [0 if x == -99 else x for x in vs]
			meanVal = sum(vs1)/len(vs1)
			meansByDegreePost[d] = meanVal

		'''
		Concat statistics
		'''
		self.statisticsStr = "### PRE-CAM: NODES ###"
		for (k, v) in preNodes.items():
			self.statisticsStr += "\n%s: %.4f" %(k, v)
		for (d, m) in meansByDegreePre.items():
			self.statisticsStr += "\nMean - Degree %d: %.4f" %(d, m)

		self.statisticsStr += "\n### POST-CAM-NODES ###"
		for (k, v) in postNodes.items():
			self.statisticsStr += "\n%s: %.4f" % (k, v)
		for (d, m) in meansByDegreePost.items():
			self.statisticsStr += "\nMean - Degree %d: %.4f" %(d, m)

		print(self.statisticsStr)
		self.openInfoBox(self.statisticsStr)

#		posDiffNum = 0
#		negDiff = 0
#		negDiffNum = 0
#		neutralDiff = 0
#		neutralDiffNum = 0
#		ambDiff = 0
#		ambDiffNum = 0
#		onlyinPre = {}
#		onlyinPost = {}

#		for k1, v1 in nodesData1.items():
#			if k1 in nodesData2:
#				if v1 > 0:
#					posDiff = posDiff + (nodesData2[k1] - v1)
#					posDiffNum = posDiffNum + 1
#				elif v1 < 0 and v1 > -99:
#					negDiff = negDiff + (nodesData2[k1] - v1)
#					negDiffNum = negDiffNum + 1
#				elif v1 == 0:
#					neutralDiff = neutralDiff + nodesData2[k1]
#					neutralDiffNum = neutralDiffNum + 1
#				elif v1 == -99:
#					if not nodesData2[k1] == -99:
#						ambDiff = ambDiff + nodesData2[k1]
#					ambDiffNum = ambDiffNum + 1
#			else:
#				onlyinPre.update({ k1 : v1} )
#		for k2, v2 in nodesData2.items():
#			if k2 not in nodesData1:
#				onlyinPost.update({k2 : v2} )
#		posDiffAvg = round(posDiff / max(posDiffNum,1), 4)
#		negDiffAvg = round(negDiff / max(negDiffNum,1), 4)
#		neutralDiffAvg = round(neutralDiff / max(neutralDiffNum,1), 4)
#		ambDiffAvg = round(ambDiff / max(ambDiffNum, 1), 4)
#		onlyinPreStr = ""
#		onlyinPostStr = ""
#		for (k1, v1) in onlyinPre.items():
#			onlyinPreStr = onlyinPreStr + "\n" + str(k1) + ":" + str(v1)
#		for (k2, v2) in onlyinPost.items():
#			onlyinPostStr = onlyinPostStr + "\n" + str(k2) + ":" + str(v2)
#
#		self.diffCamDataLabels = ["Veränderung positiver Knoten (prä-post):\n",
#			"Veränderung negativer Knoten (prä-post):\n",
#			"Veränderung neutraler Knoten (prä-post):\n",
#			"Veränderung ambivalenter Knoten (prä-post):\n",
#			"Entfallene Knoten (nur in prä): ",
#			"Hinzugefügte Knoten (nur in post): "]
#		self.diffCamData = [str(posDiffAvg), str(negDiffAvg),
#			str(neutralDiffAvg), str(ambDiffAvg),onlyinPreStr, onlyinPostStr]
#		diffStr = ""
#		for i in range(0, len(self.diffCamDataLabels)):
#			diffStr = diffStr + "\n" + str(self.diffCamDataLabels[i]) +\
#			str(self.diffCamData[i] + "\n")

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

# Deprecated. New function: exportAsCsv

#	def saveData(self, event=[]):
#		data = {}
#		data['root_geometry'] = self.root.winfo_geometry()
#		data['nodes'] = []
#
#		# acceptance field is deprecated
#		for n in self.nodes:
#			nData={}
#		#	nData['acceptance'] = n.acceptance
#			nData['index'] = n.index
#			nData['coords'] = n.coords
#			nData['radius'] = n.r
#			nData['text'] = n.getText()
#			nData['valence'] = int(n.valence)
#			nData['read-only'] = n.readOnly
#			nData['comment'] = n.commentText
#
#			data['nodes'].append(nData)
#
#			data['links'] = []
#		for l in self.links:
#			lData={}
#			lData['nA'] = l.nA.index
#			lData['nB'] = l.nB.index
#			lData['directed'] = l.directed
#			lData['strength'] = max(l.strengthA, l.strengthB)
#			lData['comment'] = l.commentText
#			if not l.dashed == ():
#				lData['strength'] = -lData['strength']
#			data['links'].append(lData)
#
#		self.exportAsCsv()
#
#		return

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
	#		CSVFIELDS_NODES_V4 = ['id', 'title', 'x_pos', 'y_pos', 'width', 'height', 'shape', 'creator', 'num',
	#							  'comment', 'timestamp', 'modifiable', 'CAM', 'removed']
			if n.valence == 0:
				val = "neutral"
			elif n.valence == -1:
				val = "negative weak"
			elif n.valence == -2:
				val = "negative"
			elif n.valence == -3:
				val = "negative strong"
			elif n.valence == 1:
				val = "positive weak"
			elif n.valence == 2:
				val = "positive"
			elif n.valence == 3:
				val = "positive strong"
			elif n.valence == -99:
				val = "ambivalent"
			r = [n.index, n.text, n.coords[0], n.coords[1], 2*n.r, 2*n.r, val, 0, n.index, "", "", 1, fnBase, n.removed]
			csvWriterNodes.writerow(r)

		linksFileName = fnBaseLong + "_links" + fnExt
		csvFileLinks = open(linksFileName, mode='w+', newline='')
		csvWriterLinks = csv.writer(csvFileLinks, delimiter=delim, quoting=csv.QUOTE_NONE,
									escapechar='\\')
		csvWriterLinks.writerow(CSVFIELDS_LINKS_V2)

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

		#	CSVFIELDS_LINKS_V2 = ['id', 'starting_block', 'ending_block', 'line_style', 'creator', 'num', 'arrow_type',
		#						  'timestamp', 'CAM']
			r = [i, l.nA.index, l.nB.index, strength, "", i, dir, "", fnBase]
			csvWriterLinks.writerow(r)
			i = i + 1



#		if self.diffCam:
#			for i in range(0, len(self.diffCamDataLabels)):
#				row1.append(self.diffCamDataLabels[i])
#				row2.append(self.diffCamData[i])
#			csvWriter.writerow(row1)
#			csvWriter.writerow(row2)
#		else:
#			rows = []
#			nodes = self.nodes
#			links = self.links
#			for n in nodes:
#				if n.acceptance:
#					rows.append([n.index, "Acceptance", "", n.initTime])
#				else:
#					rows.append([n.index, n.text, "", n.initTime])
#				for l in links:
#					if n.index == l.nB.index:
#						rows.append([n.index, l.nA.index, max(l.strengthA,
#						l.strengthB), l.initTime])
#			for r in rows:
#				csvWriter.writerow(r)

	def openFilesForDiff(self):
		if self.fileOpen:
			if tkinter.messagebox.askyesno(SAVESTR, ASKSAVESTR):
				self.saveFileAs()
			self.closeFile()
		fileNamePre = tkinter.filedialog.askopenfilename(initialdir = FILEDIR,title =
			SELECTPREFILESTR,filetypes = [("Empathica CAM","*.zip")])
		fileNamePost = tkinter.filedialog.askopenfilename(initialdir = FILEDIR,title =
			SELECTPOSTFILESTR,filetypes = [("Empathica CAM","*.zip")])

		self.computeDiffCam(fileNamePre, fileNamePost)
		self.fileOpen = True
		
	def reInitNodes(self):
		for n in self.nodes:
			n.canvas.delete(n.shapeIndex)
			n.tk_text.destroy()
			n.initDrawing()

	def closeFile(self, drawn=True):
		if drawn:
			for node in self.nodes:
				node.remove()
			self.closeInfoBox()
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

	def getLink(self, indexA, indexB):
		nodeA = self.getNodeByIndex(indexA)
		nodeB = self.getNodeByIndex(indexB)
		for l in self.links:
			if (nodeA == l.nA and nodeB == l.nB) or (nodeA == l.nB and
			nodeB == l.nA):
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

#	def calculateNodeStatistics(self, key):
##		distribution = self.valenceDistributions[key]
#		distribution = {}
#		# '1: [], '2': []...
#		median = ()
#		numVals = 0
#		totalNodes = 0
#		avgValence = 0
#		neutralNodes = len(distribution["0"])
#		neg1Nodes = len(distribution["-1"])
#		neg2Nodes = len(distribution["-2"])
#		neg3Nodes = len(distribution["-3"])
#		pos1Nodes = len(distribution["+1"])
#		pos2Nodes = len(distribution["+2"])
#		pos3Nodes = len(distribution["+3"])
#		ambNodes = len(distribution["ambivalent"])
#		for k,v in distribution.items():
#			if len(v) > numVals:
#				median = (k,len(v))
#				numVals = len(v)
#			try:
#				valence = float(k)
#			except:
#				if k == "ambivalent":
#					valence = 0
#			avgValence = avgValence + valence * len(v)
#			totalNodes = totalNodes + len(v)
#		avgValence = avgValence / totalNodes
#		std = 0
#		numVals = 0
#		for k,v in distribution.items():
#			try:
#				valence = float(k)
#			except:
#				if k == "ambivalent":
#					valence = 0
#			for n in range(0,len(v)):
#				std = std + (valence - avgValence)**2
#				numVals = numVals + 1
#		std = std/numVals
#
#		statistics = "Node Statistics: " + key.upper() + "\n\n" + "Average Valence: " + str(avgValence) +\
#			"\n" + "Median: " + str(median[0]) + " (" + str(median[1]) +")" +\
#			"\nSTD: " + str(std) + "\nNeutral: " + str(neutralNodes) +\
#			"\nWeak Positive: " + str(pos1Nodes) + "\nPositive: " + str(pos2Nodes) +\
#			"\nStrong Positive: " + str(pos3Nodes) + "\nWeak Negative: " +\
#			str(neg1Nodes) + "\nNegative: " + str(neg2Nodes) +\
#			"\nStrong Negative:" + str(neg3Nodes) + "\nAmbivalent: " + str(ambNodes)
#		return(statistics)

	def openInfoBox(self, text):
		self.infobox.config(text=text)
		self.sidebar.grid(row=2, column=3, sticky='e')
		self.infobox.grid(row=2, column=3, padx=0)
		self.sidebar.lift()
		return

	def closeInfoBox(self):
		self.sidebar.grid_forget()
		self.infobox.grid_forget()