from header import *
from Colours import *

class CommentBox(object):

	def __init__(self, obj, pos, text):
		self.obj = obj
		self.pos = pos
		self.open = False
		self.commentText = text

		self.commentBox = Text(obj.root, bd=1, height=5, width=20, wrap="word",
			font=(g.mainFont, 9, "normal"), bg=g.toHex(obj.cs.comment_bg),
			fg=g.toHex(obj.cs.lightText))
		self.commentBox.bind('<Key>', self.updateText)

		self.commentIcon = Button(obj.root, justify=LEFT)
		self.photo=PhotoImage(file=DIR+os.sep+"data"+os.sep+"comment.png")
		self.commentIcon.config(image=self.photo, width="30", height="30")
		self.commentIcon.grid()
		self.commentIcon.place(x=pos[0], y=pos[1])
		self.commentIcon.bind("<Button-1>", self.toggleCommentBox)
		self.commentIcon.bind("<Double-Button-3>", lambda event: self.obj.deleteComment(False))

		self.commentBox.insert(END, self.commentText)

	def updatePos(self, pos):
		self.pos = pos
		self.commentIcon.place(x=self.pos[0], y=self.pos[1])
		if self.open:
			self.commentBox.place(x=self.pos[0]+25, y=self.pos[1]+25)

	def updateText(self, event):
		self.commentText = self.commentBox.get("1.0", END)
		self.obj.commentText = self.commentText

	def toggleCommentBox(self, event):
		if self.open:
			self.closeCommentBox()
			self.open = False
		else:
			self.openCommentBox()
			self.open = True

	def openCommentBox(self):
		self.commentBox.place(x=self.pos[0]+25, y=self.pos[1]+25)
		return
		
	def closeCommentBox(self):
		self.commentBox.place_forget()
		return

	def deleteComment(self, event, undo=False):
		self.commentBox.destroy()
		self.commentIcon.destroy()
		self.commentText = ""
		self.obj.commentText = ""
		self.obj.hasComment = False

