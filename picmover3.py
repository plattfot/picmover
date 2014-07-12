#!/usr/bin/python
# Copyright 2013-2014 Fredrik Salomonsson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 

import os
import shutil # moving and deleting files
import glob   # get files from a directory
# Should be read from a .config file later on
import sys
import argparse
import datetime
import re
try:
    # for extracting metadata from jpeg and raw image files
    from gi.repository import GExiv2
except ImportError:
    exit('You need to install gexiv2 first.')

from collections import defaultdict
# ############# Hachoir stuff ##################
# from hachoir_core.error import HachoirError
# from hachoir_core.cmd_line import unicodeFilename
# from hachoir_parser import createParser
# from hachoir_core.tools import makePrintable
# from hachoir_metadata import extractMetadata
# from hachoir_core.i18n import getTerminalCharset
# from sys import argv, stderr, exit
##############################################


__doc__ = """PicMover: \n\tSimple class that extracts metadata from an image pool \n\tand moves them to a dir named with date and user comment.
To run simply execute PicMover.py where the pictures are.
Flags:
verbose\t-v
Created by: Fredrik "PlaTFooT" Salomonsson plattfot@gmail.com.
"""

def yesNo( x ):
    if x.lower() == 'yes' or x.lower() == 'true':
        return True
    else:
        return False

class PicMover:
 
    # python constructor
    def __init__(self, path, dry_run = False, move = False, verbose = False):
        print( "[Warning] Importing videos are currently not supported with the python 3 version!")
        # Convert ~/ to relative path if needed.
        expanded_path = os.path.expanduser( path )
        # Init variables
        image_path = "Bilder"
        video_path = "Video"
        root = os.path.expanduser( "~" )
        check_if_mounted = False
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
                    print( "Camera Maker is",data[1])
            elif data[0] == "CameraModel":
                self.camera_model = data[1]
                if verbose:
                    print( "Camera Model is",data[1])
            elif data[0] == "Root":
                root = data[1]
                if verbose:
                    print( "Root is set to:",data[1])
            elif data[0] == "ImagePath":
                image_path = data[1]
                if verbose:
                    print( "Image directory is set to:",data[1])
            elif data[0] == "VideoPath":
                video_path = data[1]
                if verbose:
                    print( "Video directory is set to:",data[1])
            elif data[0] == "SourcePath":
                self.IMAGE_POOL_PATH = data[1]
                if not os.path.ismount( data[1] ):
                    raise RuntimeError("[Error] Root path is not mounted! Abort!")
                if verbose:
                    print( "Source path is set to:",data[1])
            elif data[0] == "CheckIfMounted":
                check_if_mounted = yesNo( data[1] )
                if verbose:
                    print( "Check if root is mounted:", check_if_mounted)
        #if check_if_mounted and not os.path.ismount( root ):
        if check_if_mounted and not os.path.ismount( root ):
            raise RuntimeError("[Error] Root path is not mounted! Abort!")
        
        # Only add '/' if the *_path doesn't start with '/'
        self.TARGET_IMAGE_PATH = root + ('/' if image_path[0] != '/' else '') + image_path
        self.TARGET_VIDEO_PATH = root + ('/' if video_path[0] != '/' else '') + video_path 
        self.dry_run = dry_run
        self.move = move
        self.writepath = {}
        self.ignore = defaultdict(bool)
        self.mov_keys = {}
        self.img_keys = {}
        self.verbose = verbose
    # end __init__
        

    # checks if a directory exists, if not it creates it
    def ensureDir(self, f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            print( "Created path", f)
    # strips the path name and just return the name of the file
    # e.g path/to/file/pic.NEF -> pic.NEF
    def stripPath(self, path, filename, offset = 1):
        start = len(path)+offset
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
            self.ensureDir(writepath)

            if not os.path.exists(writepath):
                shutil.copy2(filepath,writepath)
                if self.verbose:
                    print( " -Moved to", writepath)
                if self.move: os.remove( filepath )
        else:
            if self.verbose:
                print( " -Moved to", writepath)
                    

    def add_path(self, metadata, date, img_type ):
        #userComment =  metadata['Exif.Photo.UserComment'].human_value
        #userComment = userComment.strip()
        # Get camera maker
        maker = metadata['Exif.Image.Make']
        # Choose first ( remove corporation from nikon)
        maker = maker.split()[0]
        # Get camera model
        camera = metadata['Exif.Image.Model']
        if 'NIKON' in camera:
            camera = camera.split()
            camera = camera[1]
        path = '/' + maker.capitalize()+'/'+ \
            camera+'/'+                      \
            date[0:4]+'/'
        key = date
        path_to_events = self.TARGET_IMAGE_PATH + path
        matches = glob.glob(path_to_events + key + '*')
        print( camera, maker)
        answer = 'n'
        # Found potential matching events 
        if len(matches):
            print( "Found events matching the date. Use one of these instead?")

            for i,m in enumerate(matches):
                print( "[" + str(i) + "] " + self.stripPath( path_to_events, m, 0 ))
                answer = input("Type the number matching the event, "
                                   "[n] to create a new and "
                                   "[i] to ignore this event: ")
                
        if answer.isdigit() and int(answer) < len(matches) :
            self.writepath[ key ] = '/' + maker.capitalize()+'/'+ \
                                    camera+'/'+                   \
                                    date[0:4]+ '/' +\
                                    self.stripPath( path_to_events, 
                                                    matches[int(answer)], 0 ) + '/'
        elif answer == "n":
            # Ask for name 
            name = input("["+img_type+"] Name of event ( " + key +" <name> ): ")
            
            # Add date + name
            path += date  + ' ' + name +'/' 
            
            # Add path to dict
            self.writepath[ key ] = path
        else:
            self.ignore[ key ] = True
       
    def add_path_img( self, filename, img_type ):
        # go to the correct folder e.g. ~/Nikon/D7000/2011/
        # Get the metadata from the image
        metadata = GExiv2.Metadata(filename)
        #        metadata.read()
        # Extract usfull information from the metadata object
        date = str(datetime.datetime.today())
        if 'Exif.Image.DateTime' in metadata:
            date = metadata['Exif.Image.DateTime'].split()[0]
        elif 'Exif.Photo.DateTimeOriginal' in metadata:
            date = metadata['Exif.Photo.DateTimeOriginal'].split()[0]
        else:
            print( "[Warning] Couldn't find date! Using today's date instead.")
        # GExiv2 format the date with : instead of -.
        date=date.replace(":","-")
        # Hash key to filename to avoid parse metadata twice
        self.img_keys[ filename ] = date

        if (date not in self.writepath) and (date not in self.ignore):
            self.add_path( metadata, date, img_type )

#    def add_path_mov( self, filename ):
        # Kind of complicated way of of checking the date on the movie
        # A naive way to move the .mov file
            
       #  filename, realname = unicodeFilename(filename), filename
       #  parser = createParser(filename, realname)
       #  if not parser:
       #      print( >>stderr, "Unable to parse file")
       #      exit(1)
       #  try:
       #      metadata = extractMetadata(parser)
       #  except HachoirError, err:
       #      print( "Metadata extraction error: %s" % unicode(err))
       #      metadata = None
       #  if not metadata:
       #      print( "Unable to extract metadata")
       #      exit(1)

       #  text = metadata.exportPlaintext()
       # ## charset = getTerminalCharset()
       # ## for line in text:
       #  test_str = "Creation date: "
       #  start = len(test_str)
       #  end = len("yyyy-mm-dd")
       #  for line in text: 
       #      pos = line.find(test_str)
       #      if  pos > -1 :
       #         date = line[start + pos:start + pos + end]
               
       #  if( len(date)== 0 ):
       #      print( "Didn't find any date")
       #      date = input("[MOV] Please type in year (YYYY): ")
       #      date += '-' + input("[MOV] Please type in month (MM): ")
       #      date += '-' + input("[MOV] Please type in day (DD): ")
       #  # Hash realname to avoid parsing the metadata twice
       #  self.mov_keys[ realname ] = date

       #  if date not in self.writepath and date not in self.ignore:
       #      path = '/' + self.camera_maker +'/'+ self.camera_model + '/' + date[0:4] + '/'
       #      name = input("[MOV] Name of event ( " + date +" <name> ): ")
       #      # Add date + name
       #      path += date + ' ' + name +'/' 
       #      self.writepath[ date ] = path
            
    def process_img(self,filename):
    
        key = self.img_keys[filename]
        if self.ignore[ key ]:
            return

        path = self.TARGET_IMAGE_PATH + self.writepath[ key ]
        # Move file to the new path
        self.move_file(filename, path )  

#    def process_mov(self,filename):
        # key = self.mov_keys[filename]
        # if self.ignore[ key ]:
        #     return # Do nothing

        # if key in self.writepath:
        #     path = self.TARGET_VIDEO_PATH + self.writepath[ key ]
        #     self.move_file(filename, path )
        # else :
        #     raise RunTimeError( "Didn't find the path matching the date!")


    def print_process(self,type_name, index, filenames, filenames_size):
        print( "Processing",type_name ,":",filenames[index],
               " ["+str(index+1)+"/"+str(filenames_size)+"]")

    # moves the file based on metadata (user comment and date)
    def exe(self):
        filenames =  glob.glob(self.IMAGE_POOL_PATH+'/'+'*.NEF')
        filenames += glob.glob(self.IMAGE_POOL_PATH+'/'+'*.jpg')       
        filenames += glob.glob(self.IMAGE_POOL_PATH+'/'+'*.MOV')  

        filenames_size = len(filenames)
        if filenames_size == 0 : 
            print( "No files found, exit program.")
            return
        # Scan for paths
        if self.verbose:
            print( "[------------- Scaning for paths ---------------]")

        for i in range(filenames_size):
            
            filenames[i] = self.stripPath(self.IMAGE_POOL_PATH,
                                           filenames[i])
            # if filenames is a raw file
            if not (filenames[i].find(".NEF") == -1):
                self.add_path_img(filenames[i], "NEF")
            elif not (filenames[i].find(".jpg") == -1):
                self.add_path_img(filenames[i], "JPG")
            elif not (filenames[i].find(".MOV") == -1):
                print( "[Warning] Found mov file, cannot import it!" )
            #     self.add_path_mov(filenames[i])
            else :
                print( "File not recognised")
        if self.verbose:
            print( "[---------------- Moving files -----------------]")

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
                pass
                # # fix to move mov to / my_writepath/Mov/
                # type_name = "movie"
                # self.print_process(type_name,i,filenames,filenames_size)
                # self.process_mov(filenames[i])
            else :
                print( "File not recognised")
                
        print( "done")

# Based on Guido van Rossu's main function
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def process(arg):
    print( arg)

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
    pm = PicMover( result.path, 
                   verbose = result.verbose, 
                   dry_run = result.dry_run,
                   move = result.move )
    # pm.verbose      = result.verbose
    # pm.move         = result.move
    # pm.dry_run      = result.dry_run
    # pm.camera_maker = result.camera_maker
    # pm.camera_model = result.camera_model
    pm.exe()
    return 0
    
if __name__ == "__main__":
    sys.exit(main())

    
