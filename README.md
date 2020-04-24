# image_recombination
simple script to stitch tiff images for Python 3.x

## standard automatical processing

run 
```bash
python .\image_recobination.py -x 3 -y 3
```
to stitch 9 images in a 3 x 3 matrix

## help output

```
#########################################################
# Automatically stitch TIFF images using a defined grid #
# in a selected folder.                                 #
#                                                       #
# © 2020 Florian Kleiner, Max Patzelt                   #
#   Bauhaus-Universität Weimar                          #
#   Finger-Institut für Baustoffkunde                   #
#                                                       #
#########################################################

usage: .\image_recombination.py [-h] [-x] [-y] [-d]
-h,                  : show this help
-w,                  : directory containing the images []
-x,                  : amount of slices in x direction [2]
-y,                  : amount of slices in y direction [2]
-s,                  : scaling factor [1]
-v,                  : change direction of the first line of tiles to vertical
-t,                  : create a thumbnail
-o,                  : open result file
-d                   : show debug output
```

# dependencies

This project depends on another Rpository. 

https://github.com/kleinerELM/tiff_scaling