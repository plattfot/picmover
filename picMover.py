#! /usr/bin/env python2
import pyexiv2 # for extracting metadata from jpeg and raw image files
import os
import shutil # moving and deleting files
import glob   # get files from a directory
# Should be read from a .config file later on
import sys
import argparse
import datetime
import re

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
    def __init__(self, path, verbose = False):
        # Convert ~/ to relative path if needed.
        expanded_path = os.path.expanduser( path )
        # Init variables
        image_path = "Bilder"
        video_path = "Video"
        root = os.path.expanduser( "~" )
        self.camera_maker = "Nikon" 
        self.camera_model = "D7000" 
        self.IMAGE_POOL_PATH = os.getcwd()
        # Read settings
        f = open( expanded_path, "r")
        for line in f:
            #data = re.findall(r'.*[ ]',line)
            data = line.split()
            # Check if data has no entries
            if len(data) == 0:
                continue
            if data[0] == "CameraMaker":
                self.camera_maker = data[1]
                if verbose:
                    print "Camera Maker is",data[1]
            elif data[0] == "CameraModel":
                self.camera_model = data[1]
                if verbose:
                    print "Camera Model is",data[1]
            elif data[0] == "Root":
                root = data[1]
                if not os.path.ismount( root ):
                    raise RuntimeError("[Error] Root path is not mounted! Abort!")
                if verbose:
                    print "Root is set to",data[1]
            elif data[0] == "ImagePath":
                image_path = data[1]
                if verbose:
                    print "Image directory is",data[1]
            elif data[0] == "VideoPath":
                video_path = data[1]
                if verbose:
                    print "Video directory is",data[1]
            elif data[0] == "SourcePath":
                self.IMAGE_POOL_PATH = data[1]
                if verbose:
                    print "Source path is set to",data[1]

        # print "home path = ", ROOT_PATH
        # Only add '/' if the *_path doesn't start with '/'
        self.TARGET_IMAGE_PATH = root + ('/' if image_path[0] != '/' else '') + image_path
        self.TARGET_VIDEO_PATH = root + ('/' if video_path[0] != '/' else '') + video_path 
      
        self.writepath = {}
        self.mov_keys = {}
        self.img_keys = {}
        self.verbose = verbose
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
    def move_file(self,filename, writepath ):
        if (filename.find(".NEF") > -1):
            writepath += "raw/"
        elif (filename.find(".jpg") > -1):
            writepath += "JPEG/"
        elif (filename.find(".MOV") > -1):
            writepath += "mov/"

   
        # Then move it to the new location
        # if that succeeded remove the image from the image pool 
        filepath = self.IMAGE_POOL_PATH+'/'+filename
        writepath = writepath + filename
        if self.dry_run != True:
            # check to see if the directory exists, if not create it
            self.ensure_dir(writepath)

            if not os.path.exists(writepath):
                shutil.copy2(filepath,writepath)
                if self.verbose:
                    print " -Moved to", writepath
                if self.move: os.remove( filepath )
        else:
            if self.verbose:
                print " -Moved to", writepath
                    

    def add_path(self, metadata, date, img_type ):
        #userComment =  metadata['Exif.Photo.UserComment'].human_value
        #userComment = userComment.strip()
            
        camera = metadata['Exif.Image.Model'].human_value
        camera = camera.split()
      
        path = '/' + camera[0].capitalize()+'/'+ \
            camera[1]+'/'+                       \
            str( date.year )+'/'
        key = str( date.date() )
        # Ask for name 
        name = raw_input("["+img_type+"] Name of event ( " + key +" <name> ): ")
        # Add date + name
        path += str(date.date() ) + ' ' + name +'/' 

        # Add path to dict
        self.writepath[ key ] = path
       
    def add_path_img( self, filename, img_type ):
        # go to the correct folder e.g. ~/Nikon/D7000/2011/
        # Get the metadata from the image
        metadata = pyexiv2.ImageMetadata(filename)
        metadata.read()
        # Extract usfull information from the metadata object
        date = metadata['Exif.Image.DateTime'].value

        key = str( date.date() )
        
        # Hash key to filename to avoid parse metadata twice
        self.img_keys[ filename ] = key

        if key not in self.writepath:
            self.add_path( metadata, date, img_type )

    def add_path_mov( self, filename ):
        
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
               
        if( len(date)== 0 ):
            print "Didn't find any date"
            date = raw_input("[MOV] Please type in year (YYYY): ")
            date += '-' + raw_input("[MOV] Please type in month (MM): ")
            date += '-' + raw_input("[MOV] Please type in day (DD): ")
        # Hash realname to avoid parsing the metadata twice
        self.mov_keys[ realname ] = date

        if date not in self.writepath :
            path = '/' + self.camera_maker +'/'+ self.camera_model + '/' + date[0:4] + '/'
            name = raw_input("[MOV] Name of event ( " + date +" <name> ): ")
            # Add date + name
            path += date + ' ' + name +'/' 

            
    def process_img(self,filename):
    
        key = self.img_keys[filename]
        path = self.TARGET_IMAGE_PATH + self.writepath[ key ]
        # Move file to the new path
        self.move_file(filename, path )  

    def process_mov(self,filename):
        
        date = self.mov_keys[filename]
        if date in self.writepath:

            path = self.TARGET_VIDEO_PATH + self.writepath[ date ]
            self.move_file(filename, path )
        else :
            raise RunTimeError( "Didn't find the path matching the date!")


    def print_process(self,type_name, index, filenames, filenames_size):
        print "Processing",type_name ,":",filenames[index], \
            " ["+str(index+1)+"/"+str(filenames_size)+"]"

    # moves the file based on metadata (user comment and date)
    def exe(self):
        filenames =  glob.glob(self.IMAGE_POOL_PATH+'/'+'*.NEF')
        filenames += glob.glob(self.IMAGE_POOL_PATH+'/'+'*.jpg')       
        filenames += glob.glob(self.IMAGE_POOL_PATH+'/'+'*.MOV')  

        filenames_size = len(filenames)
        if filenames_size == 0 : 
            print "No files found, exit program."
            return
        # Scan for paths
        if self.verbose:
            print "[------------- Scaning for paths ---------------]"

        for i in range(filenames_size):
            
            filenames[i] = self.strip_path(self.IMAGE_POOL_PATH,
                                           filenames[i])
            # if filenames is a raw file
            if not (filenames[i].find(".NEF") == -1):
                self.add_path_img(filenames[i], "NEF")
            elif not (filenames[i].find(".jpg") == -1):
                self.add_path_img(filenames[i], "JPG")
            elif not (filenames[i].find(".MOV") == -1):
                self.add_path_mov(filenames[i])
            else :
                print "File not recognised"
        if self.verbose:
            print "[---------------- Moving files -----------------]"

        for i in range(filenames_size):
            
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
                # fix to move mov to / my_writepath/Mov/
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

    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description = "PicMover: Simple program that moves"
                                     " images\naccording to metadata")
    parser.add_argument("-v", action="store_true", default=False, dest='verbose',
                        help="More text, i.e. verbose")
    parser.add_argument("-mv", action="store_true", default=False, dest='move',
                        help="Moves the target images, not just copying them to the target position")
    parser.add_argument("-n", action="store_true", default=False, dest='dry_run',
                        help="Dry run, execute all actions but doesn't move any files. Good for testing.")
    ### parser.add_argument("--camera-model", default='D7000', dest='camera_model',
    ###                     help="Set camera model incase no model can be found in metadata.")
    ### parser.add_argument("--camera-maker", default='Nikon', dest='camera_maker',
    ###                     help="Set camera manufacture incase no manufactor can be found in metadata.")
    parser.add_argument("-c", default='~/.picmoverrc', dest='path',
                        help="Config file to load.")

    result = parser.parse_args()
    pm = PicMover( result.path, result.verbose )
    # pm.verbose      = result.verbose
    # pm.move         = result.move
    # pm.dry_run      = result.dry_run
    # pm.camera_maker = result.camera_maker
    # pm.camera_model = result.camera_model
    # pm.path         = result.path
    #pm.exe()
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
