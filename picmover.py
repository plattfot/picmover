#! /usr/bin/env python
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
import pdb
try:
    # for extracting metadata from jpeg and raw image files
    from gi.repository import GExiv2
except ImportError:
    exit('You need to install gexiv2 first.')

from collections import defaultdict

from sys import argv, stderr, exit
from collections import namedtuple

##############################################
FileData = namedtuple("FileData", "date, filetype, target_path ")

__doc__ = """PicMover: \n\tSimple class that extracts metadata from an image
pool \n\tand moves them to a dir named with date and user comment.  To
run simply execute PicMover.py where the pictures are.  Flags:
verbose\t-v Created by: Fredrik "PlaTFooT" Salomonsson
plattfot@gmail.com.  """

def yesNo( x ):
    if x.lower() == 'yes' or x.lower() == 'true':
        return True
    else:
        return False

class ExifImg:
    """Extract metadata from images"""
    def model( self, metadata ):
        return metadata['Exif.Image.Model']
    def make( self, metadata ):
        return metadata['Exif.Image.Make']
    def date( self, metadata ):
        date = str(datetime.datetime.today())
        if 'Exif.Image.DateTimeOriginal' in metadata:
            date = metadata['Exif.Image.DateTimeOriginal'].split()[0]
        elif 'Exif.Photo.DateTimeOriginal' in metadata:
            date = metadata['Exif.Photo.DateTimeOriginal'].split()[0]
        else:
            print( "[Warning] Couldn't find date! Using today's date instead." )
        return date
        
class ExifMov:
    """Extract metadata from mov files"""
    def model( self, metadata ):
        return metadata['Xmp.video.Model']
    def make( self, metadata ):
        return metadata['Xmp.video.Make']
    def date( self, metadata ):
        date = str(datetime.datetime.today())
        if 'Xmp.video.DateTimeOriginal' in metadata:
            date = metadata['Xmp.video.DateTimeOriginal'].split()[0]
        else:
            print( "[Warning] Couldn't find date! Using today's date instead." )
        return date
    
class PicMover:
 
    # python constructor
    def __init__(self, path, dry_run = False, move = False, verbose = False):
        # Convert ~/ to relative path if needed.
        expanded_path = os.path.expanduser( path )
        # Init variables
        image_path = "Image"
        video_path = "Video"
        root = os.path.expanduser( "~" )
        check_if_mounted = False
        self.camera_maker = "Unknown maker" 
        self.camera_model = "Unknown model" 
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
                    print( "Camera Maker is",data[1] )
            elif data[0] == "CameraModel":
                self.camera_model = data[1]
                if verbose:
                    print( "Camera Model is",data[1] )
            elif data[0] == "Root":
                root = data[1]
                if verbose:
                    print( "Root is set to:",data[1] )
            elif data[0] == "ImagePath":
                image_path = data[1]
                if verbose:
                    print( "Image directory is set to:",data[1] )
            elif data[0] == "VideoPath":
                video_path = data[1]
                if verbose:
                    print( "Video directory is set to:",data[1] )
            elif data[0] == "SourcePath":
                self.IMAGE_POOL_PATH = data[1]
                if not os.path.ismount( data[1] ):
                    raise RuntimeError("[Error] Root path is not mounted! Abort!")
                if verbose:
                    print( "Source path is set to:",data[1])
            elif data[0] == "CheckIfMounted":
                check_if_mounted = yesNo( data[1] )
                if verbose:
                    print( "Check if root is mounted:",check_if_mounted )
        #if check_if_mounted and not os.path.ismount( root ):
        if check_if_mounted and not os.path.ismount( root ):
            raise RuntimeError("[Error] Root path is not mounted! Abort!")
        
        # Only add '/' if the *_path doesn't start with '/'
        self.TARGET_IMAGE_PATH = root + ('/' if image_path[0] != '/' else '')\
                                 + image_path
        self.TARGET_VIDEO_PATH = root + ('/' if video_path[0] != '/' else '')\
                                 + video_path 
        self.subdir_raw = 'raw/'
        self.subdir_jpg = 'JPEG/'
        self.subdir_mov = 'mov/'
        
        self.dry_run = dry_run
        self.move = move
        self.writepath = {}
        self.ignore = defaultdict(bool)
        self.mov_keys = {}
        self.img_keys = {}
        self.verbose = verbose
        raw_ext = '(3fr|ari|arw|bay|crw|cr2|cap|dcs|dcr|'\
                  'dng|drf|eip|erf|fff|iiq|k25|kdc|mdc|mef|'\
                  'mos|mrw|nef|nrw|obm|orf|pef|ptx|pxn|r3d|'\
                  'raf|raw|rwl|rw2|rwz|sr2|srf|srw|x3f)'
        self.pattern_raw = re.compile('\.{0}'.format(raw_ext), re.IGNORECASE)
        self.pattern_jpg = re.compile('\.jpe{0,1}g', re.IGNORECASE)
        self.pattern_mov = re.compile('\.mov', re.IGNORECASE)

    # checks if a directory exists, if not it creates it
    def ensureDir(self, f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            print( "Created path", f )
    # strips the path name and just return the name of the file
    # e.g path/to/file/pic.NEF -> pic.NEF
    def stripPath(self, path, filename, offset = 1):
        start = len(path)+offset
        filename = filename[start : ]
        return filename

    # First check if the path exists, if true; move the file 
    # Only if the file doesn't exists at that location 
    def move_file(self,filename, writepath ):

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
                    print( " -Moved to", writepath )
                if self.move: os.remove( filepath )
        else:
            if self.verbose:
                print( " -Moved to", writepath )
                    

    def add_path(self, metadata, exif, data ):
        # Get camera maker
        maker = exif.make( metadata )
        # Choose first ( remove corporation from nikon)
        maker = maker.split()[0]
        # Get camera model
        camera = exif.model( metadata )
        if 'NIKON' in camera:
            camera = camera.split()
            camera = camera[1]
        path = '/{0}/{1}/{2}/'.format(maker.capitalize(), camera, data.date[0:4])
        key = data.date
        path_to_events = data.target_path + path
        matches = glob.glob(path_to_events + key + '*')
        print( camera, maker )
        answer = 'n'
        # Found potential matching events 
        if len(matches):
            while( True ):
                print( "Found events matching the date. Use one of these instead?" )

                for i,m in enumerate(matches):
                    print( "- [{0}] add to: {1}"
                           .format(i, self.stripPath( path_to_events, m, 0 )))
                answer = input("- [n] to create a new.\n"
                               "- [i] to ignore this event.\n"
                               "- Type one of the options above: ")

                if answer.isdigit() and int(answer) < len(matches) :
                    event = self.stripPath( path_to_events, matches[int(answer)], 0 )
                    self.writepath[ key ] = '{0}{1}/'.format( path, event )
                    break
                elif answer == "n":
                    # Ask for name 
                    name = input('[{0}] Name of event ( {1} <name> ): '
                                 .format(data.filetype, data.date))
                    # Add date + name
                    path += '{0} {1}/'.format(data.date, name)
                    # Add path to dict
                    self.writepath[ key ] = path
                    break
                elif answer == 'i':
                    self.ignore[ key ] = True
                    break
                else:
                    print( 'Unknown option, try again.' )
       
    def add_file( self, filename, exif, filetype, target_path ):
        # go to the correct folder e.g. ~/Nikon/D7000/2011/
        # Get the metadata from the image
        metadata = GExiv2.Metadata( filename )

        # Extract usfull information from the metadata object
        date = exif.date( metadata )
        # GExiv2 format the date with : instead of -.
        date=date.replace(":","-")
        # Hash key to filename to avoid parse metadata twice
        self.img_keys[ filename ] = date
        
        if (date not in self.writepath) and (date not in self.ignore):
            data = FileData( date, filetype, target_path )
            self.add_path( metadata, exif, data )
            
    def process_file(self, filename, subdir, target_path):
    
        key = self.img_keys[filename]
        if self.ignore[ key ]:
            return

        path = target_path + self.writepath[ key ] + subdir
        # Move file to the new path
        self.move_file(filename, path )  


    def print_process(self,type_name, filename, count, total):
        print( "Processing {0} : {1} [{2}/{3}]"
               .format(type_name, filename, count, total) )

    # moves the file based on metadata (user comment and date)
    def exe(self):

        # filenames = [f for f in os.listdir(self.IMAGE_POOL_PATH) if re.search(self.pattern_raw, f) or\
        #              re.search(self.pattern_jpg, f) or\
        #              re.search(self.pattern_mov, f)]
#        pdb.set_trace()
        # Scan for paths
        if self.verbose:
            print( "[------------- Scaning for files ---------------]" )

        filenames_raw = []
        filenames_jpg = []
        filenames_mov = []
        for f in os.listdir(self.IMAGE_POOL_PATH):
            if re.search(self.pattern_raw, f):
                filenames_raw.append(f)
            elif re.search(self.pattern_jpg, f):
                filenames_jpg.append(f)
            elif re.search(self.pattern_mov, f):
                filenames_mov.append(f)
        total = len(filenames_raw) + len(filenames_jpg) + len(filenames_mov)

        if total == 0:
            print( "No files found, exit program." )
            return

        if self.verbose:
            print( "[-------------- Preping files ------------------]" )
        exif_img = ExifImg()
        exif_mov = ExifMov()

        for filename in filenames_raw:
            self.add_file(filename, exif_img, 'RAW', self.TARGET_IMAGE_PATH )

        for filename in filenames_jpg:
            self.add_file(filename, exif_img, 'JPG', self.TARGET_IMAGE_PATH )

        for filename in filenames_mov:
            self.add_file(filename, exif_mov, 'MOV', self.TARGET_VIDEO_PATH )

        if self.verbose:
            print( "[--------------- Moving files ------------------]" )

        count = 1

        for filename in filenames_raw:
            type_name = "raw image"
            self.print_process( type_name, filename, count, total )
            self.process_file(filename, self.subdir_raw, self.TARGET_IMAGE_PATH)
            count += 1

        for filename in filenames_jpg:
            type_name = "jpg image"
            self.print_process( type_name, filename, count, total )
            self.process_file(filename, self.subdir_jpg, self.TARGET_IMAGE_PATH )
            count += 1
            
        for filename in filenames_mov:
            type_name = "movie"
            self.print_process( type_name, filename, count, total )
            self.process_file(filename, self.subdir_mov, self.TARGET_VIDEO_PATH)
            count += 1
        print( "done" )

# Based on Guido van Rossu's main function
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def process(arg):
    print( arg )

def main(argv=None):

    if argv is None:
        argv = sys.argv

    parser = argparse\
        .ArgumentParser( description = "picmover: Simple program that "
                         "moves images according to metadata")
    parser.add_argument("-v", action="store_true", default=False, dest='verbose',
                        help="More text, i.e. verbose")
    parser.add_argument("-m","--mv", action="store_true", default=False, dest='move',
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

    
