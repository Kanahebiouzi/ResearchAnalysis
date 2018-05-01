#Modules
import sys, os, shutil, weakref, logging
import numpy as np

#SetProjectPath
__projectpath=os.getcwd()
sys.path.append(__projectpath)
__CDChangeListener=[]
import scipy.ndimage
import scipy.signal
#BaseClasses
#Object
class BaseObject(object):
    #static objects
    __dic={}
    @classmethod#TODO
    def OnMoveFile(cls,file,file_to):
        if cls.IsUsed(os.path.abspath(file)):
            cls.__dic[os.path.abspath(file)]()._Connect(os.path.abspath(file_to))
            cls._Remove(file)
    @classmethod
    def _Append(cls,file,data):
        cls.__dic[os.path.abspath(file)]=weakref.ref(data)
    @classmethod
    def _GetData(cls,file):
        try:
            abs=os.path.abspath(file)
        except Exception:
            return None
        if not abs in cls.__dic:
            return None
        res=cls.__dic[abs]()
        if res is None:
            del cls.__dic[abs]
        return res
    
    def __init__(self,file):
        self.__file=file
        self.__init(file)
        if file is not None:
            BaseObject._Append(file,self)
        self.__listener=[]
    def addDataChangedListener(self,listener):
        self.__listener.append(weakref.WeakMethod(listener))
    def removeDataChangedListener(self,listener):
        for l in self.__listener:
            if l()==listener:
                self.__listener.remove(l)
    def _emitDataChanged(self):
        for l in self.__listener:
            if l() is None:
                self.__listener.remove(l)
            else:
                l()()
    def Save(self,file):
        obj=BaseObject._GetData(file)
        if obj is None:
            BaseObject._Append(file,self)
            self._save(file)
            self._emitDataChanged()
            return self
        elif obj==self:
            self._save(file)
            self._emitDataChanged()
            return self
        else:
            obj.__overwrite(file,self)
            obj._emitDataChanged()
            return obj
    def __overwrite(self,file,target):
        for key in self._vallist():
            self.__setattr__(key,target.__getattribute__(key))
        self._save(file)
    def __init(self,file):
        if file is None:
            self._init()
        else:
            if not os.path.exists(os.path.abspath(file)):
                self._init()
            else:
                self._load(file)

    def _init(self):
        for l in self._vallist():
            self.__setattr__(l,None)
    def _load(self,file):
        with open(file,'r') as f:
            self.data=eval(f.read())
    def _save(self,file):
        with open(file,'w') as f:
            f.write(str(self.data))
    def _vallist(self):
        return ['data']
#
class AutoSaved(object):
    def _newobj(self,file):
        return BaseObject(file)

    def __init__(self,file=None):
        self.obj=None
        self.__file=file
        self.__loadFile=None
        self.__modListener=[]
        res=BaseObject._GetData(file)
        if res is None:
            self.obj=self._newobj(file)
            self.Save()
        else:
            self.obj=res
        self.obj.addDataChangedListener(self._EmitModified)

    def __setattr__(self,key,value):
        if not key=='obj':
            if self.obj is not None:
                if key in self.obj._vallist():
                    res=self.obj.__setattr__(key,value)
                    self.Save()
                    return res
        super().__setattr__(key,value)
    def __getattribute__(self,key):
        if key=='obj':
            return super().__getattribute__(key)
        if self.obj is not None:
            if key in self.obj._vallist():
                return self.obj.__getattribute__(key)
        return super().__getattribute__(key)

    def Save(self,file=None):
        if file is not None:
            newfile=os.path.abspath(file)
            if not self.__file==newfile:
                if self.__file is not None:
                    self.Disconnect()
                self.__file=newfile
        if self.__file is not None:
            tmp=self.obj.Save(self.__file)
            if not tmp==self.obj:
                self.obj.removeDataChangedListener(self._EmitModified)
                tmp.addDataChangedListener(self._EmitModified)
                self.obj=tmp
                self._EmitModified()
            return True
        else:
            self._EmitModified()
            return False
    def Disconnect(self):
        newobj=self._newobj(None)
        for key in newobj._vallist():
            newobj.__setattr__(key,self.obj.__getattribute__(key))
        self.obj.removeDataChangedListener(self._EmitModified)
        newobj.addDataChangedListener(self._EmitModified)
        self.obj=newobj
        self._EmitModified()
        self.__file=None

    def setLoadFile(self,file):
        self.__loadFile=os.path.abspath(file)
    def FileName(self):
        if self.__file is not None:
            return self.__file
        return self.__loadFile
    def Name(self):
        if self.FileName() is None:
            return "untitled"
        else:
            nam,ext=os.path.splitext(os.path.basename(self.FileName()))
            return nam
    def IsConnected(self):
        return self.__file is not None

    def addModifiedListener(self,method):
        self.__modListener.append(weakref.WeakMethod(method))
    def _EmitModified(self):
        for m in self.__modListener:
            if m() is None:
                self.__modListener.remove(m)
            else:
                m()(self)
class Wave(AutoSaved):
    class _wavedata(BaseObject):
        def _init(self):
            self.data=[]
            self.x=None
            self.y=None
            self.z=None
            self.note=None
        def _load(self,file):
            tmp=np.load(file)
            self.data=tmp['data']
            self.x=tmp['x']
            self.y=tmp['y']
            self.z=tmp['z']
            self.note=tmp['note']
        def _save(self,file):
            np.savez(file, data=self.data, x=self.x, y=self.y, z=self.z,note=self.note)
        def _vallist(self):
            return ['data','x','y','z','note']
        def __setattr__(self,key,value):
            if key in ['data','x','y','z']:
                super().__setattr__(key,np.array(value))
            else:
                super().__setattr__(key,value)
    def _newobj(self,file):
        return self._wavedata(file)
    def __getattribute__(self,key):
        if key=='x' or key=='y' or key=='z':
            val=super().__getattribute__(key)
            index=['x','y','z'].index(key)
            dim=self.data.ndim-index-1
            if self.data.ndim<=index:
                return None
            elif val.ndim==0:
                if self.data.ndim>index:
                    return np.arange(self.data.shape[dim])
                else:
                    return val
            else:
                if self.data.shape[dim]==val.shape[0]:
                    return val
                else:
                    res=np.empty((self.data.shape[dim]))
                    for i in range(self.data.shape[dim]):
                        res[i]=np.NaN
                    for i in range(min(self.data.shape[dim],val.shape[0])):
                        res[i]=val[i]
                    return res
        else:
            return super().__getattribute__(key)

    def slice(self,pos1,pos2,axis='x'):
        index=['x','y'].index(axis)
        size=pos2[index]-pos1[index]
        x,y=np.linspace(pos1[0], pos2[0], size), np.linspace(pos1[1], pos2[1], size)
        res=scipy.ndimage.map_coordinates(self.data, np.vstack((x,y)))
        w=Wave()
        w.data=res
        w.x=self.x[pos1[index]:pos2[index]]
        return w
    def getSlicedImage(self,zindex):
        return self.data[:,:,zindex]

    def var(self,*args):
        if len(args)==0:
            return self.data.var()
    def smooth(self,cutoff):#cutoff is from 0 to 1 (relative to nikist frequency)
        b, a = scipy.signal.butter(1,cutoff)
        w=Wave()
        w.data=self.data
        for i in range(0,self.data.ndim):
            w.data=scipy.signal.filtfilt(b,a,w.data,axis=i)
        return w
    def differentiate(self):
        w=Wave()
        w.data=self.data
        w.x=self.x
        w.y=self.y
        for i in range(0,w.data.ndim):
            w.data=np.gradient(self.data)[i]
        return w

    def average(self,*args):
        dim=len(args)
        if len(args)==0:
            return self.data.mean()
        if not dim==self.data.ndim:
            return 0
        if dim==1:
            return self.__average1D(args[0])
        if dim==2:
            return self.__average2D(args[0],args[1])
    def posToPoint(self,pos):
        x0=self.x[0]
        x1=self.x[len(self.x)-1]
        y0=self.y[0]
        y1=self.y[len(self.y)-1]
        dx=(x1-x0)/(self.data.shape[1]-1)
        dy=(y1-y0)/(self.data.shape[0]-1)
        return (int(round((pos[0]-x0)/dx)),int(round((pos[1]-y0)/dy)))
    def copy(self):
        w=Wave()
        w.data=self.data
        w.x=self.x
        w.y=self.y
        w.z=self.z
        w.note=self.note
    def __average1D(self,range):
        return self.data[range[0]:range[1]+1].sum()/(range[1]-range[0]+1)
    def __average2D(self,range1,range2):
        return self.data[int(range2[0]):int(range2[1])+1,int(range1[0]):int(range1[1])+1].sum()/(range1[1]-range1[0]+1)/(range2[1]-range2[0]+1)
class String(AutoSaved):
    class _stringdata(BaseObject):
        def _load(self,file):
            with open(file,'r') as f:
                self.data=f.read()
        def _init(self):
            self.data=''
    def _newobj(self,file):
        return self._stringdata(file)
    def __setattr__(self,key,value):
        if key=='data':
            super().__setattr__(key,str(value))
        else:
            super().__setattr__(key,value)

class Variable(AutoSaved):
    class _valdata(BaseObject):
        def _init(self):
            self.data=0
    def _newobj(self,file):
        return self._valdata(file)
class Dict(AutoSaved):
    class _dicdata(BaseObject):
        def _init(self):
            self.data={}
    def _newobj(self,file):
        return self._dicdata(file)
    def __getitem__(self,key):
        return self.data[key]
    def __setitem__(self,key,value):
        self.data[key]=value
        self.Save()
    def __delitem__(self,key):
        del self.data[key]
        self.Save()
    def __missing__(self,key):
        return None
    def __contains__(self,key):
        return key in self.data
    def __len__(self):
        return len(self.data)

class List(AutoSaved):
    class _listdata(BaseObject):
        def _init(self):
            self.data=[]
    def _newobj(self,file):
        return self._listdata(file)
    def __getitem__(self,key):
        return self.data[key]
    def __setitem__(self,key,value):
        self.data[key]=value
        self.Save()
    def append(self,value):
        self.data.append(value)
        self.Save()
    def remove(self,value):
        self.data.remove(value)
        self.Save()
    def __contains__(self,key):
        return key in self.data
    def __len__(self):
        return len(self.data)
#Command Extention

def mkdir(name):
    try:
        os.makedirs(name)
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
                BaseObject.OnMoveFile(name,name_to)
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
            if BaseObject._GetData(os.path.abspath(name)) is None:
                os.remove(name)
            else:
                sys.stderr.write('Error: Cannot remove. This file is in use.\n')
    except Exception:
        sys.stderr.write('Error: Cannot remove.\n')
def pwd():
    return os.getcwd()
def cd(direct=None):
    if direct is None or len(direct)==0:
        direct=__projectpath
    os.chdir(direct)
    for listener in __CDChangeListener:
        listener.OnCDChanged(pwd())
def home():
    return __projectpath
def addCDChangeListener(listener):
    __CDChangeListener.append(listener)
    listener.OnCDChanged(pwd())
def SetProjectPath(project):
    global __projectpath
    __projectpath=project



if __name__=='__main__':
    print('This is BaseObject')
    a=Variable()