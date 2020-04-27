#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
import os, sys, getopt, platform, subprocess
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import numpy as np

# check for dependencies
home_dir = os.path.dirname(os.path.realpath(__file__))
# import tiff_scaling script
ts_path = os.path.dirname( home_dir ) + '/tiff_scaling/'
ts_file = 'set_tiff_scaling'
if ( os.path.isdir( ts_path ) and os.path.isfile( ts_path + ts_file + '.py' ) or os.path.isfile( home_dir + ts_file + '.py' ) ):
    if ( os.path.isdir( ts_path ) ): sys.path.insert( 1, ts_path )
    import set_tiff_scaling
else:
    programInfo()
    print( 'missing ' + ts_path + ts_file + '.py!' )
    print( 'download from https://github.com/kleinerELM/tiff_scaling' )
    sys.exit()

def programInfo():
    print("#########################################################")
    print("# Automatically stitch TIFF images using a defined grid #")
    print("# in a selected folder.                                 #")
    print("#                                                       #")
    print("# © 2020 Florian Kleiner, Max Patzelt                   #")
    print("#   Bauhaus-Universität Weimar                          #")
    print("#   Finger-Institut für Baustoffkunde                   #")
    print("#                                                       #")
    print("#########################################################", end='\n\n')

def getBaseSettings():
    settings = {
        "showDebuggingOutput" : False,
        "openResultFile"      : False,
        "createThumbnail"     : False,
        "home_dir"            : os.path.dirname(os.path.realpath(__file__)),
        "workingDirectory"    : "",
        "outputDirectory"     : "",
        "fileType"            : "",
        "col_count"           : 2,
        "row_count"           : 2,
        "tile_count"          : 0,
        "imageDirection"      : "h",
        "scaleFactor"         : 1,
        "scaleX"              : 1,
        "scaleY"              : 1,
        "scaleUnit"           : 'nm'
    }
    return settings

#### process given command line arguments
def processArguments():
    settings = getBaseSettings()
    col_changed = False
    row_changed = False
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-x] [-y] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hw:x:y:s:vtod",[])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-w,                  : directory containing the images [' + settings["workingDirectory"] + ']' )
            print( '-x,                  : amount of slices in x direction [' + str( settings["col_count"] ) + ']' )
            print( '-y,                  : amount of slices in y direction [' + str( settings["row_count"] ) + ']' )
            print( '-s,                  : scaling factor [' + str( settings["scaleFactor"] ) + ']' )
            print( '-v,                  : change direction of the first line of tiles to vertical' )
            print( '-t,                  : create a thumbnail' )
            print( '-o,                  : open result file' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-w"):
            newWorkingDirectory = str( arg )
            if ( os.path.isdir( newWorkingDirectory ) ):
                settings["workingDirectory"] = str( arg )
                print( 'changed working directory to "' + settings["workingDirectory"] + '"' )
            else:
                print( '"' + settings["workingDirectory"] + '" is not a directory!' )
        elif opt in ("-x"):
            settings["col_count"] = int( arg )
            col_changed = True
            print( 'changed amount of slices in x direction to ' + str( settings["col_count"] ) )
        elif opt in ("-y"):
            settings["row_count"] = int( arg )
            row_changed = True
            print( 'changed amount of slices in y direction to ' + str( settings["row_count"] ) )
        elif opt in ("-s"):
            settings["scaleFactor"] = int( arg )
            print( 'changed scale factor to ' + str( settings["scaleFactor"] ) )
        elif opt in ("-t"):
            settings["createThumbnail"] = True
            print( 'creating thumbnail' )
        elif opt in ("-o"):
            settings["openResultFile"] = True
            print( 'result file will be opened' )
        elif opt in ("-v"):
            settings["imageDirection"] = 'v'
            print( 'result file will be opened' )
        elif opt in ("-d"):
            print( 'show debugging output' )
            settings["showDebuggingOutput"] = True
    # always expecting the same values for row/col if not defined explicitly
    if col_changed and not row_changed:
        settings["row_count"] = settings["col_count"]
        print( 'changed amount of slices in y direction also to ' + str( settings["row_count"] ) )
    elif row_changed and not col_changed:
        settings["col_count"] = settings["row_count"]
        print( 'changed amount of slices in x direction also to ' + str( settings["col_count"] ) )
    imageDirectionName = 'vertical' if ( settings["imageDirection"] == 'v' ) else 'horizontal'
    print( 'direction of the first line of tiles is ' + imageDirectionName )
    print( '' )
    return settings

# https://stackoverflow.com/questions/30227466/combine-several-images-horizontally-with-python
def stitchImages( settings, fileNameList ):
    # check, if the image count will fit in new canvas 
    if ( settings["tile_count"] != settings["col_count"] * settings["row_count"] ):
        print( "  Error: Expected " + str( settings["col_count"] * settings["row_count"] ) + " images, but found " + str( settings["tile_count"] )  )
    else:
        print( "  stitching " + str( settings["tile_count"] ) + " images." )
        images = [ Image.open( x ) for x in fileNameList ]     

        h_sizes, v_sizes = [0] * settings["col_count"], [0] * settings["row_count"]
        # get grid size and create empty canvas
        for i, im in enumerate( images ):
            print( "   resizing image #" + str( i+1 ), end="     \r" )
            if ( settings["scaleFactor"] < 1 ):
                newsize = ( int(im.size[0]*settings["scaleFactor"]), int(im.size[1]*settings["scaleFactor"]) )
                im = im.resize(newsize) 
            h, v = i % settings["col_count"], i // settings["col_count"]
            h_sizes[h] = max(h_sizes[h], im.size[0])
            v_sizes[v] = max(v_sizes[v], im.size[1])
        
        h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
        im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
        # insert tiles to canvas
        for i, im in enumerate( images ):
            print( "   pasting image #" + str( i+1 ), end="     \r" )
            if ( settings["imageDirection"] == 'v' ): # vertical tile sequence
                im_grid.paste(im, (h_sizes[i // settings["row_count"]], v_sizes[i % settings["row_count"]]))
            else: # horizontal tile sequence
                im_grid.paste(im, (h_sizes[i % settings["col_count"]], v_sizes[i // settings["col_count"]]))
        resultFile = settings["outputDirectory"] + '/' + os.path.basename( settings["workingDirectory"] ) + settings["fileType"]

        print( "  saving result to " + resultFile )

        # set scaling for ImageJ
        scaling = { 'x' : settings["scaleX"], 'y' : settings["scaleY"], 'unit' : settings["scaleUnit"], 'editor':'FEI-MAPS'}
        im_grid.save( resultFile, tiffinfo = set_tiff_scaling.setImageJScaling( scaling ) )

        thumbXSize = 2000
        thumbDirectory = settings["outputDirectory"] + '/thumbnails'
        if ( settings["createThumbnail"] and im_grid.size[0] > thumbXSize):
            if ( not os.path.isdir( thumbDirectory ) ):
                os.mkdir( thumbDirectory )
            thumbFile = thumbDirectory + '/' + os.path.basename( settings["workingDirectory"] ) + settings["fileType"]
            print( "  saving thumbnail to " + thumbFile )
            scaleFactor = thumbXSize/im_grid.size[0]
            newsize = ( thumbXSize, int(scaleFactor*im_grid.size[1]) )
            im_grid = im_grid.resize(newsize) 
            scaling = { 'x' : settings["scaleX"]/scaleFactor, 'y' : settings["scaleY"]/scaleFactor , 'unit' : settings["scaleUnit"], 'editor':'FEI-MAPS'}
            im_grid.save( thumbFile, tiffinfo = set_tiff_scaling.setImageJScaling( scaling ) )

        im_grid.close()

        if settings["openResultFile"]:
            if platform.system() == 'Darwin':       # macOS
                subprocess.call(('open', resultFile))
            elif platform.system() == 'Windows':    # Windows
                os.startfile(resultFile)
            else:                                   # linux variants
                subprocess.call(('xdg-open', resultFile))

def getFileList( settings ):
    allowed_file_extensions = [ '.tif', '.png' ]
    if os.path.isdir( settings["workingDirectory"] ) :
        fileNameList = []
        for file in os.listdir(settings["workingDirectory"]):
            file_name, file_extension = os.path.splitext( file )
            if ( file_extension.lower() in allowed_file_extensions ):#   file.lower().endswith( ".tif" ) or file.lower().endswith( ".png" ) ):
                if ( settings["fileType"] == "" ):
                    settings["fileType"] = file_extension.lower()
                if ( settings["fileType"] == file_extension.lower() ):
                    settings["tile_count"] += 1
                    fileNameList.append( settings["workingDirectory"] + "/" + file )
    else:
        print( "  Error: '" + settings["workingDirectory"] + "' is no directory")
    if ( settings["showDebuggingOutput"] ):
        print( "found " + str( settings["tile_count"] ) + " " + settings["fileType"].upper() + " tiles." )

    return fileNameList

### actual program start
if __name__ == '__main__':
    #remove root windows
    root = tk.Tk()
    root.withdraw()
  
    ### global settings    
    programInfo()
    settings = processArguments()
    if ( settings["workingDirectory"] == "" ):
        print( "Please select a working directory", end="\r" )
        settings["workingDirectory"] = filedialog.askdirectory(title='Please select the image / working directory')
    if ( settings["outputDirectory"] == "" ):
        settings["outputDirectory"] = os.path.dirname( settings["workingDirectory"] )

    if ( settings["showDebuggingOutput"] ) : 
        print( "I am living in '" + settings["home_dir"] + "'" )
        print( "Selected working directory: " + settings["workingDirectory"] )
        print( "Output directory: " + settings["outputDirectory"], end='\n\n' )

    fileNameList = getFileList( settings )
    stitchImages( settings, fileNameList )

    print( "Script DONE!" )