from tkinter import *
import tkinter

from calculations import *
import threading

from PIL import ImageTk, Image

import random
import time

import sys
import os

DIR = os.getcwd()
FILEDIR = DIR + os.sep + "Sheets"
TEMPLDIR = DIR + os.sep + "Templates"

mainFont = "Droid Sans"

def resource_path(relative_path):
    """ Get absolute path to resource (for PyInstaller) """
    base_path = getattr(sys, '_MEIPASS2', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
