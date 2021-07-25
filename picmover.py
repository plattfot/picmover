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
import gi
try:
    # for extracting metadata from jpeg and raw image files
    gi.require_version('GExiv2','0.10')
    from gi.repository import GExiv2
except ImportError:
    exit('You need to install gexiv2 first.')
try:
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify
    HAS_NOTIFY_SUPPORT=True
except ImportError:
    HAS_NOTIFY_SUPPORT=False
# For gps
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from collections import defaultdict

from sys import argv, stderr, exit
from collections import namedtuple

##############################################
FileData = namedtuple("FileData", "key, date, make, model, filetype, target_path")

__doc__ = """PicMover: Simple class that extracts metadata from an
image pool and moves them to a dir named with date and user comment.

To run simply execute PicMover.py where the pictures are.

Flags:
  -v, --verbose

Created by: Fredrik "PlaTFooT" Salomonsson
plattfot@gmail.com. """

def yesNo( x ):
    if x.lower() == 'yes' or x.lower() == 'true':
        return True
    else:
        return False
def getMetadata( metadata, key, default='Unknown' ):
    if key in metadata:
        return metadata[key]
    else:
        print("[Error] Exif data {0} doesn't exist in img! "
              "Returning \"{1}\".".format(key,default))
        return default
# TODO: Add that you can add custom mappings in the config file or
# similar file instead of editing this all the time. Something like
# Apple[0-9+-,]+ -> Apple
# Or maybe xml or something.

class FilterMake:
    def __init__(self):
        self.apple_re = re.compile("Apple[0-9+-.]+")
        self.nikon_re = re.compile("Nikon", re.IGNORECASE)
        self.lg_re = re.compile("LGE")
        self.asus = re.compile("asus")
    def __call__( self, make ):
        # For iphone 4, apple appends some sort of id after the make
        # so just remove that.
        if re.search(self.apple_re, make ):
            make = 'Apple'
        elif re.search(self.nikon_re, make):
            # Choose first ( remove corporation from nikon)
            make = 'Nikon'
        elif re.search(self.lg_re, make):
            make = 'LG'
        elif re.search(self.asus,make):
            make = 'Asus'
        return make

class FilterModel:
    def __init__(self):
        self.iphone_re = re.compile("iPhone ([0-9s]+)-[0-9+-.]+")
        self.nikon_re = re.compile("NIKON (D[0-9]+)", re.IGNORECASE)

    def __call__( self, model ):
        # For iphone 4, apple appends some sort of id after the model
        # so just remove that.
        match =  re.search(self.iphone_re, model )
        if match:
            return 'iPhone {0}'.format(match.group(1))

        match = re.search( self.nikon_re, model )
        if match:
            return match.group(1)
        return model
def extract_timestamp(filename):
    regex = re.compile( "_([0-9]{4})([0-9]{2})([0-9]{2})_" )
    match = re.search(regex,filename)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        if( (year >= 1990) and
            (month > 0 and month <= 12 ) and
            (day > 0 and day <= 31)):
            return "{:4d}:{:2d}:{:2d}".format(year,month,day)

    return ""
class ExifImg:
    """Extract metadata from images"""
    def __init__(self, default_make, default_model):
        self.default_make = default_make
        self.default_model = default_model
        self.filter_model = FilterModel()
        self.filter_make = FilterMake()

    def model( self, metadata ):
        return self.filter_model( getMetadata( metadata, 'Exif.Image.Model',
                                               self.default_model ) )
    def make( self, metadata ):
        return self.filter_make( getMetadata( metadata, 'Exif.Image.Make',
                                              self.default_make ) )
    def date( self, metadata, filename ):
        if 'Exif.Image.DateTimeOriginal' in metadata:
            date = metadata['Exif.Image.DateTimeOriginal'].split()[0]
        elif 'Exif.Photo.DateTimeOriginal' in metadata:
            date = metadata['Exif.Photo.DateTimeOriginal'].split()[0]
        else:
            print( "[Warning] Couldn't find date!" )
            print( "          Checking the filename for timestamp")
            date = extract_timestamp(filename)
            if( not date ):
                print( "          Found no valid timestamp,\n"
                       "          using today's date instead.")
                date = '{:%Y:%m:%d}'.format(datetime.datetime.today())
            else :
                print( "          Found valid timestamp, using that.")
        return date
    def gps(self, metadata ):
        if 'Exif.GPSInfo.GPSLatitude' in metadata and\
           'Exif.GPSInfo.GPSLongitude' in metadata:
            return [metadata.get_gps_latitude(), metadata.get_gps_longitude()]
        else:
            return []

class ExifMov:
    """Extract metadata from mov files"""
    def __init__(self, default_make, default_model):
        self.default_make = default_make
        self.default_model = default_model
        self.filter_model = FilterModel()
        self.filter_make = FilterMake()

        self.gps_re = re.compile("([+-][0-9]+\.[0-9]+)([+-][0-9]+\.[0-9]+)")

    def model( self, metadata ):
        return self.filter_model( getMetadata( metadata, 'Xmp.video.Model',
                                               self.default_model) )

    def make( self, metadata ):
        return self.filter_make( getMetadata( metadata, 'Xmp.video.Make',
                                              self.default_make ) )

    def date( self, metadata, filename ):
        if 'Xmp.video.DateTimeOriginal' in metadata:
            date = metadata['Xmp.video.DateTimeOriginal'].split()[0]
        elif 'Xmp.video.CreateDate' in metadata:
            date = metadata['Xmp.video.CreateDate'].split('T')[0]
        else:
            print( "[Warning] Couldn't find date!" )
            print( "          Checking the filename for timestamp")
            date = extract_timestamp(filename)
            if( not date ):
                print( "          Found no valid timestamp,\n"
                       "          using today's date instead.")
                date = '{:%Y:%m:%d}'.format(datetime.datetime.today())
            else :
                print( "          Found valid timestamp, using that.")
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

    def __init__(self, path, pool, gps_option, dry_run = False, move = False,
                 verbose = False, date_only = False, ignore_all = False, match=None,
                 camera_maker = "Unknown maker", camera_model="Unknown model"):
        # Convert ~/ to relative path if needed.
        expanded_path = os.path.expanduser( path )
        # Init variables
        image_path = "Image"
        video_path = "Video"
        root = os.path.expanduser( "~" )
        check_if_mounted = False
        self.camera_maker = camera_maker
        self.camera_model = camera_model

        is_camera_maker_unset = camera_maker == "Unknown maker"
        is_camera_model_unset = camera_model == "Unknown model"

        self.IMAGE_POOL_PATH = pool
        # Read settings
        f = open( expanded_path, "r")
        for line in f:
            data = line.split()
            # Check if data has no entries
            if len(data) == 0:
                continue
            if data[0] == "CameraMaker" and is_camera_maker_unset:
                self.camera_maker = data[1]
            elif data[0] == "CameraModel" and is_camera_model_unset:
                self.camera_model = data[1]
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
        if verbose:
            print( "Default camera maker is",self.camera_maker )
            print( "Default camera model is",self.camera_model )

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
        raw_ext = '(3fr|ari|arw|bay|crw|cr2|cap|dcs|dcr|'\
                  'dng|drf|eip|erf|fff|iiq|k25|kdc|mdc|mef|'\
                  'mos|mrw|nef|nrw|obm|orf|pef|ptx|pxn|r3d|'\
                  'raf|raw|rwl|rw2|rwz|sr2|srf|srw|x3f)'
        mov_ext = '(mov|mp4)'
        self.pattern_raw = re.compile('\.{0}$'.format(raw_ext), re.IGNORECASE)
        self.pattern_jpg = re.compile('\.jpe{0,1}g$', re.IGNORECASE)
        self.pattern_mov = re.compile('\.{0}$'.format(mov_ext), re.IGNORECASE)

        self.set_gps( gps_option )
        self.match = match

    # checks if a directory exists, if not it creates it
    def ensure_dir(self, f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            print( "Created path", f )

    def set_gps(self, gps_option ):
        if gps_option is not None:
            self.gps_option = gps_option
            self.use_gps = True
        else:
            self.use_gps = False

    # Returns an xml tree of the search
    def gps_query( self, coords ):
         html = urlopen("http://nominatim.openstreetmap.org/reverse?"
                        "format=xml&lat={0}&lon={1}".format( coords[0], coords[1]))
         return ET.fromstring( html.read() )

    def get_gps_name(self, exif, metadata ):
        coordinates = exif.gps(metadata)
        name = ''
        if len(coordinates):
            xml = self.gps_query( coordinates )
            if xml is not None:

                if self.verbose:
                    print("Address from GPS: {0}".format(xml[0].text) )
                if len(xml) == 1:
                    print("[Error] {0}".format(xml[0]))
                    return 'Unknown location'
                for opt in self.gps_option:
                    if opt == 'full':
                        name = xml[0].text
                        break
                    elm = xml[1].find( opt )
                    if elm is not None:
                        name += ", {0}".format(elm.text)

        return name[2:]

    # strips the path name and just return the name of the file
    # e.g path/to/file/pic.NEF -> pic.NEF
    def strip_path(self, path, filename, offset = 1):
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
            self.ensure_dir(writepath)

            if not os.path.exists(writepath):
                shutil.copy2(filepath,writepath)
                if self.verbose:
                    print( " -Moved to", writepath )
                if self.move: os.remove( filepath )
        else:
            if self.verbose:
                print( " -Moved to", writepath )

    def print_match(self, matches, idx ):
        print("Found events using match {0}: {1}".format(idx, matches[idx]))
    def add_path(self, metadata, exif, data ):
        path = '/{0}/{1}/{2}/'.format( data.make,
                                       data.model, data.date[0:4])
        path_to_events = data.target_path + path

        matches = glob.glob(path_to_events + data.date + '*')
        print( data.make, data.model )
        # Found potential matching events
        answer = 'n'
        num_matches = len(matches)
        while( True ):
            if num_matches:
                if not self.ignore_all:
                    if self.match is None:
                        print( "Found events matching the date. "
                               "Use one of these instead?" )
                        for i,m in enumerate(matches):
                            print( "- [{0}] add to: {1}"
                                   .format(i, self.strip_path( path_to_events, m, 0 )))
                        answer = input("- [n] to create a new.\n"
                                       "- [i] to ignore this event.\n"
                                       "- Type one of the options above: ")
                    elif self.match[0] < num_matches:
                        self.print_match( matches, self.match[0] )
                        answer = str(self.match[0])

                    else:
                        idx = num_matches-1
                        self.print_match( matches, idx )
                        answer = str(idx)
                else:
                    answer = 'i'
            if self.use_gps:
                name = self.get_gps_name(exif, metadata )

                # Empty string means that it didn't have any valid gps info
                if len(name):
                    self.writepath[data.key] = '{0}{1} {2}/'.format( path, data.date,
                                                                     name )
                    break

            if answer.isdigit() and int(answer) < len(matches) :
                event = self.strip_path( path_to_events, matches[int(answer)], 0 )
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
        metadata = GExiv2.Metadata( "{0}/{1}".format(self.IMAGE_POOL_PATH, filename) )
        # Extract usfull information from the metadata object

        make = exif.make( metadata )
        model = exif.model( metadata )
        date = exif.date( metadata, filename )

        # GExiv2 format the date with : instead of -.
        date=date.replace(":","-")
        misc = ""

        if self.use_gps:
          # If using the gps add the gps coordinates to the key to
          # avoid clumping pictures taken at different locations.
          gps = exif.gps( metadata )
          if gps:
            misc = "{0}{1}".format( gps[0], gps[1] )

        # Create key to filename to avoid parsing metadata twice
        key = "{0}{1}{2}{3}".format( make, model, date, misc )
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
        if HAS_NOTIFY_SUPPORT:
          Notify.init("picmover")
          notify = Notify.Notification.new("picmover","Copying files from {0}"
                                           .format(self.IMAGE_POOL_PATH))
          notify.show()

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
        exif_img = ExifImg( self.camera_maker, self.camera_model )
        exif_mov = ExifMov( self.camera_maker, self.camera_model )

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
        if HAS_NOTIFY_SUPPORT:
          notify = Notify.Notification.new("picmover","Done copying files from {0}"
                                           .format(self.IMAGE_POOL_PATH))
          notify.show()

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
    parser.add_argument("-p","--pool", default=os.getcwd(), dest='pool',
                        help="Source path it will look for files, "
                        "defaults to the directory it's called from.")
    parser.add_argument("-v", action="store_true", default=False, dest='verbose',
                        help="More text, i.e. verbose")
    parser.add_argument("-m","--mv", action="store_true", default=False, dest='move',
                        help="Moves the target images, "
                        "not just copying them to the target position")
    parser.add_argument("-n", action="store_true", default=False, dest='dry_run',
                        help="Dry run, execute all actions but doesn't move "
                        "any files. Good for testing.")
    parser.add_argument("-d","--date-only", action="store_true", default=False,
                        dest='date_only',
                        help="Date only, will just use the date as the "
                        "destination directory. Will only prompt for input if "
                        "it finds a directory with the same date in the "
                        "destination dir.")
    parser.add_argument("-i","--ignore", action="store_true",default=False,
                        dest='ignore_all',
                        help="Will ignore all files where a directory with the "
                        "same date exist in the destination directory.")
    parser.add_argument("-c","--config", default='~/.picmoverrc', dest='path',
                        help="Config file to load.")
    parser.add_argument("-g","--gps", dest="gps",nargs='*',
                        help="Use the gps location to name the destination dir. "
                        "See https://wiki.openstreetmap.org/wiki/Nominatim#Example "
                        "under addressparts for arguments for GPS.")
    parser.add_argument("--model", nargs=1, dest='model', type=str,
                        default='Unknown model',
                        help="Specify the model name to use if it "
                        "cannot be deduced from the metadata.")
    parser.add_argument("--maker", nargs=1, dest='maker', type=str,
                        default='Unknown maker',
                        help="Specify the maker name to use if it "
                        "cannot be deduced from the metadata.")
    parser.add_argument("--match", nargs=1, dest='match', type=int,
                        help="Pick match MATCH when finding matches at destination "
                        "instead of prompting user. If MATCH is greater than "
                        "number of matches it will pick the last one.")
    result = parser.parse_args()
    pm = PicMover( result.path,
                   result.pool,
                   result.gps,
                   verbose = result.verbose,
                   dry_run = result.dry_run,
                   move = result.move,
                   date_only = result.date_only,
                   ignore_all = result.ignore_all,
                   match=result.match,
                   camera_model=result.model[0],
                   camera_maker=result.maker[0] )
    pm.exe()
    return 0

if __name__ == "__main__":
    sys.exit(main())
