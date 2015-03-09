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
# For gps
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from collections import defaultdict

from sys import argv, stderr, exit
from collections import namedtuple

##############################################
FileData = namedtuple("FileData", "key, date, make, model, filetype, target_path")

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
def getMetadata( metadata, key ):
    if key in metadata:
        return metadata[key]
    else:
        print("[Error] Exif data {0} doesn't exist in img! Returning \"Unknown\".".format(key))
        return "Unknown"

class ExifImg:
    """Extract metadata from images"""
    def model( self, metadata ):
        model = getMetadata( metadata, 'Exif.Image.Model')
        if 'NIKON' in model:
            model = model.split()
            model = model[1]
        return model
    def make( self, metadata ):
        make = getMetadata( metadata, 'Exif.Image.Make')
        if 'NIKON' in make:
            # Choose first ( remove corporation from nikon)
            make = make.split()[0]
        return make

    def date( self, metadata ):
        if 'Exif.Image.DateTimeOriginal' in metadata:
            date = metadata['Exif.Image.DateTimeOriginal'].split()[0]
        elif 'Exif.Photo.DateTimeOriginal' in metadata:
            date = metadata['Exif.Photo.DateTimeOriginal'].split()[0]
        else:
            print( "[Warning] Couldn't find date! Using today's date instead." )
            date = str(datetime.datetime.today()).split()[0]
        return date
    def gps(self, metadata ):
        if 'Exif.GPSInfo.GPSLatitude' in metadata and\
           'Exif.GPSInfo.GPSLongitude' in metadata:
            return [metadata.get_gps_latitude(), metadata.get_gps_longitude()]
        else:
            return []

class ExifMov:
    """Extract metadata from mov files"""
    def __init__(self):
        self.apple_re = re.compile("Apple[0-9+.]+")
        self.gps_re = re.compile("([+-][0-9]+\.[0-9]+)([+-][0-9]+\.[0-9]+)")
        
    def model( self, metadata ):
        return getMetadata( metadata, 'Xmp.video.Model')
    def make( self, metadata ):
        make = getMetadata( metadata, 'Xmp.video.Make')
        # For iphone 4, apple appends some sort of id after the make
        # so just remove that.
        if re.match(self.apple_re, make ):
            make = 'Apple'
        return make
    def date( self, metadata ):
        if 'Xmp.video.DateTimeOriginal' in metadata:
            date = metadata['Xmp.video.DateTimeOriginal'].split()[0]
        elif 'Xmp.video.CreateDate' in metadata:
            date = metadata['Xmp.video.CreateDate'].split('T')[0]
        else:
            print( "[Warning] Couldn't find date! Using today's date instead." )
            date = str(datetime.datetime.today()).split()[0]
        return date

    def gps(self, metadata ):
        if 'Xmp.video.GPSCoordinates' in metadata:
            coords_raw = metadata['Xmp.video.GPSCoordinates']
            match = re.match(self.gps_re, coords_raw)
            if match is not None:
                return [match.group(1),match.group(2)]
        else:
            return []
    
class PicMover:
 
    # python constructor

    def __init__(self, path, gps_option, dry_run = False, move = False, 
                 verbose = False, date_only = False, ignore_all = False ):
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
        self.date_only = date_only
        self.ignore_all = ignore_all
        self.dry_run = dry_run
        self.move = move
        self.writepath = {}
        self.ignore = defaultdict(bool)
        self.mov_keys = {}
        self.img_keys = {}
        self.verbose = verbose
        self.ignore_always = ignore 
        raw_ext = '(3fr|ari|arw|bay|crw|cr2|cap|dcs|dcr|'\
                  'dng|drf|eip|erf|fff|iiq|k25|kdc|mdc|mef|'\
                  'mos|mrw|nef|nrw|obm|orf|pef|ptx|pxn|r3d|'\
                  'raf|raw|rwl|rw2|rwz|sr2|srf|srw|x3f)'
        self.pattern_raw = re.compile('\.{0}'.format(raw_ext), re.IGNORECASE)
        self.pattern_jpg = re.compile('\.jpe{0,1}g', re.IGNORECASE)
        self.pattern_mov = re.compile('\.mov', re.IGNORECASE)

        self.setGPS( gps_option )
    # checks if a directory exists, if not it creates it
    def ensureDir(self, f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            print( "Created path", f )

    def setGPS(self, gps_option ):
        if len(gps_option):
            self.gps_option = gps_option
            self.use_gps = True
        else:
            self.use_gps = False
            
    # Returns an xml tree of the search
    def gpsQuery( self, coords ):
         html = urlopen("http://nominatim.openstreetmap.org/reverse?format=xml&lat={0}&lon={1}".format( coords[0], coords[1]))
         return ET.fromstring( html.read() )
             
    def getGPSName(self, exif, metadata ):
        coordinates = exif.gps(metadata)
        name = ''
        if len(coordinates):
            xml = self.gpsQuery( coordinates )
            if xml is not None:
                
                # if self.verbose:
                #     print("Address from GPS: {0}".format(xml[0].text) )
                for opt in self.gps_option:
                    if opt == 'full':
                        name = xml[0].text
                        break
                    elm = xml[1].find( opt )
                    if elm is not None:
                        print( "tag = {0}, text = {1}".format(elm.tag, elm.text))
                        name += ", {0}".format(elm.text)
                        
        return name[2:]

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
        path = '/{0}/{1}/{2}/'.format( data.make.capitalize(), data.model, data.date[0:4])
        path_to_events = data.target_path + path

        matches = glob.glob(path_to_events + data.date + '*')
        print( data.make, data.model )
        # Found potential matching events 
        answer = 'n'
        num_matches = len(matches)
        while( True ):
            if num_matches:
                if not self.ignore_all:
                    print( "Found events matching the date. Use one of these instead?" )

                    for i,m in enumerate(matches):
                        print( "- [{0}] add to: {1}"
                               .format(i, self.stripPath( path_to_events, m, 0 )))
                    answer = input("- [n] to create a new.\n"
                                   "- [i] to ignore this event.\n"
                                   "- Type one of the options above: ")
                else:
                    answer = 'i'
            if self.use_gps:
                name = self.getGPSName(exif, metadata )

                # Empty string means that it didn't have any valid gps info
                if len(name):
                    self.writepath[data.key] = '{0}{1} {2}/'.format( path, data.date, name )
                    break
            
            if answer.isdigit() and int(answer) < len(matches) :
                event = self.stripPath( path_to_events, matches[int(answer)], 0 )
                self.writepath[ data.key ] = '{0}{1}/'.format( path, event )
                break
            elif answer == "n":
                name = ''
                # Ask for input if date_only isn't set or if it founds some matches.
                if not self.date_only or num_matches:
                    # Ask for name 
                    name = input('[{0}] Name of event ( {1} <name> ): '
                                 .format(data.filetype, data.date))
                if len( name ):
                    # Add date + name
                    path += '{0} {1}/'.format(data.date, name)
                else:
                    path += '{0}/'.format(data.date)

                # Add path to dict
                self.writepath[ data.key ] = path
                break
            elif answer == 'i':
                self.ignore[ data.key ] = True
                break
            else:
                print( 'Unknown option, try again.' )
       
    

    def add_file( self, filename, exif, filetype, target_path ):
        # go to the correct folder e.g. ~/Nikon/D7000/2011/
        # Get the metadata from the image
        metadata = GExiv2.Metadata( filename )
        # Extract usfull information from the metadata object

        make = exif.make( metadata )
        model = exif.model( metadata )
        date = exif.date( metadata )
        # GExiv2 format the date with : instead of -.
        date=date.replace(":","-")
        # Create key to filename to acoid parsing metadata twice
        key =  "{0}{1}{2}".format( make, model, date )

        self.img_keys[ filename ] = key
        
        if (key not in self.writepath) and (key not in self.ignore):
            data = FileData( key, date, make, model, filetype, target_path )
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
    parser.add_argument("-d","--date-only", action="store_true", default=False, dest='date_only',
                        help="Date only, will just use the date as the destination directory. "
                        "Will only prompt for input if it finds a directory with the same date "
                        "in the destination dir.")
    parser.add_argument("-i","--ignore", action="store_true",default=False, dest='ignore_all',
                        help="Will ignore all files where a directory with the same date exist in the destination directory.")
    parser.add_argument("-c", default='~/.picmoverrc', dest='path',
                        help="Config file to load.")
    parser.add_argument("-g","--gps", dest="gps",nargs='*',
                        help="Use the gps location to name the destination dir. "
                        "See https://wiki.openstreetmap.org/wiki/Nominatim#Example "
                        "under addressparts for arguments for GPS.")
    result = parser.parse_args()
    pm = PicMover( result.path, 
                   result.gps,
                   verbose = result.verbose, 
                   dry_run = result.dry_run,
                   move = result.move,
                   date_only = result.date_only,
                   ignore_all = result.ignore_all )
    pm.exe()
    return 0
    
if __name__ == "__main__":
    sys.exit(main())

    
