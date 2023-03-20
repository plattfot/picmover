#! /bin/bash

# SPDX-FileCopyrightText: 2023 Fredrik Salomonsson <plattfot@posteo.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

#dependecies (pyexiv2, hachoir-metadata)
echo "Installing picMover"
sudo cp picmover.py /usr/bin/picmover
sudo chmod a+x /usr/bin/picmover
echo "done!"

