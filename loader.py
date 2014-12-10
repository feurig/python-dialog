#!/usr/bin/env python3

from dialog import Dialog

d = Dialog(dialog="dialog")
d.set_background_title("Select file to load.....")
code, selection = d.fselect('/mnt/images/',10,70)
if code == d.OK :
  d.set_background_title("loading:" +selection)
  d.pause("Something should happen here",15,70,15)

