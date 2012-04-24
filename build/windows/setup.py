from distutils.core import setup
import py2exe

import sys, os
relative_dirs = ['../../src',
                 '../../src/gui',
                 '../../src/library/ext/cp4pc']
dirs = [os.path.abspath(dir) for dir in relative_dirs]
main_file = os.path.join(dirs[1], 'xig_app.py')

python_modules = []
for dir in dirs:
    sys.path.append(dir)
    for filename in os.listdir(dir):
        try:
            if filename[-3:] == ".py":
                python_modules.append(filename[:-3])
        except:
            pass

setup(console=[main_file], 
      options={
               "py2exe": {
                         "includes": python_modules,
                         "packages": ["handlers", "rci", "library", "sessions", "sessions.library"]
                         }
               }
      )
print "done."