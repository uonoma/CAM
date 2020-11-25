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

CSVFIELDS_NODES_V2 = ['id', 'title', 'x_pos', 'y_pos', 'shape', 'creator', 'num',
'comment', 'timestamp', 'modifiable', 'CAM']

CSVFIELDS_NODES_V3 = ['id', 'title', 'x_pos', 'y_pos', 'width', 'height', 'shape', 'creator', 'num',
'comment', 'timestamp', 'modifiable', 'CAM']

CSVFIELDS_LINKS_V2 = ['id','starting_block','ending_block','line_style','creator','num','arrow_type','timestamp', 'CAM']

CSVFIELDS_NODES_V1 = ['id', 'title', 'x_pos', 'y_pos', 'shape', 'creator', 'links', 'num', 'comment', 'timestamp', 'modifiable']

CSVFIELDS_LINKS_V1 = ['id','starting_block','ending_block','line_style','creator','num','start_x','start_y','end_x','end_y','arrow_type','timestamp']

mainFont = "Droid Sans"
