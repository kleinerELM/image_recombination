# -*- coding: utf-8 -*-
import csv
import os, sys, getopt, platform, subprocess
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import numpy as np
#remove root windows
root = tk.Tk()
root.withdraw()

print("#########################################################")
print("# Automatically stitch TIFF images using a defined grid #")
print("# in a selected folder.                                 #")
print("#                                                       #")
print("# © 2020 Florian Kleiner, Max Patzelt                   #")
print("#   Bauhaus-Universität Weimar                          #")
print("#   Finger-Institut für Baustoffkunde                   #")
print("#                                                       #")
print("#########################################################")
print()

#### directory definitions
home_dir = os.path.dirname( os.path.realpath(__file__) )

#### global var definitions
col_count = 2
row_count = 2
showDebuggingOutput = False
openResultFile = False

#### process given command line arguments
def processArguments():
    global col_count
    global row_count
    global showDebuggingOutput
    global openResultFile
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-x] [-y] [-d]"
    col_changed = False
    row_changed = False
    try:
        opts, args = getopt.getopt(argv,"hcx:y:d",[])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-x,                  : amount of slices in x direction [' + str( col_count ) + ']' )
            print( '-y,                  : amount of slices in y direction [' + str( row_count ) + ']' )
            print( '-o,                  : open result file' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-o"):
            openResultFile = True
            print( 'result file will be opened' )
        elif opt in ("-x"):
            col_count = int( arg )
            col_changed = True
            print( 'changed amount of slices in x direction to ' + str( col_count ) )
        elif opt in ("-y"):
            row_count = int( arg )
            row_changed = True
            print( 'changed amount of slices in y direction to ' + str( row_count ) )
        elif opt in ("-d"):
            print( 'show debugging output' )
            showDebuggingOutput = True
    # alway expecting the same values for row/col if not defined explicitly        
    if col_changed and not row_changed:
        row_count = col_count
        print( 'changed amount of slices in y direction also to ' + str( row_count ) )
    elif row_changed and not col_changed:
        col_count = row_count
        print( 'changed amount of slices in x direction also to ' + str( col_count ) )
    print( '' )

def pil_grid(images, max_horiz=np.iinfo(int).max, fileType="png"):
    global workingDirectory
    n_images = len(images)
    n_horiz = min(n_images, max_horiz)
    h_sizes, v_sizes = [0] * n_horiz, [0] * (n_images // n_horiz)
    for i, im in enumerate(images):
        h, v = i % n_horiz, i // n_horiz
        h_sizes[h] = max(h_sizes[h], im.size[0])
        v_sizes[v] = max(v_sizes[v], im.size[1])
    h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
    im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
    for i, im in enumerate(images):
        print( " " + str( i+1 ), end="\r" )
        im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
    resultFile = os.path.dirname(workingDirectory) + '/' + os.path.basename( workingDirectory ) + "." + fileType
    print( "saving result to " + resultFile )
    im_grid.save( resultFile )
    im_grid.close()
    if openResultFile:
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', resultFile))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(resultFile)
        else:                                   # linux variants
            subprocess.call(('xdg-open', resultFile))

### actual program start
processArguments()
if ( showDebuggingOutput ) : print( "I am living in '" + home_dir + "'" )
workingDirectory = filedialog.askdirectory(title='Please select the image / working directory')
if ( showDebuggingOutput ) : print( "Selected working directory: " + workingDirectory )

count = 0
position = 0
## count files
if os.path.isdir( workingDirectory ) :
    fileNameList = []
    fileType = ''
    for file in os.listdir(workingDirectory):
        if ( file.endswith( ".tif" ) or file.endswith( ".TIF" ) or file.endswith( ".png" ) or file.endswith( ".PNG" ) ):
            count = count + 1
            if ( file.endswith( ".tif" ) or file.endswith( ".TIF" ) ):
                fileType = 'tif'
            if ( file.endswith( ".png" ) or file.endswith( ".PNG" ) ):
                fileType = 'png'
            fileNameList.append(file)
if ( count != col_count * row_count ):
    print( "Error: Expected" + str( col_count * row_count ) + " images, but found " + str( count )  )
else:
    print( str( count ) + " images found as expected!" )
    images = [Image.open(workingDirectory + "/" + x) for x in fileNameList]        
    pil_grid( images, col_count, fileType )

print( "Script DONE!" )