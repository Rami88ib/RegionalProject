import os,pyudev,glob
from datetime import datetime
import sched,time,shutil
from picamera import PiCamera as camera
import picamera.array as pca
from PIL import Image
from math import sqrt
import numpy as np
from time import sleep
from shutil import copytree, ignore_patterns
from libs.smartPanTilt import SmartPanTilt
import matplotlib.pyplot as plt
import threading
from queue import Queue



class ImageAcquire(threading.Thread):

    def __init__(self,C_camera,C_panTilt,C_queue,verbose=False,execlog=False):

        if execlog:
            print('{1}.__init__ called at\t{0}'.format(datetime.now(), type(self).__name__))

        threading.Thread.__init__(self)


        self.A_camera = C_camera
        self.my_PT = C_panTilt
        self.q1 = C_queue
        self.running = False
        self.P_T_onPosition = False
        self.P_T_onDefault = False
        self.P_T_Home = True
        self.threadRunning = False
        self.paused = False
        self.loopnumber = 0
        
        #self.t1 = threading.Timer(5,self.CaptureLoop)
        self.t1 = None
        #self.run()

        
    
    ## Acquires an image and returns it as an array
    # @param asNDArray Bool: If True it returns the image as a numpy ndarray
    def getImgArray(self,asNDArray):

        output = pca.PiRGBArray(self.A_camera)
        self.A_camera.capture(output,'rgb')

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


    def CheckLightIntensity(self):
        resList = []
        for i in range (4):
            if i == 0:
                sleep(1)      
            frame = self.getImgArray(True)
            result = self.calcMeanIntens(frame)
            resList.append(result)    
            sleep(1)

        #print("\n".join([str(s) for s in resList]))
        tot = sum(resList) 
        avg = tot/ len(resList) 
        print(avg)

        return avg


    ##Performe a checking task of the light intensity, if condition is true start the sistem if not recheck
    def lightIntensity(self):
        print("I'm in lightIntensity")
        self.avg = self.CheckLightIntensity()
        
        while self.avg < 80:
            self.avg = self.CheckLightIntensity()
        sleep(0.2)
        self.MoveStageToDefault()


    ## Check if lightintensuty is over the break down point 
    def doubleCheck(self,frame=None):
        print("Im in double Check")
        limit = 80.00

        if frame is None:
            frame = self.getImgArray(True)
        result = self.calcMeanIntens(frame)

        #if result > limit:
        #    Lsup = Lsup+1
        #else:
        #    Linf = Linf+1
        
        if result<limit: #Lsup < Linf:
            print("I will ReCheck the light")
            sleep(2)
            self.ReDoubleCheck()


    def ReDoubleCheck(self):
        print("Im in Redouble Check")
        limit = 80.00

        frame = self.getImgArray(True)
        result = self.calcMeanIntens(frame)

        #if result > limit:
        #    Lsup = Lsup+1
        #else:
        #    Linf = Linf+1
        
        if result < limit:  #Lsup < Linf:
            print("Light is low system is calling the lightintensity")
            print("prima")
            self.pauseThread()
        print("dopo")
        self.MoveStageToReference()



    ## Perform the move to the reference point for check the light intensity
    def MoveStageToReference(self):
        print("moving")
        self.P_T_onDefault = False
        deg=1
        count=0
        while count < 50:
            self.my_PT.moveSlowTiltRelative(deg,delay=0.02)
            count+=1
        self.P_T_onPosition = True
        if self.P_T_onPosition:
            self.lightIntensity()



    def MoveStageToDefault(self):
            self.stgOnRefern = False
            deg=-1
            count=0
            if self.P_T_Home :
                while count > -50:
                    self.my_PT.moveSlowTiltRelative(deg,delay=0.02)
                    count-=1
            self.P_T_onDefault = True
            sleep(0.5)
            self.continueThreah()
            
    # look how to call the function move to THE REFER POINT 
            #MoveStageToPoint()



    def CaptureLoop(self):

        print("im in CAPTURE LOOP")
        self.loopnumber = self.loopnumber + 1
    
        frame = self.getImgArray(True)
    
        self.doubleCheck(frame)

        frame90 = frame[::-1,::,:]
        self.q1.put(frame90)
        #plt.imsave("/home/pi/Pictures/"+ str(datetime.today()).replace(" ","_").replace(":","_") +'.tiff',frame90)
        print("Im no the loop num:  ",self.loopnumber)
        self.GetSize()
        #else:
            #self.t1.start()
            #self.running = True
        

        #if not running:
            #t1.cancel()
        '''try: 
            threading.Timer(3,CaptureLoop).start()
            
        except:
            print("some thing went wrong")
            #my_thread.cancel()
        if not running:
            threading.Timer(3,CaptureLoop).cancel()
            print("canciling thread")
            #threading.Timer(3,GetSize).cancel()'''
            
##############################################################
    '''def SaveLoop(self):
        while not self.q1.empty():
            self.q1.get()
            plt.imsave("/home/pi/Pictures/"+ str(datetime.today()).replace(" ","_").replace(":","_") +'.tiff')
        '''



    ## Get the size of the directory and send a flag once it over the limit
    def GetSize(self,start_path = '/home/pi/Pictures'):
        print("I'm in GetSize")
        dircSize=0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    dircSize += os.path.getsize(fp)

        print(dircSize/1000000000, 'GB')
        
        
        if dircSize > 40000000.00:
            self.deleteOldestImage()


    ## Deleting the oldest image to avoid memory overflow
    def deleteOldestImage(self):
        print("Deleting IMAGE")
        list_of_files = os.listdir('/home/pi/Pictures/')
        list_of_files.sort()
        full_path = ["/home/pi/Pictures/{0}".format(x) for x in list_of_files]
        oldest_file = min(full_path, key=os.path.basename)
        os.remove(oldest_file)     

    

    def pauseThread(self):
        
        self.paused = True



    def continueThreah(self):
        
        self.paused = False


    
    def run(self):
        print("Class started")
        
        self.running = True
        while self.running:
            if self.paused:
                sleep(0.5)
                pass
            else:
                self.t1 = threading.Timer(5,self.CaptureLoop)
                self.t1.start()
                self.t1.join()
                