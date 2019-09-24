import os,pyudev,glob,time,shutil
from multiprocessing import Process,Pool,Pipe,Queue
from datetime import datetime
from picamera import PiCamera as Camera
from libs.smartPanTilt import SmartPanTilt
import picamera.array as pca
import numpy as np
from math import sqrt
from time import sleep
import threading
from queue import Queue
from Image_Acquire_Module import ImageAcquire
from Image_Save_Module import ImageSaving
from StageZoom_Movment_Module import StageZoomMovment


class CoreClass(Process):

    def __init__(self,verbose=False,execlog=False):
        

        if execlog:
            print('{1}.__init__ called at\t{0}'.format(datetime.now(), type(self).__name__))

        Process.__init__(self)

        self.C_panTilt = SmartPanTilt()
        self.context = pyudev.Context()
        self.C_queue = Queue()
        self._verbose = verbose
        self._execLog = execlog
        self.C_camera = None
        self.C_panTilt = SmartPanTilt()
        self.context = pyudev.Context()
        self.C_queue = Queue()
        

        self.stgOnRefern = False
        self.initialized = False
        self.lightIntenOk = False
        self.P_T_Home = False
        self.running = False
        self.USB_Dedected = False
        self.ClientDeviceName = None
        self.NameOfDevice = None

        self.t1 = None
        
        self.C_IA_Count = 10
        self.C_IS_Count = 10

        

    ## Perform an initialization operation for the stage and set it on the Acuiring position
    def StageInitialization(self):
        self.C_panTilt.MoveStageToMax()
        self.P_T_Home = True
        print("homing Done")
        sleep(0.5)
        self.MoveStageToReference()



    ## Perform the move to the reference point for check the light intensity
    def MoveStageToReference(self):
        deg=1
        count=0
        while count < 50:
            self.C_panTilt.moveSlowTiltRelative(deg,delay=0.02)
            count+=1
        self.stgOnRefern = True
        if self.stgOnRefern:
            self.lightIntensity()
            sleep(0.2)
            self.MoveStageToDefault()



    def MoveStageToDefault(self):
            self.stgOnRefern = False
            deg=-1
            count=0
            if self.P_T_Home :
                while count > -50:
                    self.C_panTilt.moveSlowTiltRelative(deg,delay=0.02)
                    count-=1
                self.P_T_onDefault = True
            



    ## Acquires an image and returns it as an array
    # @param asNDArray Bool: If True it returns the image as a numpy ndarray
    def getImgArray(self,asNDArray):
        print("befor output")
        output = pca.PiRGBArray(self.C_camera)
        print("after output")
        print("\n")
        print("befor Capture")
        
        self.C_camera.capture(output,'rgb')
        
        print("after capture")

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
        

    
    ##Check the light intensity , if light intensity is ok start Acquiring images and spectrums 
    def CheckLightIntensity(self): 
        print("i'm in checklight")
        resList = []
        for i in range (4):
            if i == 0:
                sleep(1) 
            print("befor getImgArray")     
            frame = self.getImgArray(True)
            print("after getImgArray")
            print("\n")
            print("befor CalcMeanIntens")
            result = self.calcMeanIntens(frame)
            print("after CalcMeanIntens")
            print("\n")
            print("befor Result append")
            resList.append(result)    
            print("after Result append")
            sleep(0.5)

        #print("\n".join([str(s) for s in resList]))
        tot = sum(resList) 
        avg = tot/ len(resList) 
        print(avg)

        return avg



    ##Performe a checking task of the light intensity, if condition is true start the sistem if not recheck
    def lightIntensity(self):
        print("I'm in lightIntensity")
        avg = self.CheckLightIntensity()
        
        while avg < 80:
            avg = self.CheckLightIntensity()

        self.lightIntenOk = True
        
    


    ##----------Client Functions----------Client Functions----------Client Functions----------##

    def FindUSB(self):
        print("Waiting Device")
        while not self.USB_Dedected:
            self.UsbDetected()
            sleep(0.05)

        
    ## Looks for the client device name for future elaborations
    def GetClientUsbName(self):
        list_of_direc = os.listdir('/media/pi/')
        full_path = ["/media/pi/{0}".format(x) for x in list_of_direc]
        USBDeviceName = (full_path, os.path.basename('/media/pi/'))
        USBDeviceName = str(USBDeviceName)
        #ClientDeviceName = min(full_path, key=os.path.basename) 
        self.ClientDeviceName = list_of_direc    
        print("ClientDeviceName  ",self.ClientDeviceName)
        



    ## Usb detector if a usb drive is connected
    def UsbDetected(self):
        for device in self.context.list_devices(MAJOR='8'):
            self.C_ImageAcquire.pauseThread()
            if (device.device_type == 'disk'):
                print ("{}, ({})".format(device.device_node, device.device_type)+" Usb Drive Detected")
                self.NameOfDevice = device.device_node
                self.running = False
                self.USB_Dedected = True
                sleep(1)
                self.GetClientUsbName()
                sleep(5)
                #moveAllFilesinDir()
                self.USBCreateFolder()
                break
            else:
                self.C_ImageAcquire.continueThreah()
                self.running = True


    ## Folder creator\generator nested in the client device for future elaborations
    def USBCreateFolder(self):
        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y-%H:%M:%S").replace("/","_").replace(":","_")
        Dpath = ("/media/pi/"+ str(self.ClientDeviceName[0]+"/") + date_time)
        #path =(Dpath + folder)
        try:
            os.makedirs(Dpath)
        except OSError:
            print ("Creation of the directory %s failed" % Dpath)
            
        else:
            print ("Successfully created the directory %s " % Dpath)
            f = open(os.path.join(Dpath, 'file.txt'), 'w')
            f.write('This is a new Folder created on. ' + date_time)
            f.close()
            self.OnFinish()
            sleep(0.2)
            self.UsbRemoved()


        


    ##Act's as an Identificator when the client device removed 
    def UsbRemoved(self):
        print("im in USBREMOVED")
        print(self.NameOfDevice)
        while self.NameOfDevice in [device.device_node for device in self.context.list_devices(MAJOR='8')]:
            sleep(2)
        self.USB_Dedected = False
        self.StageInitialization()

        #for device in self.context.list_devices(MAJOR='8'):
        #        while (device.device_node == self.NameOfDevice):
        #            print ("{}, ({})".format(device.device_node, device.device_type)+" Usb Drive Detected")
        #            self.GetClientUsbName()
        #            detected = True
        #            sleep(2)
        #            
        #        else:
        #            detected = False
        #            self.USB_Dedected = False
        #            self.StageInitialization()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  

        return False


    ## Image downloader from directory to the ubs drive
    def moveAllFilesinDir(self):
        print("im In MOVE ALL TO DIRECTORY")
        self.running = False
        srcDir = '/home/pi/Pictures/'
        dstDir = '/media/pi/'
        # Check if both the are directories
        if os.path.isdir(srcDir) and os.path.isdir(dstDir) :
            # Iterate over all the files in source directory
            for filePath in glob.glob(srcDir + '/*'):
                # Move each file to destination Directory
                print(filePath)
                shutil.move(filePath, dstDir)
            self.OnFinish()
        else:
            print("srcDir & dstDir should be Directories")
            self.running = True
            self.USB_Dedected = False
        
        while self.UsbRemoved():
            sleep(0.1)
        self.USB_Dedected = False
        self.running = True
        self.MoveStageToReference()


    
    def OnFinish(self):
        deg =15
        self.C_panTilt.moveSlowTiltRelative(deg,delay=0.02)
        sleep(0.5)
        self.C_panTilt.moveSlowTiltRelative(-deg,delay=0.02)



    def run(self):
        
        self.C_camera = Camera()
        self.StageInitialization()

        ##-----Classes Instantiating-----Classes Instantiating-----Classes Instantiating-----Classes Instantiating-----###
        self.C_ImageAcquire = ImageAcquire(self.C_camera,self.C_panTilt,self.C_queue,self._verbose,self._execLog)
        self.C_ImageSaving = ImageSaving(self.C_queue,self._verbose,self._execLog)
        ##------------------------------------------Start Point---------------------------------------------##
        print("Out of stage initialization")

        while self.C_IA_Count > 0:
            try:
                self.C_ImageAcquire.start()
            except:
                self.C_IA_Count -= 1
        
        while self.C_IS_Count > 0:
            try:
                self.C_ImageSaving.start()
            except:
                self.C_IS_Count -= 1


        self.running = True
        while self.running:
            self.t1 = threading.Timer(5,self.FindUSB)
            self.t1.start()
            self.t1.join()
            