import os,logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from . import BaseClass

class ExtendMdiSubWindowBase(QMdiSubWindow):
    pass
class SizeAdjustableWindow(ExtendMdiSubWindowBase):
    def __init__(self):
        super().__init__()
        #Mode #0 : Auto, 1 : heightForWidth, 2 : widthForHeight
        self.__mode=0
        self.__aspect=0
        self.setWidth(0)
        self.setHeight(0)
        self.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
    def setWidth(self,val):
        if self.__mode==2:
            self.__mode=0
        if val==0:
            self.setMinimumWidth(35)
            self.setMaximumWidth(100000)
        else:
            self.setMinimumWidth(val)
            self.setMaximumWidth(val)
    def setHeight(self,val):
        if self.__mode==1:
            self.__mode=0
        if val==0:
            self.setMinimumHeight(35)
            self.setMaximumHeight(100000)
        else:
            self.setMinimumHeight(val)
            self.setMaximumHeight(val)

class AttachableWindow(SizeAdjustableWindow):
    resized=pyqtSignal()
    moved=pyqtSignal()
    closed=pyqtSignal()
    def __init__(self):
        super().__init__()
    def resizeEvent(self,event):
        self.resized.emit()
        return super().resizeEvent(event)
    def moveEvent(self,event):
        self.moved.emit()
        return super().moveEvent(event)
    def closeEvent(self,event):
        self.closed.emit()
        return super().closeEvent(event)
class ExtendMdiSubWindow(AttachableWindow):
    mdimain=None
    __wins=[]
    def __init__(self, title=None):
        logging.debug('[ExtendMdiSubWindow] __init__')
        super().__init__()
        ExtendMdiSubWindow._AddWindow(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()
    @classmethod
    def CloseAllWindows(cls):
        for g in cls.__wins:
            g.close()
    @classmethod
    def _AddWindow(cls,win):
        cls.__wins.append(win)
        if cls.mdimain is not None:
            cls.mdimain.addSubWindow(win)
    @classmethod
    def _RemoveWindow(cls,win):
        cls.__wins.remove(win)
        cls.mdimain.removeSubWindow(win)
    @classmethod
    def _Contains(cls,win):
        return win in cls.__wins
    @classmethod
    def AllWindows(cls):
        return cls.__wins
    def closeEvent(self,event):
        ExtendMdiSubWindow._RemoveWindow(self)
        super().closeEvent(event)

class AutoSavedWindow(ExtendMdiSubWindow):
    __list=None
    _isclosed=False
    _restore=False
    @classmethod
    def _StartProject(cls):
        __list=BaseClass.List(BaseClass.home()+'/.lys/winlist.lst')
    @classmethod
    def _IsUsed(cls,path):
        return path in cls.__list.data
    @classmethod
    def _AddAutoWindow(cls,win):
        if not win.FileName() in cls.__list.data:
            cls.__list.append(win.FileName())
    @classmethod
    def _RemoveAutoWindow(cls,win):
        if win.FileName() in cls.__list.data:
            cls.__list.remove(win.FileName())
    @classmethod
    def RestoreAllWindows(cls):
        from . import LoadFile
        cls._restore=True
        BaseClass.mkdir(BaseClass.home()+'/.lys/wins')
        for path in cls.__list.data:
            try:
                w=LoadFile.load(path)
                if path.find(BaseClass.home()+'/.lys/wins') > -1:
                    w.Disconnect()
            except:
                pass
        cls._restore=False
    @classmethod
    def StoreAllWindows(cls):
        cls._isclosed=True
        for w in cls.AllWindows():
            w.close()
        cls._isclosed=False
    @classmethod
    def _IsClosed(cls):
        return cls._isclosed
    @classmethod
    def _onRestore(cls):
        return cls._restore
    def NewTmpFilePath(self):
        BaseClass.mkdir(BaseClass.home()+'/.lys/wins')
        for i in range(1000):
            path=BaseClass.home()+'/.lys/wins/'+self._prefix()+str(i).zfill(3)+self._suffix()
            if not AutoSavedWindow._IsUsed(path):
                return path
        print('Too many windows.')
    def __new__(cls, file=None, title=None):
        logging.debug('[AutoSavedWindow] __new__ called.')
        #ChangeProject
        cls._StartProject()
        if cls._restore:
            return super().__new__(cls)
        if AutoSavedWindow._IsUsed(file):
            logging.debug('[AutoSavedWindow] found loaded window.')
            return None
        return super().__new__(cls)
    def __init__(self, file=None, title=None):
        logging.debug('[AutoSavedWindow] __init__ called.')
        #ChangeProject
        self._StartProject()
        try:
            self.__file
        except Exception:
            logging.debug('[AutoSavedWindow] new window will be created.')
            if file is None:
                logging.debug('[AutoSavedWindow] file is None. New temporary window is created.')
                self.__isTmp=True
                self.__file=self.NewTmpFilePath()
            else:
                logging.debug('[AutoSavedWindow] file is ' + file + '.')
                self.__isTmp=False
                self.__file=file
            if title is not None:
                super().__init__(title)
            else:
                super().__init__(self.Name())
            self._init()
            self.__Load(self.__file)
            self.Save()
            AutoSavedWindow._AddAutoWindow(self)
    def setLoadFile(self,file):
        self.__loadFile=os.path.abspath(file)
    def __Load(self,file):
        logging.debug('[AutoSavedWindow] __Load called.')
        if file is not None:
            self.__file=os.path.abspath(file)
        if os.path.exists(self.__file):
            self._load(self.__file)

    def FileName(self):
        return self.__file
    def Name(self):
        nam,ext=os.path.splitext(os.path.basename(self.FileName()))
        return nam
    def IsConnected(self):
        return not self.__isTmp
    def Disconnect(self):
        self.__isTmp=True
    def Save(self,file=None):
        if file is not None:
            self._save(file)
            self.__isTmp=False
        else:
            self._save(self.__file)

    def closeEvent(self,event):
        if (not AutoSavedWindow._IsClosed()) and (not self.IsConnected()):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok==QMessageBox.Cancel:
                event.ignore()
                return
        if not AutoSavedWindow._IsClosed():
            AutoSavedWindow._RemoveAutoWindow(self)
            if not self.IsConnected():
                BaseClass.remove(self.__file)
        return super().closeEvent(event)
