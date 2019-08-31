import os
from pymediainfo import MediaInfo
import configparser
import ast
import logging
import time
import pathlib
def getvcodec(filename):
    media_info = MediaInfo.parse(filename)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            return(track.format)
    return(False)
def getcolor(filename):
    media_info = MediaInfo.parse(filename)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            return(track.color_primaries)
    return(False)
def getbit(filename):
    media_info = MediaInfo.parse(filename)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            return(track.Bit_depth)
    return(False)
def getacodec(filename):
    media_info = MediaInfo.parse(filename)
    for track in media_info.tracks:
        if track.track_type == 'Audio':
            return(track.format)
    return(False)
def getoptivcodec(codec, hq):
    if codec == False:
        return(False)
    elif codec.lower().replace("-", "") == "vc1":
        #vc1 encoding is not supported by ffmpeg so codec is changed to h.264
        return('libx264')
    elif codec.lower().replace("-", "") in "wmv":
        #upgrades codec to wmv3 if wmv1/2 who wants to use outdated codecs anyway
        return('wmv3')
    elif codec.lower().replace("-", "") == "mpeg4":
        return('libxvid')
    elif codec.lower().replace("-", "") == "msmpeg4" or codec.lower().replace("-", "") == "msmpeg4v1" or codec.lower().replace("-", "") == "msmpeg4v2" or codec.lower().replace("-", "") == "msmpeg4v3":
        #Should encode to msmpeg4v3 there is no standalose encoder for V2 and V1 can not be encoded
        return('msmpeg4')
    elif codec.lower().replace("-", "") == "h264" or codec.lower().replace("-", "") == "avc" or codec.lower().replace("-", "") == "h264":
        return('libx264')
    elif codec.lower().replace("-", "") == "hvec" or codec.lower().replace("-", "") == "h265" or codec.lower().replace("-", "") == "h.265":
        return('libx265')
    elif codec.lower().replace("-", "") == "mpeg2" or codec.lower().replace("-", "") == "mpeg2video":
        return('mpeg2video')
    elif codec.lower().replace("-", "") == "vp9":
        return('libvpx-vp9')
    else:
        #h.264 is a good fallback
        if hq == True:
            return('libx265')
        return('libx264')
def getoptiacodec(codec, hq):
    if codec == False:
        return(False)
    elif codec.lower().replace("-", "") == "aac" or codec.lower().replace("-", "") == "aaclc":
        #if compiled with non free libfdk_aac is the best aac encoder
        if getconfig(nonfree) == True:
            return('libfdk_aac')
        return('aac')
    elif codec.lower().replace("-", "") == "heaac":
        #if compiled with non free libfdk_aac is the best aac encoder
        if getconfig(nonfree) == True:
            return('libfdk_aac')
        return('libaacplus')
    elif codec.lower().replace("-", "") == "eac3":
        return('eac3')
    elif codec.lower().replace("-", "") == "flac":
        return('flac audio.flac')
    elif codec.lower().replace("-", "") == "mp3":
        return('libmp3lame')
    elif codec.lower().replace("-", "") == "mp2":
        return('libtwolame')
    elif codec.lower().replace("-", "") == "ac3":
        return('ac3')
    elif codec.lower().replace("-", "") == "wmav2":
        return('wmav2')
    elif codec.lower().replace("-", "") == "alac":
        return('flac')
    elif codec.lower().replace("-", "") == "opus":
        return('libopus')
    else:
        #aac is a goodfallback
        if hq == True:
            return('libopus')
        if getconfig(nonfree) == True:
            return('libfdk_aac')
        return('aac')
def getconfig(info):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return(config['settings'][info])

def listgen(info):
    output = ['']
    output = ast.literal_eval(getconfig(info))
    output = [n.strip() for n in output]
    return(output)

def isVideo(file):
    try:
        filename, ext = file.rsplit(".", 1)
    except:
        filename, ext = file, ''
    if ext in listgen('videoext'):
        return(True)
    return(False)

def isHDR(filename):
    global codec
    isHDR = False
    color = getcolor(filename)
    bit = getbit(filename)
    try:
        if "BT.2020" in color:
            logging.info("{} uses BT.2020 color space and is HDR.".format(filename))
            return(True)
    except:
        logging.info("Warning No color_primaries String in {}".format(filename))
    try:
        if "10" in bit:
            logging.info("{} uses 10 bit color and is HDR.".format(filename))
            return(True)
    except:
        logging.info("Warning No bit_depth String in {}".format(filename))
    logging.info("File {} is not an HDR Video, Does not use the BT.2020 color space, or has already been converted".format(filename))
    return(False)
did = False
number = 0
done = ['']
logging.basicConfig(filename='batchtonemapping.log', filemode='w', format='%(levelname)s - %(message)s', level=logging.DEBUG)

for path, subdirs, files in os.walk(getconfig('path')):
    for name in files:
        currentfile = '{}/{}'.format(path, name)
        if currentfile in done:
            break
        done.append(currentfile)
        try:
            filename, fileext = currentfile.rsplit(".", 1)
        except:
            filename, fileext = currentfile, ''
        logging.info("Testing {}". format(currentfile))
        if isVideo(currentfile) == True:
            logging.info('Currentfile is a video')
            if isHDR(currentfile) == True:
                did = True
                number = number + 1
                os.system ('ffmpeg -i "{}" -max_muxing_queue_size 40000 -c copy -map 0 -vf zscale=transfer=linear,tonemap=tonemap=hable:param=1.0:desat=0:peak=10,zscale=transfer=bt709,format=yuv420p -c:v {} "{}"'.format(currentfile, getoptivcodec(getvcodec(currentfile), getconfig('hq')), filename + "tmp." + fileext))
                if getconfig("deleteorig") == True:
                    os.remove(currentfile)
                    os.rename(filename + "tmp." + fileext, currentfile)
                else:
                    os.rename(currentfile, filename + ".SDR." + fileext)
                    os.rename(filename + "tmp." + fileext, filename + ".SDR." + fileext)

if did == True:
    logging.info('Tone Maped {} Files'.format(number))
elif did == False:
    logging.info('Did not find any files to tone map')
else:
    logging.info("I Dont feel so good Mr. Stark....")
