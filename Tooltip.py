from header import *
import tkinter as Tk

class CreateToolTip(object):
	'''
	create a tooltip for a widget
	'''
	def __init__(self, widget, text='widget info', fromTextBox=True):
		self.widget = widget
		self.text = text
		self.fromTextBox = fromTextBox
		self.ttOpened = False
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Key>", self.reload)
		self.widget.bind("<Leave>", self.close)

	def enter(self):
		x = y = 0
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 55

		# creates a toplevel window
		if not self.ttOpened:
			self.tw = Tk.Toplevel(self.widget)
			# Leaves only the label and removes the app window
			self.tw.wm_overrideredirect(True)
			self.tw.wm_geometry("+%d+%d" % (x, y))

			if self.fromTextBox:
				self.text = self.widget.get("0.0",END)
			self.label = Tk.Label(self.tw, text=self.text, justify='left',
					background='yellow', relief='solid', borderwidth=1,
					font=("times", "14", "normal"))
			self.label.bind("<Enter>", self.enter)
			self.widget.after(500, self.label.pack(ipadx=4, ipady=4))
			self.ttOpened = True

	def close(self):
		if self.ttOpened:
			self.label.pack_forget()
			self.tw.destroy()
			self.ttOpened = False

	def reload(self, event=None):
		self.close()
		self.text = self.widget.get("1.0",END)
		self.enter()

class CreateToolTipV2(object):
	'''
	create a tooltip for Tkinter shapes
	'''
	def __init__(self, canvas, shape, text=''):
		self.canvas = canvas
		self.shape = shape
		self.text = text
		self.ttOpened = False
		self.canvas.tag_bind(shape, "<Enter>", self.enter)
		self.canvas.tag_bind(shape, "<Leave>", self.close)

	def enter(self, event=None):
		x = y = 0
		x += self.canvas.coords(self.shape)[0] + 55
		y += self.canvas.coords(self.shape)[1] + 55
		# creates a toplevel window
		if not self.ttOpened:
			self.tw = Tk.Toplevel()
			self.tw.wm_overrideredirect(True)
			self.tw.wm_geometry("+%d+%d" % (x, y))
			self.label = Tk.Label(self.tw, text=self.text, justify='left',
					background='yellow', relief='solid', borderwidth=1,
					font=("times", "14", "normal"))
			self.label.bind("<Enter>", self.enter)
			self.label.pack(ipadx=4, ipady=4)
			self.ttOpened = True

	def close(self, event=None):
		if self.ttOpened:
			self.label.pack_forget()
			self.tw.destroy()
			self.ttOpened = False