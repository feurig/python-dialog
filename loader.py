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

d = Dialog(dialog="dialog")
d.set_background_title("Select file to load.....")
code, selection = d.fselect('/mnt/images/',10,70)
if code == d.OK :
   
    cmd = ['pv', '-n', selection ]
    try:
        output=open('/dev/sda','w')
    except:
        print("Can't open target disk" )
        pass
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
                break
    except IOError:
        print ('oops')
        
    exit_code = d.gauge_stop() 


