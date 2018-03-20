#!/usr/bin/env python3

########################################################################
###                                                                  ###
###                            UnionFilms                            ###
###                                                                  ###
###                    Written on 2018/01/24 by KD                   ###
###                 Last modified on 2018/01/25 by KD                ###
###                                                                  ###
### Script for making rating tags from a png                         ###
### Usage: ./makeRtg.py <pathToPngFile>                              ###
###                                                                  ###
### Depends: OpenDCP, ffmpeg/libav                                   ###
###                                                                  ###
### or just drag and drop the png file onto this script              ###
###                                                                  ###
########################################################################

import os
import sys
import datetime

assert(len(sys.argv) == 2)

pngFile = sys.argv[1]
basePath = os.path.dirname(pngFile)
projectName = os.path.splitext(pngFile)[0]

tiffFolder = os.path.join(basePath, projectName + "_tiff")
if not os.path.exists(tiffFolder):
    os.makedirs(tiffFolder)

j2cFolder = os.path.join(basePath, projectName + "_j2c")
if not os.path.exists(j2cFolder):
    os.makedirs(j2cFolder)

dcpName = projectName + "_RTG_S_EN-XX_UK_2K_UF_" + datetime.datetime.now().strftime('%Y%m%d') + "_UF_SMPTE_OV"

dcpFolder = os.path.join(basePath, dcpName)
if not os.path.exists(dcpFolder):
    os.makedirs(dcpFolder)

mxfName = os.path.join(dcpFolder, projectName + "_j2c.mxf")

##########

doFFmpeg = 'ffmpeg -loop 1 -t 15 -i %s -filter_complex "fade=t=in:st=0:d=2,fade=t=out:st=13:d=2" -vcodec tiff %s' % (pngFile, os.path.join(tiffFolder, '%06d.tiff'))
os.system(doFFmpeg)

##########

doOpenDCPj2k = 'opendcp_j2k -i %s -o %s --rate 24 --profile cinema2k' % (tiffFolder, j2cFolder)
os.system(doOpenDCPj2k)

##########

doOpenDCPmxf = 'opendcp_mxf -i %s -o %s --rate 24 --n smpte' % (j2cFolder, mxfName)
os.system(doOpenDCPmxf)

##########

os.chdir(dcpFolder)
doOpenDCPmxf = 'opendcp_xml --reel %s --digest OpenDCP --kind rating --title %s' % (mxfName, dcpName)
os.system(doOpenDCPmxf)

##########

os.chdir(tiffFolder)
#os.system('find . -name "*.tiff" -print0 | xargs -0 rm')

os.chdir(j2cFolder)
os.system('find . -name "*.j2c" -print0 | xargs -0 rm')
