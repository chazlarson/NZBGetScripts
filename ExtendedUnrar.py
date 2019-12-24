#!/usr/bin/env python
#
# ExtendedUnrar post-processing script for NZBGet
#
# Copyright (C) 2014 thorli <thor78@gmx.at>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Version 1.0 (2014-06-01)
# Version 2.0 (2019-04-20) Fixes/improvements/cleanup by Bun
# Version 2.0.1 (2019-12-24) Minor tweak, stored in github
#

##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# Unrar nested rar files
#
# This script extracts nested rar archives from downloaded files.
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                                ###

# Full Path to Unrar executable (optional, default: unrar)
#
# (if blank, NZBGet "UnrarCmd" setting is used)
#UnrarPath=unrar

# File extension of rar files to search for (default: *.[rR]??)
#
# It is possible to use "*" and "?" for wildcards and "[]" for character ranges.
# NOTE: Only one entry for the extension mask is supported.
#RarExtensions=*.[rR]??

# Time (in seconds) to pause start of script (default: 0)
#
# (Gives NZBGet time to perform "UnpackCleanupDisk" action on slow systems)
#WaitTime=0

# Delete leftover extended rar files after successful extract (yes, no).
#
#DeleteLeftover=yes

### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################


import glob
import os
import sys
import subprocess
import time

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS=93
POSTPROCESS_ERROR=94
POSTPROCESS_NONE=95

# Check if the script is called from nzbget 18.0 or later
if not 'NZBOP_EXTENSIONS' in os.environ:
    print('[ERROR] This script requires NZBGet v18.0 or later')
    sys.exit(POSTPROCESS_ERROR)

print('[INFO] Script successfully started - python %s' % sys.version_info)
sys.stdout.flush()

# Check nzbget.conf options
required_options = ('NZBOP_UNRARCMD', 'NZBPO_UNRARPATH', 'NZBPO_RAREXTENSIONS', 'NZBPO_WAITTIME', 'NZBPO_DELETELEFTOVER')
for optname in required_options:
    if (not optname in os.environ):
        print('[ERROR] Option %s is missing in NZBGet configuration. Please check script settings' % optname[6:])
        sys.exit(POSTPROCESS_ERROR)

# If NZBGet Unpack setting isn't enabled, this script cannot work properly
if os.environ['NZBOP_UNPACK'] != 'yes':
    print('[ERROR] You must enable option "Unpack" in NZBGet configuration, exiting')
    sys.exit(POSTPROCESS_ERROR)

unrarpath=os.environ['NZBPO_UNRARPATH']
rarext=os.environ['NZBPO_RAREXTENSIONS']
waittime=os.environ['NZBPO_WAITTIME']
deleteleftover=os.environ['NZBPO_DELETELEFTOVER']

if unrarpath == '':
   print('[DETAIL] UnrarPath setting is blank. Using default NZBGet UnrarCmd setting')
   unrarpath=os.environ['NZBOP_UNRARCMD']

# Check TOTALSTATUS
if os.environ['NZBPP_TOTALSTATUS'] != 'SUCCESS':
    print('[WARNING] NZBGet download TOTALSTATUS is not SUCCESS, exiting')
    sys.exit(POSTPROCESS_NONE)

# Check if destination directory exists (important for reprocessing of history items)
if not os.path.isdir(os.environ['NZBPP_DIRECTORY']):
    print('[WARNING] Destination directory ' + os.environ['NZBPP_DIRECTORY'] + ' does not exist, exiting')
    sys.exit(POSTPROCESS_NONE)

# Sleep (maybe)
if os.environ['NZBOP_UNPACKCLEANUPDISK'] == 'yes':
    print('[DETAIL] Sleeping ' + waittime + ' seconds to give NZBGet time to finish UnpackCleanupDisk action')
    time.sleep(int(float(waittime)))

# Traverse download files to check for un-extracted rar files
print('[DETAIL] Searching for rar/RAR files')

sys.stdout.flush()

status = 0
extract = 0
rarlist = []

for dirpath, dirnames, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
    # Find all possible extensions for rar files
    rarlist.extend(sorted(glob.glob(os.path.join(dirpath,rarext))))
    for file in filenames:
        filePath = os.path.join(dirpath, file)
        fileName, fileExtension = os.path.splitext(file)
        if fileExtension in ['.rar', '.RAR']:
            print('[INFO] Extracting %s' % file)
            sys.stdout.flush()
            # You can adjust the unrar options here if you need.  The defaults are:
            # e (extract without paths), -idp (no extract progress), -ai (ignore attributes), -o- (don't overwrite)
            unrar = '"' + unrarpath + '" e -idp -ai -o- "' + filePath + '" "' + os.environ['NZBPP_DIRECTORY'] + '"'
            try:
                retcode = subprocess.call(unrar, shell=True)
                if retcode == 0:
                    print('[INFO] Extract Successful')
                    extract = 1
                else:
                    print('[ERROR] Extract failed, Returncode %d' % retcode)
                    status = 1;
            except OSError as e:
                print('[ERROR] Execution of unrar command failed: %s' % e)
                print('[ERROR] Unable to extract %s' % file)
                status = 1

sys.stdout.flush()

if extract == 1 and deleteleftover == 'yes':
    print('[INFO] Deleting leftover rar files')
    for file in rarlist:
        print('[INFO] Deleting %s' % file)
        try:
            os.remove(file)
        except OSError as e:
            print('[ERROR] Delete failed: %s' % e)
            print('[ERROR] Unable to delete %s' % file)
            status = 1

if status == 0:
    sys.exit(POSTPROCESS_SUCCESS)
else:
    sys.exit(POSTPROCESS_NONE)
