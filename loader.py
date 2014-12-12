#!/usr/bin/env python3

from dialog import Dialog
from threading import Thread
import subprocess
import sys, os
import contextlib
import time


#http://blog.thelinuxkid.com/2013/06/get-python-subprocess-output-without.html
def read_stderr_realtime(proc, stream='stderr'):
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
        
    try:
        subprocess.check_call(["mount","depot:/home/public/images","/mnt/images"])
 
    except subprocess.CalledProcessError:   
        d.set_background_title("Fatal: Can not mount images directory")
        d.msgbox("Please contact your system administrator") 
        sys.exit(1)
    
d = Dialog(dialog="dialog")

check_environment(d)

d.set_background_title("Select file to load.....")

code, selection = d.fselect('/mnt/images/',10,70)

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
 

