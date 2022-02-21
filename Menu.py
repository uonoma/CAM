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

		self.minusBtn = ImageButton(menu=self, image=os.path.join("data", "minus.png"),
			cmd=self.parentSheet.openFilesForDiff, tooltiptext=MINUSSTR)
		self.minusBtn.grid(row=0, column=3,padx=140)

		self.minusJsonBtn = ImageButton(menu=self, image=os.path.join("data", "minusJson.png"),
			cmd=self.parentSheet.parseCAMFromJson, tooltiptext=MINUSSTR)
		self.minusJsonBtn.grid(row=0, column=3, padx=70)

		self.saveFileBtn = ImageButton(menu=self, image=os.path.join("data", "save.png"),
			cmd=self.parentSheet.saveFileAs, tooltiptext=SAVESTR)
		self.saveFileBtn.grid(row=0, column=3,padx=0)

		self.root.config(menu=menubar)

	def menuPopup(self, event):
		self.initMenu(event)
		try:
			self.menu.tk_popup(event.x_root, event.y_root, 0)
		finally:
			self.menu.grab_release()