#!/usr/bin/env python3

########################################################################
###                                                                  ###
###                            UnionFilms                            ###
###                                                                  ###
###                    Written on 2018/01/24 by KD                   ###
###                 Last modified on 2018/03/20 by KD                ###
###                                                                  ###
### Script for making rating tags from a png                         ###
###                                                                  ###
### Usage: ./makeRtg.py <pathToPngFile>                              ###
### or just drag and drop the png file onto this script              ###
###                                                                  ###
### Depends: OpenDCP, ffmpeg/libav, PIL/Pillow (Optional)            ###
###                                                                  ###
########################################################################

import os
import sys
import datetime
import argparse

assert(len(sys.argv) >= 2)

parser = argparse.ArgumentParser(description='Make rating tags!')

parser.add_argument('image', metavar='image', type=str, nargs=1, help='The rating tag to convert to a DCP rating tag.')
parser.add_argument('--dry', dest='dryrun', action='store_true', help='Don\'t do encoding, just print out the commands.')
parser.add_argument('--keep', dest='keep', action='store_true', help='Don\'t delete temp files.')

parser.add_argument('--duration', dest='duration', type=int, default=15, help='Duration of the tag, default=15.')
parser.add_argument('--fade', dest='fade', type=int, default=1, help='Duration of the in/out fade, default=1.')

parser.add_argument('--3d', dest='threed', action='store_true', help='Rating tag is in 3D. (Needs a 2D image.)')

parser.add_argument('--2k', dest='twok', action='store_true', help='Rating tag is in 2k.')
parser.add_argument('--4k', dest='fourk', action='store_true', help='Rating tag is in 4k.')

parser.add_argument('-f', '--flat', dest='flat', action='store_true', help='Rating tag is in Scope.')
parser.add_argument('-s','--scope', dest='scope', action='store_true', help='Rating tag is in Flat.')

args = parser.parse_args()

def callSys(cmd):
    if args.dryrun:
        print(cmd)
        return 0
    else:
        hresult = os.system(cmd)

        if hresult > 0:
            print('Error: The command "%s" has returned %d.' % (cmd, hresult))
            sys.exit(1)

##########
# Prep

dcpCreator = "UF"

pngFile = ''
if type(args.image) == list:
    pngFile = args.image[0]
else:
    pngFile = args.image

pngFile = os.path.abspath(pngFile)
basePath = os.path.dirname(pngFile)
projectName = os.path.basename(os.path.splitext(pngFile)[0])

vf = ''

width, height = 0, 0
arDcp, sizeDcp = '', ''

##########
# Get image size

# Cannot have both
assert(not (args.flat and args.scope))
assert(not (args.twok and args.fourk))

# Try to find the image size
try:
    from PIL import Image
except ImportError:
    if ((args.flat or args.scope) and (args.twok or args.fourk)):
        print('No PIL or Pillow found. Need to specify aspect ratio and size. (--flat or --scope and --2k or --4k)')
        sys.quit(1)
    else:
        if args.scope and args.twok:
            width, height = 2048, 858
        if args.scope and args.fourk:
            width, height = 4096, 1716
        elif args.flat and args.twok:
            width, height = 1998, 1080
        elif args.flat and args.fourk:
            width, height = 3996, 2160
else:
    im = Image.open(pngFile)
    width, height = im.size

ar = round(width/height, 2)

if (ar == 2.39):
    if not args.scope: print('Detected scope.')
    arDcp = 'S'
elif (ar == 1.85):
    if not args.flat: print('Detected flat.')
    arDcp = 'F'
else:
    print('Warning: Non-standard aspect ratio of %.2f detected.' % ar)

if ((width == 2048 and height == 858) or (width == 1998 and height == 1080)) and not args.fourk:
    if not args.twok: print('Detected 2K.')
    sizeDcp = '2K'
elif ((width == 4096 and height == 1716) or (width == 3996 and height == 2160)) and not args.twok:
    if not args.fourk: print('Detected 4K.')
    sizeDcp = '4K'
elif args.twok or args.fourk:
    pass # Suppress the warning below
else:
    print('Warning: Non standard size of %dx%d detected.')

# Something's not DCI Scope/Flat or 2K or 4K
if not sizeDcp or not arDcp:
    arDcp = 'F-%.2f' % ar

    if args.fourk:
        sizeDcp = '4K'
        if ar == 2.39:
            vf = 'scale=w=4096:h=1716:force_original_aspect_ratio=1,'
            print('Scaling to 4K, keeping scope aspect ratio.')
        elif ar == 1.85:
            vf = 'scale=w=3996:h=2160:force_original_aspect_ratio=1,'
            print('Scaling to 4K, keeping flat aspect ratio.')
        else:
            vf = 'scale=w=4096:h=2160:force_original_aspect_ratio=1,pad=3996:2160:(ow-iw)/2:(oh-ih)/2,'
            print('Scaling to 4K and padding to full frame.')
    else: # 2K
        sizeDcp = '2K'
        if ar == 2.39:
            vf = 'scale=w=2048:h=858:force_original_aspect_ratio=1,'
            print('Scaling to 2K, keeping scope aspect ratio.')
        elif ar == 1.85:
            vf = 'scale=w=1996:h=1080:force_original_aspect_ratio=1,'
            print('Scaling to 2K, keeping flat aspect ratio.')
        else:
            vf = 'scale=w=2048:h=1080:force_original_aspect_ratio=1,pad=2048:1080:(ow-iw)/2:(oh-ih)/2,'
            print('Scaling to 2K and padding to full frame.')

if args.threed:
   arDcp += '-3D'

##########
# Make a clip from the stiff frame

tiffFolder = os.path.join(basePath, projectName + "_tiff")
if not os.path.exists(tiffFolder) and not args.dryrun:
    os.makedirs(tiffFolder)

vf += 'fade=t=in:st=0:d=%d,fade=t=out:st=%d:d=%d' % (args.fade, args.duration - args.fade, args.fade)
callSys('ffmpeg -loop 1 -i %s -t %d -filter_complex "%s" -vcodec tiff %s' % (pngFile, args.duration, vf, os.path.join(tiffFolder, '%06d.tiff')))

##########
# Convert to j2c

j2cFolder = os.path.join(basePath, projectName + "_j2c")
if not os.path.exists(j2cFolder) and not args.dryrun:
    os.makedirs(j2cFolder)
    
callSys('opendcp_j2k -i %s -o %s --rate 24 --profile cinema2k' % (tiffFolder, j2cFolder))

##########
# Mux to mxf

dcpName = projectName + "_RTG_" + arDcp + "_EN-XX_UK_" + sizeDcp + "_" + dcpCreator + "_" + datetime.datetime.now().strftime('%Y%m%d') + "_" + dcpCreator + "_SMPTE_OV"

dcpFolder = os.path.join(basePath, dcpName)
if not os.path.exists(dcpFolder) and not args.dryrun:
    os.makedirs(dcpFolder)

mxfName = os.path.join(dcpFolder, projectName + "_j2c.mxf")

if not args.threed:
    callSys('opendcp_mxf -i %s -o %s --rate 24 --n smpte' % (j2cFolder, mxfName))
else:
    callSys('opendcp_mxf -l %s -r %s -o %s --rate 24 --n smpte' % (j2cFolder, j2cFolder, mxfName))

##########
# Make DCP metadata

ret = os.path.curdir
if not args.dryrun: os.chdir(dcpFolder)
callSys('opendcp_xml --reel %s --digest OpenDCP --issuer OpenDCP --title %s --kind rating' % (mxfName, dcpName))
if not args.dryrun: os.chdir(ret)

##########
# Cleanup temp files
# TODO: This is not compatible with Windows

if not args.keep:
    callSys('find %s -name "*.%s" -print0 | xargs -0 rm' % (tiffFolder, 'tiff'))
    callSys('rmdir %s' % (tiffFolder))
    callSys('find %s -name "*.%s" -print0 | xargs -0 rm' % (j2cFolder, 'j2c'))
    callSys('rmdir %s' % (j2cFolder))

print('Success! Your rating tag is', dcpName)
