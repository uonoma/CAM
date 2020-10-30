
from header import *

from Link import *

from Node import *

from Sheet import *

import os

def resizeLayout(event=[]):
	global sheet

	w=tk_root.winfo_screenwidth()
	h=tk_root.winfo_screenheight()

	sheet.resize()
	
def graphicsInit():
	tk_root.title("MindMap")
	tk_root.geometry("%dx%d%+d%+d" % (g.WIDTH/2, g.HEIGHT/2, g.WIDTH/4, g.HEIGHT/4))
	tk_root.config(bg="black")
	tk_canvas.configure(bd=0, highlightthickness=0)

	tk_root.protocol('WM_DELETE_WINDOW', exit_app)  # root is your root window

def exit_app():
    # check if saving
    # if not:
    tk_root.destroy()

if __name__ == "__main__":
    tk_root = Tk()
    tk_canvas = Canvas(tk_root)
    
    #img = ImageTk.PhotoImage(file=DIR+ os.sep +'icons' + os.sep + 'mindmap.png')
    img = ImageTk.PhotoImage(file=DIR+ os.sep +'data' + os.sep + 'mindmap.png')
    tk_root.tk.call('wm', 'iconphoto', tk_root._w, img)
    
    graphicsInit()
    
    fileName=DIR+ os.sep + "musse.json"
    if len(sys.argv) >= 2:
    	fileName = sys.argv[1]
    print("fileName:", fileName)
    
    sheet = Sheet(root=tk_root, canvas=tk_canvas, fileName=fileName)
    
    # have to do this after creating sheet, since resizeLayout calls sheet resize functions
    tk_root.bind("<Configure>", resizeLayout)
    
    
    resizeLayout()
    
    tk_root.mainloop()
