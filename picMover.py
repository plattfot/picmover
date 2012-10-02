#! /usr/bin/env python2
import pyexiv2 # for extracting metadata from jpeg and raw image files
import os
import shutil # moving and deleting files
import glob   # get files from a directory
# Should be read from a .config file later o
import sys
import argparse
import datetime

############# Hachoir stuff ##################
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import getTerminalCharset
from sys import argv, stderr, exit
##############################################


__doc__ = """PicMover: \n\tSimple class that extracts metadata from an image pool \n\tand moves them to a dir named with date and user comment.
To run simply execute PicMover.py where the pictures are.
Flags:
verbose\t-v
Created by: Fredrik "PlaTFooT" Salomonsson plattfot@gmail.com.
"""
class PicMover:
 
    # python constructor
    def __init__(self):
        if os.getenv("PMV_ROOT")==None:
            if os.path.ismount( "/media/Valhalla" ):
                ROOT_PATH = "/media/Valhalla"
            else:
                raise RunTimeError("[Error] Default path is not mounted! Abort!")

        else:
            # Set en path to Root
            ROOT_PATH = os.getenv("PMV_ROOT")

        print "home path = ", ROOT_PATH
        self.TARGET_IMAGE_PATH = ROOT_PATH+'/Bilder' 
        self.TARGET_VIDEO_PATH = ROOT_PATH+'/Video' 
        self.IMAGE_POOL_PATH = os.getcwd() # for now
        self.WRITEPATH = []
        self.verbose = False
        self.move = False
    # checks if a directory exists, if not it creates it
    def ensure_dir(self, f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            print "Created path", f
    # strips the path name and just return the name of the file
    # e.g path/to/file/pic.NEF -> pic.NEF
    def strip_path(self, path, filename):
        start = len(path)+1
        filename = filename[start : ]
        return filename

    # First check if the path exists, if true; move the file 
    # Only if the file doesn't exists at that location 
    def move_file(self,filename, root_path ):
        writepath = root_path + self.WRITEPATH
        if (filename.find(".NEF") > -1):
            writepath += "raw/"
        elif (filename.find(".jpg") > -1):
            writepath += "JPEG/"
        elif (filename.find(".MOV") > -1):
            writepath += "mov/"

        # check to see if the directory exists, if not create it
        # self.ensure_dir(writepath)
        
        # Then move it to the new location
        # if that succeeded remove the image from the image pool 
        filepath = self.IMAGE_POOL_PATH+'/'+filename
        writepath = writepath + filename
        print "From ", filepath, "\n", "To ", writepath
        # if not os.path.exists(writepath):
        #     shutil.copy2(filepath,writepath)
        #     if self.verbose:
        #         print "Moved", filename
        #         print "To", writepath
        #     if self.move: os.remove(filepath)
            
    def check_if_in_us(self, date):
        start_date = datetime.datetime(2011,01,31)
        end_date = datetime.datetime(2011,05,23)

        if start_date < date < end_date:
            usa = str(start_date.date() )  +" USA tripp/"
        else : 
            usa =""

        self.WRITEPATH += usa

    def process_img(self,filename):
    
        # go to the correct folder e.g. ~/Nikon/D7000/2011/
            # Get the metadata from the image
        metadata = pyexiv2.ImageMetadata(filename)
        metadata.read()
        # Extract usfull information from the metadata object
        date = metadata['Exif.Image.DateTime'].value
        userComment =  metadata['Exif.Photo.UserComment'].human_value
        userComment = userComment.strip()
            
        camera = metadata['Exif.Image.Model'].human_value
        camera = camera.split()
      
        # go to the correct folder e.g. ~/Nikon/D7000/2011/
        self.WRITEPATH = '/' + camera[0].capitalize()+'/'+     \
            camera[1]+'/'+                  \
            str( date.year )+'/'
        
        # create the folder name for the image e.g 2011-02-21 Test
        imageDir = str(date.date() ) + ' ' + userComment +'/' 
        self.check_if_in_us(date)
        self.WRITEPATH = self.WRITEPATH + imageDir
        
        #print filename
        # Move file to the new path
        self.move_file(filename, self.TARGET_IMAGE_PATH )  

    def print_process(self,type_name, index, filenames, filenames_size):
        print "Processing",type_name ,":",filenames[index], \
            " ["+str(index+1)+"/"+str(filenames_size)+"]"

    def process_mov(self,filename):
        # Kind of complicated way of of checking the date on the movie
        # A naive way to move the .mov file

        filename, realname = unicodeFilename(filename), filename
        parser = createParser(filename, realname)
        if not parser:
            print >>stderr, "Unable to parse file"
            exit(1)
        try:
            metadata = extractMetadata(parser)
        except HachoirError, err:
            print "Metadata extraction error: %s" % unicode(err)
            metadata = None
        if not metadata:
            print "Unable to extract metadata"
            exit(1)

        text = metadata.exportPlaintext()
       ## charset = getTerminalCharset()
       ## for line in text:
        test_str = "Creation date: "
        start = len(test_str)
        end = len("yyyy-mm-dd")
        for line in text: 
            pos = line.find(test_str)
            if  pos > -1 :
               date = line[start + pos:start + pos + end]
        if(len(date)!= 0):
            #date = datetime.datetime(int(date[0:4]), \ 
            #                         int(date[5:7]), \
            #                         int(date[8:10]))
            if self.WRITEPATH.find(date) > -1 :
                self.move_file(filename, self.TARGET_VIDEO_PATH )
               
            else :
                #if os.getenv("PMV_CAMERA_MODEL")==None:
                    

                print "Error: .Mov and target path missmatched!"
                
        else :
            print "Error: Didn't find a creation date!"
    # moves the file based on metadata (user comment and date)
    def exe(self):
        filenames =  glob.glob(self.IMAGE_POOL_PATH+'/'+'*.NEF')
        filenames += glob.glob(self.IMAGE_POOL_PATH+'/'+'*.MOV')  
        filenames += glob.glob(self.IMAGE_POOL_PATH+'/'+'*.jpg')       
        filenames_size = len(filenames)
        if filenames_size == 0 : print "No files found"
        for i in range(filenames_size):
            
            filenames[i] = self.strip_path(self.IMAGE_POOL_PATH,
                                           filenames[i])
            # if filenames is a raw file
            if not (filenames[i].find(".NEF") == -1):
                type_name = "raw image"
                self.print_process(type_name,i,filenames,filenames_size)
                self.process_img(filenames[i])
            elif not (filenames[i].find(".jpg") == -1):
                type_name = "jpg image"
                self.print_process(type_name,i,filenames,filenames_size)
                self.process_img(filenames[i])
            elif not (filenames[i].find(".MOV") == -1):
                # fix to move mov to / WRITEPATH/Mov/
                type_name = "movie"
                self.print_process(type_name,i,filenames,filenames_size)
                self.process_mov(filenames[i])
            else :
                print "File not recognised"
                
        print "done"

# Based on Guido van van Rossu's main function
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def process(arg):
    print arg

def main(argv=None):
    pm = PicMover()
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description = "PicMover: Simple program that moves images\naccording to metadata")
    parser.add_argument("-v", action="store_true", default=False, dest='verbose',
                        help="More text, i.e. verbose")
    parser.add_argument("-mv", action="store_true", default=False, dest='move',
                        help="Moves the target images, not just copying them to the target position")
    result = parser.parse_args()
    pm.verbose = result.verbose
    pm.move = result.move
    pm.exe()
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
