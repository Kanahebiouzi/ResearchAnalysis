import numpy as np
from .Functions import *
from scipy import optimize

class Fitting(object):
    class funcSum(function):
        def __init__(self,f1,f2):
            self.f1=f1
            self.f2=f2
        def func(self,x,*p):
            return self.f1.func(x,*p[:self.f1.nparam()])+self.f2.func(x,*p[self.f1.nparam():])
        def nparam(self):
            return self.f1.nparam()+self.f2.nparam()
    def __init__(self):
        self.func=none()
    def addFunction(self,f):
        self.func=self.funcSum(self.func,f)
    def fit(self,xdata,ydata,guess=None,bounds=None):
        if guess is None:
            estimation=[]
            for f in range(self.func.nparam()):
                estimation.append(1)
        else:
            estimation=guess
        if bounds is None:
            res, tmp = optimize.curve_fit(self.func.func,xdata,ydata,estimation)
        else:
            res, tmp = optimize.curve_fit(self.func.func,xdata,ydata,estimation,bounds=bounds)
        return res, tmp

if __name__ == '__main__':
    xdata = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
    ydata = [0,1,2,3,4,5,6,7,8,9,8, 7, 6, 5, 4, 3, 2, 1]

    fit=Fitting()
    fit.addFunction(linear())
    res, tmp=fit.fit(xdata,ydata)
    print(res)
    def lin(x,a,b):
        return a*x+b
    res, tmp=optimize.curve_fit(lin,xdata,ydata)
    print(res)
