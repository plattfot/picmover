# Picmover

Moving pictures and videos from one location to another, using
metadata to determine camera maker, model, date and location. Useful
for importing files from a camera.

Why yet another file importer? The ones I tried didn't suit my needs
and I needed a small project to better familiarise myself with
python.

## Table of content
- [Installation](#installation)
  - [From source](#from-source)
  - [Arch Linux](#arch-linux)
- [Features](#features)
- [Usage](#usage)
  - [GPS](#gps)
  - [Config file](#config-file)
- [Limitations](#limitations)
  - [Tested cameras](#tested-cameras)
  - [OS support](#os-support)
## Installation
### From source
It's a simple python script so you don't need to compile anything. Just run
```bash
make install DESTDIR=<location>
```

where <location> is where you want to install it. The default is /usr.
Before you run the script make sure you have python-libgexiv2,
python-gobject and python-gobject2 version 0.10 installed.

### Arch Linux
Clone my aur repo and then build the package using the PKBUILD:
```bash
$ git clone git@bitbucket.org:plattfot/aur.git
$ cd aur/picmover
$ makepkg -ic
```
## Features
- Using exiv2 to extract metadata which is use to determine the
  destination of the files.
- GPS support, using
  [openstreetmap](https://wiki.openstreetmap.org/wiki/Nominatim#Example)
  to query the location name.

## Usage

To use picmover you change directory to where the images are that you
want to import, then you just execute picmover. It will then start to
parse the files and query you to add a description to each unique
camera and date it finds. If it already exist a directory with
matching date at the destiantion you have to option of:
- Using that destination.
- Create a new directory with another description
- Or ignore all files picmover finds with that date.

By default picmover will copy the images to the "~/Image" and the
video files to "~/Video". This can be changed in the config file, see
the [config file](#config-file) section for more info about that.

The structure for images are "<root>/<image root>/<Camera
maker>/<model>/<year>/<date> <description>/<ext>" Where ext for jpg is
"JPEG", for nef, or other raw formats is "raw". This is similar for
video.

### GPS

To use the gps data as a description use the command line argument
"-g" or "--gps", note that picmover will only query you if it finds a
conflict.

The options for gps are what it should pick as the description from
the xml file that openstreetmap returns. For example to have it print
out the road, city, country and land mark (if exist):
```bash
picmover --gps pedestrian road city country
```

See
[openstreetmap](https://wiki.openstreetmap.org/wiki/Nominatim#Example)
on what more keywords you can use.

### Config files

Picmover will look for a configure file called *.picmoverrc* in the
home directory, to specify another config file use *-c/--config PATH*.
Lines starting with # will be ignored.
The syntax is KEYWORD VALUE.
Here are all the keywords that the config file supports:

####CameraMaker
The default camera manufacturer which it will use if it cannot find it
in the metadata. The default is set to *Unknown maker* .

####CameraModel
The default camera model which it will use if it cannot find it in the
metadata. The default is set to *Unknown model*.

####Root
Path to where the root of the destination is. Default is $HOME.

####ImagePath
Path to where it should place the images relative to *Root*. The default is *Image*.

####VideoPath
Path to where it should place the videos relative to *Root*. The default is *Video*

####SourcePath
If this is set it will look for images and videos in this path instead
of looking at the directory it was called from.

####CheckIfMounted
Check if the *Root* is mounted before proceeding. Useful if the root
on a external/network attached drive. Will abort if the root isn't
mounted.

## Limitiations
### Tested cameras
- Nikon D750, D7000
- Nokia 6700
- Apple iPhone 4
### OS support
It's only tested on arch linux.

