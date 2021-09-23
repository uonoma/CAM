from Sheet import *

import os

def resizeLayout(event=[]):
    global sheet

    w=tk_root.winfo_screenwidth()
    h=tk_root.winfo_screenheight()

    sheet.resize()
	
def graphicsInit():
    tk_root.title("Delta CAM")
    tk_root.geometry("800x600")
    tk_root.config(bg="black")
    tk_canvas.configure(bd=0, highlightthickness=0)

    tk_root.protocol('WM_DELETE_WINDOW', exit_app)  # root is your root window

def exit_app():
    tk_root.destroy()

if __name__ == "__main__":
    tk_root = Tk()
    tk_canvas = Canvas(tk_root)
    
    graphicsInit()
    
    fileName=DIR+ os.sep + "Untitled"
    if len(sys.argv) >= 2:
        fileName = sys.argv[1]

    sheet = Sheet(root=tk_root, canvas=tk_canvas, fileName=fileName)
    
    resizeLayout()
    
    tk_root.mainloop()