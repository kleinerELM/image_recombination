#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
import os, sys, getopt, platform, subprocess
import tkinter as tk
from tkinter import filedialog
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000 # prevent decompressionbomb warning for typical images
import numpy as np

# check for dependencies
home_dir = os.path.dirname(os.path.realpath(__file__))
# import tiff_scaling script
ts_path = os.path.dirname( home_dir ) + '/tiff_scaling/'
ts_file = 'extract_tiff_scaling'
if ( os.path.isdir( ts_path ) and os.path.isfile( ts_path + ts_file + '.py' ) or os.path.isfile( home_dir + ts_file + '.py' ) ):
    if ( os.path.isdir( ts_path ) ): sys.path.insert( 1, ts_path )
    import extract_tiff_scaling as es
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
    print("# © 2022 Florian Kleiner, Max Patzelt                   #")
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
        "scaleUnit"           : 'nm',
        "cropX"               : 0,
        "cropY"               : 0
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
def stitchImages( settings, fileNameList, resultFile = '', result_file_name = '' ):
    # check, if the image count will fit in new canvas
    if ( settings["tile_count"] != settings["col_count"] * settings["row_count"] ):
        print( "  Error: Expected " + str( settings["col_count"] * settings["row_count"] ) + " images, but found " + str( settings["tile_count"] )  )
    else:
        scaling_filename = None
        for x in fileNameList:
            if x != 'EMPTY': # fails if the first image is empty, which should never happen
                scaling_filename = x
                break
        if scaling_filename != None:
            scaling = es.autodetectScaling( os.path.basename(scaling_filename), os.path.dirname(os.path.abspath(scaling_filename)) )
            scaling_file = Image.open( scaling_filename )
            if result_file_name == '': result_file_name = os.path.basename( settings["workingDirectory"] )
            print( "  stitching " + str( settings["tile_count"] ) + " images." )

            images = []
            for x in fileNameList:
                if x == 'EMPTY': # fails if the first image is empty, which should never happen
                    images.append(Image.new(scaling_file.mode, (scaling_file.size[0], scaling_file.size[1]), color='black'))
                else:
                    images.append(Image.open( x ))

            h_sizes, v_sizes = [0] * settings["col_count"], [0] * settings["row_count"]
            # get grid size and create empty canvas
            for i, im in enumerate( images ):
                print( "   resizing image #" + str( i+1 ), end="     \r" )
                if ( settings["scaleFactor"] < 1 ):
                    newsize = ( int(im.size[0]*settings["scaleFactor"]), int(im.size[1]*settings["scaleFactor"]) )
                    images[i] = images[i].resize(newsize, Image.ANTIALIAS)
                h, v = i % settings["col_count"], i // settings["col_count"]
                h_sizes[h] = max(h_sizes[h], images[i].size[0])
                v_sizes[v] = max(v_sizes[v], images[i].size[1])

            h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
            #print(h_sizes[-1], v_sizes[-1])
            im_grid = Image.new(images[0].mode, (h_sizes[-1], v_sizes[-1]), color='white')
            # insert tiles to canvas
            for i, im in enumerate( images ):
                print( "   pasting image #" + str( i+1 ), end="     \r" )
                if ( settings["imageDirection"] == 'v' ): # vertical tile sequence
                    im_grid.paste(im, (h_sizes[i // settings["row_count"]], v_sizes[i % settings["row_count"]]))
                else: # horizontal tile sequence
                    im_grid.paste(im, (h_sizes[i % settings["col_count"]], v_sizes[i // settings["col_count"]]))
            if resultFile == '': resultFile = settings["outputDirectory"] + os.sep + result_file_name + settings["fileType"]

            print( "  saving result to " + resultFile )
            if settings["cropX"] > 0 and (settings["cropX"] < h_sizes[-1] or settings["cropY"] < v_sizes[-1]):
                crop_x = settings["cropX"] if settings["cropX"] < h_sizes[-1] else h_sizes[-1]
                crop_y = settings["cropY"] if settings["cropY"] < v_sizes[-1] else v_sizes[-1]
                im_grid = im_grid.crop((0,0, crop_x, crop_y))
            # set scaling for ImageJ
            if scaling == False or scaling == es.getEmptyScaling(): scaling = { 'x' : settings["scaleX"], 'y' : settings["scaleY"], 'unit' : settings["scaleUnit"], 'editor':'FEI-MAPS'}
            im_grid.save( resultFile, tiffinfo = es.setImageJScaling( scaling ) )

            thumbXSize = 2000
            thumbDirectory = settings["outputDirectory"] + os.sep +'thumbnails'
            if ( settings["createThumbnail"] and im_grid.size[0] > thumbXSize):
                if ( not os.path.isdir( thumbDirectory ) ):
                    os.mkdir( thumbDirectory )
                thumbFile = thumbDirectory + os.sep + result_file_name + settings["fileType"]
                print( "  saving thumbnail to " + thumbFile )
                scaleFactor = thumbXSize/im_grid.size[0]
                newsize = ( thumbXSize, int(scaleFactor*im_grid.size[1]) )
                im_grid = im_grid.resize(newsize)
                scaling = { 'x' : scaling['x']/scaleFactor, 'y' : scaling['y']/scaleFactor , 'unit' : scaling['unit'], 'editor' : scaling['editor']}
                im_grid.save( thumbFile, tiffinfo = es.setImageJScaling( scaling ) )

            im_grid.close()

            if settings["openResultFile"]:
                if platform.system() == 'Darwin':       # macOS
                    subprocess.call(('open', resultFile))
                elif platform.system() == 'Windows':    # Windows
                    os.startfile(resultFile)
                else:                                   # linux variants
                    subprocess.call(('xdg-open', resultFile))
        else:
            print('Error, none of the files found!')


def getFileList( settings ):
    allowed_file_extensions = [ '.tif', '.png' ]
    if os.path.isdir( settings["workingDirectory"] ) :
        fileNameList = []
        for file in sorted(os.listdir(settings["workingDirectory"])):
            file_name, file_extension = os.path.splitext( file )
            if ( file_extension.lower() in allowed_file_extensions ):
                if ( settings["fileType"] == "" ):
                    settings["fileType"] = file_extension.lower()
                if ( settings["fileType"] == file_extension.lower() ):
                    settings["tile_count"] += 1
                    fileNameList.append( settings["workingDirectory"] + os.sep + file )
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