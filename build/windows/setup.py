from distutils.core import setup
import py2exe

import os

import xbee
cp4pc_dir = os.path.dirname(xbee.__file__)

import xig
xig_src_dir = os.path.dirname(xig.__file__)

python_modules = []
dirs = [xig_src_dir, os.path.join(xig_src_dir, "gui"), cp4pc_dir]
for dir in dirs:
    for filename in os.listdir(dir):
        try:
            if filename[-3:] == ".py":
                python_modules.append(filename[:-3])
        except:
            pass
    
setup(console=[os.path.join(xig_src_dir, "gui", 'xig_app.py')], 
      options={
               "py2exe": {
                         "includes": python_modules,
                         "packages": ["handlers", "rci", "library", "sessions", "sessions.library"]
                         }
               }
      )
print "done."