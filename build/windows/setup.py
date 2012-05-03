from distutils.core import setup
import py2exe

print "Creating Windows Binary"

print "Removing existing files"

import sys, os, shutil
this_folder = os.path.dirname(__file__)
dist_folder = os.path.join(this_folder, 'dist')
# remove dist folder and everything in it
if os.path.exists(dist_folder):
    shutil.rmtree(dist_folder, True)
# add dist folder back in
if not os.path.exists(dist_folder):
    os.mkdir(dist_folder)

print "Creating Binary"

relative_dirs = ['../../src',
                 '../../src/gui',
                 '../../src/library/ext',
                 '../../src/library/ext/serial',
                 '../../src/library/ext/cp4pc']
dirs = [os.path.abspath(dir) for dir in relative_dirs]
main_file = os.path.join(dirs[1], 'xig_app.py')

python_modules = []
for dir in dirs:
    sys.path.insert(0, dir)
    for filename in os.listdir(dir):
        try:
            if filename[-3:] == ".py":
                python_modules.append(filename[:-3])
        except:
            pass

setup(console=[
               {
                "script": main_file,
                "icon_resources": [(1, 'xig.ico')]
                }
               ],
      options={
               "py2exe": {
                         "includes": python_modules,
                         "packages": ["handlers", "rci", "library", "sessions", "sessions.library"]
                         }
               }
      )

print "Copying non-Python file to directory"
src_root = os.path.join(this_folder, '..', '..', 'src', 'gui')
for dir in ('static', 'templates'):
    shutil.copytree(os.path.join(src_root, dir), os.path.join(dist_folder, dir))
shutil.copy2(os.path.join(this_folder, 'xig.ico'), os.path.join(dist_folder, 'xig.ico'))
shutil.copy2(os.path.join('..', '..', 'src', 'library', 'ext', 'cp4pc', 'rci', 'idigi-ca-cert-public.crt'),
             os.path.join(dist_folder, 'idigi-ca-cert-public.crt'))

print "Copy dist folder and zip up"
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
import xig
xig_version = xig.VERSION.replace('.', '_')
filename = 'xig_'+xig_version
xig_folder = os.path.join(this_folder, filename)
if os.path.exists(xig_folder):
    shutil.rmtree(xig_folder, True)
shutil.copytree(dist_folder, xig_folder)
print "Created folder %s" % xig_folder

zip_filename = os.path.join(this_folder, filename+'.zip')
if os.path.exists(zip_filename):
    os.remove(zip_filename)
with closing(ZipFile(zip_filename, "w", ZIP_DEFLATED)) as z:
    z.write(xig_folder, os.path.relpath(xig_folder, this_folder))
    for root, dirs, files in os.walk(xig_folder):
        #NOTE: ignore empty directories
        for fn in files:
            absfn = os.path.join(root, fn)
            z.write(absfn, os.path.relpath(absfn, this_folder))

print "Created zip file: %s" % zip_filename

print "A little cleanup"
json_file = os.path.join(this_folder, 'settings.json')
if os.path.exists(json_file):
    os.remove(json_file)

print "done."
