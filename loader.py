#!/usr/bin/env python3
"""-------------------------------------------------------------------loader.py
Summary: This is a minimal dialog based image loader for tizen images. 
Author: Donald Delmar Davis ddavis3@jaguarlandrover.com

Assumptions:
Images are being moved to and from /dev/sda1
Images are stored on depot in /home/public/images
Images are 4M raw files.

----------------------------------------------------------------------------"""

from dialog import Dialog
from threading import Thread
import subprocess
import sys, os
import contextlib
import time
from enum import Enum

class Flags(Enum):
    NO_NETWORK=1
    NO_DEPOT=2
    NO_IMAGES=4
    NO_LOCAL=8
    
#flags=Enum('flags' ,'OK NO_DEPOT NO_NETWORK')

def read_stderr_realtime(proc, stream='stderr'):
    """ 
    do not let python buffer our status stream.
    See: http://blog.thelinuxkid.com/2013/06/get-python-subprocess-output-without.html
    """
    newlines = ['\n', '\r\n', '\r']
    stream = getattr(proc, stream)
    with contextlib.closing(stream):
        while True:
            out = []
            last = stream.read(1)
            # Don't loop forever
            if last == '' and proc.poll() is not None:
                break
            while last not in newlines:
                # Don't loop forever
                if last == '' and proc.poll() is not None:
                    break
                out.append(last)
                last = stream.read(1)
            out = ''.join(out)
            yield out


def check_environment(d):

    """
    do some rudimentry environment checks.
    """
    global flags
    retval=0x00   
    d.set_background_title("Checking your environment")

    try:
        subprocess.check_call(["ping", "8.8.8.8", "-c1", "-W5"])

    except subprocess.CalledProcessError:
        retval |= Flags.NO_NETWORK.value | Flags.NO_DEPOT.value | Flags.NO_IMAGES.value
    else:
     try:
        subprocess.check_call(["ping", "192.168.4.200", "-c1", "-W5"])

     except subprocess.CalledProcessError:
        retval |= Flags.NO_DEPOT.value | Flags.NO_IMAGES.value
      
     else:  
      subprocess.call(["umount","/mnt/images"])

      try:
          subprocess.check_call(["mount","depot:/home/public/images","/mnt/images"])
 
      except subprocess.CalledProcessError:   
          retval |= Flags.NO_IMAGES.value
 
    subprocess.call(["umount","/mnt/local"])

    try:
        subprocess.check_call(["mount","/dev/sdb2","/mnt/local"])
 
    except subprocess.CalledProcessError:   
        retval |= Flags.NO_LOCAL.value
       
    return retval

def main_menu(d,state):
    """
    front end menu
    """
    global flags
    list=[("exit","Quit")]
    if not state & Flags.NO_LOCAL.value:
        list.insert(0,("archive_local","Archive disk image to stick"))
        list.insert(0,("load_local","Load disk image from stick"))
    if not state & Flags.NO_DEPOT.value:
        list.insert(0,("archive","Archive disk image to Depot"))
        list.insert(0,("load","Load disk image from Depot"))
    
    if (state & Flags.NO_LOCAL.value) and (state & Flags.NO_DEPOT.value) :
      d.set_background_title("OSTC Image Loader -- NO MEDIA AVALIABLE")
    else:
      d.set_background_title("OSTC Image Loader")
   
    code, tag = d.menu("Select Action Below",
                       choices=list
                      )
    return tag
    


def select_file_for_read(d,directory):
  """
  do a little checking before accepting selection
  """
  
  while True:
      code, selection = d.fselect(directory,10,70)
      if code==d.OK:
        if os.path.isfile(selection) and os.access(selection,os.R_OK):
      	    return code, selection
        else:
            d.msgbox("Invalid Selection: Can't open image file")
      else:
            return code, selection
            


def load_image(d,directory):
  """
  load a raw image onto the disk. Reboot if successful
  """

  d.set_background_title("Select file to load.....")

  code, selection = select_file_for_read(d,directory)

  if code == d.OK :
    
    disk_loaded=False
       
    cmd = ['pv', '-n', selection ]
    try:
        output=open('/dev/sda','w')
    except:
        d.set_background_title("Fatal: Can not open target disk")
        d.msgbox("Please check your system") 
        sys.exit(1)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=output,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        d.set_background_title("loading:" +selection)
        d.gauge_start("Progress",10,70,0)
   
        for line in read_stderr_realtime(proc):
            if line.strip() == '':
                continue
            if "No such file" in line.strip():
                break
            d.gauge_update(int(line.strip()))  
            if int(line.strip()) == 100:
                d.gauge_update(100, "Finished!")
                disk_loaded=True       
                break

    except IOError:
        d.set_background_title("Fatal: Could Not Complete Task")
        d.msgbox("Sorry") 
        sys.exit(1)

    code = d.gauge_stop() 

    if disk_loaded:
        d.set_background_title("Success: Disk has been reimaged!")
        code = d.pause("Rebooting in 5 seconds, Remove media once reboot begins", 10,70, 5)
        if code==d.OK:
            subprocess.check_call(["reboot"])
        else:         
            d.set_background_title("Reboot Cancelled")
            d.msgbox("Have A Nice Day") 
            sys.exit(2)
  else:
     d.set_background_title("Cancelled")
     d.msgbox("Have A Nice Day") 
     sys.exit(2)



def select_file_for_write(d,directory):
  """ 
  Do some checks before we write our file.
  TODO: add warning if overwriting a file
  """

  while True:
      code, selection = d.fselect(directory,10,70)
      if code==d.OK:
        if os.path.isfile(selection) and os.access(selection, os.W_OK):
            itsok = d.yesno("File Exists!!! Overwrite it?")
            if itsok==d.OK :
                return code, selection
        if ( not os.path.isdir(selection) ) and os.access(os.path.dirname(selection),os.W_OK):
      	    return code, selection
        else:
            d.msgbox("Invalid Selection: Can't write image file: "+selection)
      else:
            return code, selection
            



def archive_image(d,directory):
  """
  save image of disk to archive directory.
  """
  
  d.set_background_title("Select archive filename.....")

  code, selection = select_file_for_write(d,directory)

  if code == d.OK :
    sourcepath='/dev/sda'
    disk_archived=False
    cmd = [ 'dd if='+sourcepath+' bs=16M count=256 status=none | pv -n -s 4g' ]
    try:
        output=open(selection,'w')
    except:
        d.set_background_title("Fatal: Can not open archive file")
        d.msgbox("Sorry") 
        sys.exit(1)
    try:
       d.set_background_title("Archiving to:" +selection)
       d.gauge_start("Progress",10,70,0)
   
       proc = subprocess.Popen(
            cmd,
            stdout=output,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True 
       )
   
       for line in read_stderr_realtime(proc):
            if line.strip() == '':
                continue
            if "No such file" in line.strip():
                break
            d.gauge_update(int(line.strip()))  
            if int(line.strip()) == 100:
                d.gauge_update(100, "Finished!")
                disk_archived=True       
                break
 
    except:
        d.set_background_title("Fatal: Could Not Complete Task")
        d.msgbox("Sorry") 
        sys.exit(1)

    code = d.gauge_stop() 

    if disk_archived:
        d.set_background_title("Success: Disk has been archived!")
        code = d.pause("Returning to loader in 5 seconds", 10,70, 5)
        if code==d.OK:
            return
  else:
     d.set_background_title("Cancelled")
     d.msgbox("Have A Nice Day") 
     sys.exit(2)


"""------------------------------------------------------------------------main

TODO: should go from archive to load

----------------------------------------------------------------------------"""

d = Dialog(dialog="dialog")
flags=check_environment(d)
while True:
 choice=main_menu(d,flags)

 if choice=="load":
     load_image(d,'/mnt/images/')
     continue
 if choice=="archive":
     archive_image(d,'/mnt/images/archive/')
     continue
 if choice=="load_local":
     load_image(d,'/mnt/local/')
     continue
 if choice=="archive_local":
     archive_image(d,'/mnt/local/')
 else:
     d.set_background_title("OK....")
     d.msgbox("Have A Nice Day") 
     sys.exit(2)

     
  