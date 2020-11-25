from header import *
import tkinter as tk
from PIL import Image
from Tooltip import CreateToolTip

class ImageButton(object):

	def __init__(self, menu, image="", cmd=[], tooltiptext=""):
		self.text=tooltiptext
		self.root = menu.root

		imgOpen=Image.open(image)
		photoImg=ImageTk.PhotoImage(imgOpen)
		self.button = Button(self.root, image=photoImg, command=cmd)
		self.button.image=photoImg

		self.tooltip = CreateToolTip(self.button, self.text, fromTextBox=False)

	def grid(self, row, column, padx=0, pady=0):
		self.button.grid(row=row, column=column, padx=padx, pady=pady, sticky='e')