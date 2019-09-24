from multiprocessing import Process,Queue,Pipe
from datetime import datetime
import sched,time,shutil,scipy
import picamera.array as pca
from picamera import PiCamera as camera
import numpy as np
from math import sqrt
import threading



class ImageAcquire(Process):

    def __init__(self,Camera,onReference=False,verbose=False,execlog=False):

        if execlog:
            print('{1}.__init__ called at\t{0}'.format(datetime.now(), type(self).__name__))

        Process.__init__(self,Camera,onReference,verbose,execlog)
        s = sched.scheduler(time.time, time.sleep)
        self._onRefr = onReference
        self.s = sched.scheduler(time.time, time.sleep)
        self.q = Queue()
        self.running  = False
        self.Acamera = Camera
        self.FrameInQueue = False

        MoudleStart(self)


        ## Acquires an image and returns it as an array
        # @param asNDArray Bool: If True it returns the image as a numpy ndarray
        def getImgArray(self,asNDArray):

            output = pca.PiRGBArray(self.Acamera)
            self.Acamera.capture(output,'rgb')

            if asNDArray:
                return output.array
            else:
                return output



        ## Calculates the mean perceived intensity of a RGB image array
        # @param frame Ndarray: A three dimensional array with rgb image values
        def calcMeanIntens(self,frame):

            r = np.mean(frame[:,:,0])
            g = np.mean(frame[:,:,1])
            b = np.mean(frame[:,:,2])
            result = sqrt(0.241*(r**2) + 0.691*(g**2) + 0.068*(b**2))

            return result

        

        def MoudleStart(self):
            global running 
            running = True
            s.enter(3, 1, StartAcquire, (s,))
            s.run()


        ## Perform as a starter Clock for image and spectrum acquisition
        def StartAcquire(self,sc):
            global running
            while running:            
                try:
                    sc.enter(60, 1, ImageAcquire, (sc,))
                    sc.run()
                except :
                    running = False
                    #look for pipe communication

        ##
        def ImageAcquire(self,q,frame): 
            print("I'm in do_something")
            global running
            global FrameInQueue
            while running == True:
                frame = getImgArray(self,True)
                CheckFrameLight(frame)
                frame90 = frame[::-1,::,:]
                q.put(frame90)
                FrameInQueue = True

                #plt.imsave("/home/pi/Pictures/"+ str(datetime.today()).replace(" ","_").replace(":","_") +'.tiff',frame90)



        ## Check if lightintensuty is over the break down point 
        def CheckFrameLight(self,frame=None):
            print("Im in double Check")
            limit = 80.00
            if frame is None:
                frame = getImgArray(self,True)
            result = calcMeanIntens(self,frame)
            
            if result<limit: #Lsup < Linf:
                print("I will ReCheck the light")
                DoubleCheck(self)



        def DoubleCheck(self):
            print("Im in Redouble Check")
            limit = 80.00
            frame = getImgArray(self,True)
            result = calcMeanIntens(self,frame)

            if result < limit:
                print("Light is low system is calling the lightintensity")
                global running 
                running = False
