from header import *
from i18n import *
from ImageButton import ImageButton
from PIL import Image
from tkinter import messagebox

class MainMenu:

	root=[]
	canvas=[]
	kinds = [NODESTR, LINKSTR, SHEETSTR]

	def __init__(self, parentSheet):
		self.root=parentSheet.root
		self.canvas=parentSheet.canvas

		self.parentSheet=parentSheet
		self.cs = parentSheet.cs
		self.open = False
		self.kind = ""
		self.menu = Menu(self.root)

	def initMenu(self):
		menubar = self.menu

		self.exportBtn = ImageButton(menu=self, image="data/exportpng.png",
									cmd=self.parentSheet.exportToPng, tooltiptext=EXPORTPNGSTR)
		self.exportBtn.grid(row=0, column=3,padx=210)

		self.resetBtn = ImageButton(menu=self, image="data/reset.png",
									cmd=self.parentSheet.resetNodeSizes, tooltiptext=RESETSTR)
		self.resetBtn.grid(row=0, column=3,padx=140)

		self.minusBtn = ImageButton(menu=self, image="data/minus.png",
			cmd=self.parentSheet.openFilesForDiff, tooltiptext=MINUSSTR)
		self.minusBtn.grid(row=0, column=3,padx=70)

		self.saveFileBtn = ImageButton(menu=self, image="data/save.png",
			cmd=self.parentSheet.saveFileAs, tooltiptext=SAVESTR)
		self.saveFileBtn.grid(row=0, column=3,padx=0)

		self.root.config(menu=menubar)

	def menuPopup(self, event):
		self.initMenu(event)
		try:
			self.menu.tk_popup(event.x_root, event.y_root, 0)
		finally:
			self.menu.grab_release()