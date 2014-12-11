#!/usr/bin/env python3

from dialog import Dialog
from threading import Thread
import subprocess
import sys, os
import contextlib

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
  d.set_background_title("loading:" +selection)
  d.pause("Something should happen here",15,70,15)

