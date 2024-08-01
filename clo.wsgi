import sys, os
# ROOT_FOLDER = os.path.abspath(os.curdir)
# ROOT_FOLDER = "/home/user/DASH_APPS/flowboard"

#activate_this = os.path.join(ROOT_FOLDER, 'env/bin/activate_this.py')
#with open(activate_this) as file_:
#   exec(file_.read(), dict(__file__=activate_this))

# exec(open(activate_this).read(), {'__file__': activate_this})

#sys.path.append(ROOT_FOLDER)

setupBaseDir = os.path.dirname(__file__)
sys.path.insert(0, setupBaseDir)

from app import server as application