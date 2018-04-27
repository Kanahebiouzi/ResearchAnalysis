#Modules
import sys, os, shutil, weakref, logging
import numpy

#SetProjectPath
__projectpath=os.getcwd()
sys.path.append(__projectpath)

#BaseClasses
#Object
class BaseObject(object):
    __dic={}
    @classmethod
    def _Append(cls,file,data):

#Command Extention
def mkdir(dirname):
    try:
        os.makedirs(dirname)
    except Exception:
        pass

def copy(name,name_to):
    try:
        if os.path.isdir(name):
            mkdir(name_to)
            lis=os.listdir(name)
            for item in lis:
                copy(name+'/'+item,name_to+'/'+item)
        else:
            if not os.path.exists(name_to):
                shutil.copy(name,name_to)
            else:
                sys.stderr.write('Error: Cannot copy. This file exists.\n')
    except Exception:
        sys.stderr.write('Error: Cannot remove.\n')
def move(name,name_to):
    if os.path.abspath(name_to).find(os.path.abspath(name))>-1:
        sys.stderr.write('Error: Cannot move. The file cannot be moved to this folder.\n')
        return 0
    try:
        if os.path.isdir(name):
            mkdir(name_to)
            lis=os.listdir(name)
            for item in lis:
                move(name+'/'+item,name_to+'/'+item)
            remove(name)
        else:
            if not os.path.exists(name_to):
                shutil.move(name,name_to)
                ExtendObject.OnMoveFile(name,name_to)
            else:
                sys.stderr.write('Error: Cannot move. This file exists.\n')
    except Exception:
        sys.stderr.write('Error: Cannot move.\n')
def remove(name):
    try:
        if os.path.isdir(name):
            lis=os.listdir(name)
            for item in lis:
                remove(name+'/'+item)
            os.rmdir(name)
        else:
            os.remove(name)
    except Exception:
        sys.stderr.write('Error: Cannot remove.\n')