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
    
    d.set_background_title("Checking your environment")

    try:
        subprocess.check_call(["ping", "8.8.8.8", "-c1", "-W5"])

    except subprocess.CalledProcessError:
        d.set_background_title("Fatal: Not Connected To Network")
        d.msgbox("Please check your network connection and restart") 
        sys.exit(1)

    try:
        subprocess.check_call(["ping", "192.168.4.200", "-c1", "-W5"])

    except subprocess.CalledProcessError:
        d.set_background_title("Fatal: Can not find depot")
        d.msgbox("Please check your network connection and restart") 
        sys.exit(1)
        
    subprocess.call(["umount","/mnt/images"])

    try:
        subprocess.check_call(["mount","depot:/home/public/images","/mnt/images"])
 
    except subprocess.CalledProcessError:   
        d.set_background_title("Fatal: Can not mount images directory")
        d.msgbox("Please contact your system administrator") 
        sys.exit(1)



def main_menu(d):
    """
    fron end menu
    """
    
    d.set_background_title("OSTC Image Loader")
    code, tag = d.menu("Select Action Below",
                       choices=[("load","Load new disk image from depot"),
                                ("archive","Archive disk image to depot"),
                                ("exit","Quit")]
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
            


def load_image(d):
  """
  load a raw image onto the disk. Reboot if successful
  """

  d.set_background_title("Select file to load.....")

  code, selection = select_file_for_read(d,'/mnt/images/')

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
        code = d.pause("Please remove boot media, rebooting in 5 seconds", 10,70, 5)
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
        if ( not os.path.isdir(selection) ) and os.access(os.path.dirname(selection),os.W_OK):
      	    return code, selection
        else:
            d.msgbox("Invalid Selection: Can't write image file: "+selection)
      else:
            return code, selection
            



def archive_image(d):
  """
  save image of disk to archive directory.
  """
  
  d.set_background_title("Select archive filename.....")

  code, selection = select_file_for_write(d,'/mnt/images/archive/')

  if code == d.OK :
    
    disk_archived=False
    cmd=['dd','if=/dev/sda','bs=16M','count=256','status=none|pv','-n','-s','4g']
    #cmd = ['pv', '-n', '/dev/sda' ]
    try:
        output=open(selection,'w')
    except:
        d.set_background_title("Fatal: Can not open archive file")
        d.msgbox("Please check your system") 
        sys.exit(1)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=output,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True
        )

        d.set_background_title("Archiving to:" +selection)
        d.gauge_start("Progress",10,70,0)
   
        for line in read_stderr_realtime(proc):
            if line.strip() == '':
                continue
            if "No such file" in line.strip():
                #break
                continue
            d.gauge_update(int(line.strip()))  
            if int(line.strip()) == 100:
                d.gauge_update(100, "Finished!")
                disk_archived=True       
                break

    except IOError:
        d.set_background_title("Fatal: Could Not Complete Task")
        d.msgbox("Sorry") 
        sys.exit(1)

    code = d.gauge_stop() 

    if disk_archived:
        d.set_background_title("Success: Disk has been reimaged!")
        code = d.pause("Please remove boot media, rebooting in 5 seconds", 10,70, 5)
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


"""------------------------------------------------------------------------main

TODO: should go from archive to load

----------------------------------------------------------------------------"""

d = Dialog(dialog="dialog")
check_environment(d)
while True:
  choice=main_menu(d)

  if choice=="load":
     load_image(d)
  if choice=="archive":
     archive_image(d)
  else:
     d.set_background_title("OK....")
     d.msgbox("Have A Nice Day") 
     sys.exit(2)

     
  