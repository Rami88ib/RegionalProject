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
from Pscripts.libs.smartPanTilt import SmartPanTilt
import matplotlib.pyplot as plt
import threading


s = sched.scheduler(time.time, time.sleep)
camera1 = camera()
context = pyudev.Context()
my_SmPanTilt=SmartPanTilt()
TypeOfDevice = None
running = False
P_T_onPosition = False
P_T_onDefault = False
P_T_Home = False
USB_Dedected = False





def MoveStageToMax():
    my_SmPanTilt.MoveStageToMax()
    global P_T_Home 
    P_T_Home = True
    print("homing Done")
    sleep(0.5)
    MoveStageToPoint()

## check the light intensity moving the stage to the landmark point
def MoveStageToPoint():
    global USB_Dedected
    USB_Dedected = False
    global P_T_onPosition
    deg=1
    count=0
    while count < 45:
        my_SmPanTilt.moveSlowTiltRelative(deg,delay=0.02)
        count+=1
    P_T_onPosition = True
    if P_T_onPosition:
        lightIntensity()


def MoveStageToDefault():
    global P_T_onPosition
    P_T_onPosition = False
    deg=-1
    count=0
    if P_T_Home :
        while count > -45:
            my_SmPanTilt.moveSlowTiltRelative(deg,delay=0.02)
            count-=1
    #global P_T_onDefault
    #P_T_onDefault = True
    startOperation()
    
   
## Acquires an image and returns it as an array
# @param asNDArray Bool: If True it returns the image as a numpy ndarray
def getImgArray(asNDArray):

    output = pca.PiRGBArray(camera1)
    camera1.capture(output,'rgb')

    if asNDArray:
        return output.array
    else:
        return output


## Calculates the mean perceived intensity of a RGB image array
# @param frame Ndarray: A three dimensional array with rgb image values
def calcMeanIntens(frame):

    r = np.mean(frame[:,:,0])
    g = np.mean(frame[:,:,1])
    b = np.mean(frame[:,:,2])
    result = sqrt(0.241*(r**2) + 0.691*(g**2) + 0.068*(b**2))

    return result


def CheckLightIntensity():
    resList = []
    for i in range (4):
        if i == 0:
            sleep(1)      
        frame = getImgArray(True)
        result = calcMeanIntens(frame)
        resList.append(result)    
        sleep(1)

    #print("\n".join([str(s) for s in resList]))
    tot = sum(resList) 
    avg = tot/ len(resList) 
    print(avg)

    return avg


##Performe a checking task of the light intensity, if condition is true start the sistem if not recheck
def lightIntensity():
    print("I'm in lightIntensity")
    avg = CheckLightIntensity()
    
    while avg < 80:
      avg = CheckLightIntensity()

    MoveStageToDefault()    


## Check if lightintensuty is over the break down point 
def doubleCheck(frame=None):
    print("Im in double Check")
    limit = 80.00
    Lsup = 0
    Linf = 0
    if frame is None:
        frame = getImgArray(True)
    result = calcMeanIntens(frame)

    #if result > limit:
    #    Lsup = Lsup+1
    #else:
    #    Linf = Linf+1
    
    if result<limit: #Lsup < Linf:
        print("I will ReCheck the light")
        ReDoubleCheck()


def ReDoubleCheck():
    print("Im in Redouble Check")
    limit = 80.00
    Lsup = 0
    Linf = 0
    frame = getImgArray(True)
    result = calcMeanIntens(frame)

    #if result > limit:
    #    Lsup = Lsup+1
    #else:
    #    Linf = Linf+1
    
    if result < limit:  #Lsup < Linf:
        print("Light is low system is calling the lightintensity")
        global running 
        running = False
        MoveStageToPoint()
        
        
## Perform as a starter Clock for image and spectrum acquisition
def startOperation():
    print("I'm in StartOperation")
    global running 
    running = True
    s.enter(3, 1, do_something, (s,))
    s.run()


## Perform as a Clock for image and spectrum acquisition
def do_something(sc): 
    print("I'm in do_something")
    global running
    while running == True:
        frame = getImgArray(True)
        #camera1.capture("/home/pi/Pictures/"+ str(datetime.today()).replace(" ","_").replace(":","_") +'.jpg')
        doubleCheck(frame)
        frame90 = frame[::-1,::,:]
        plt.imsave("/home/pi/Pictures/"+ str(datetime.today()).replace(" ","_").replace(":","_") +'.tiff',frame90)
        GetSize()
        global USB_Dedected
        if not USB_Dedected:
            UsbDetected()
        # do your stuff
        event2 = s.enter(3, 1, do_something, (sc,))
        sc.run()
    if not running:
        event2 = s.enter(3, 1, do_something, (sc,))
        sc.cancel(event2)
        #while not running:
          #  UsbRemoved()
            


## Get the size of the directory and send a flag once it over the limit
def GetSize(start_path = '/home/pi/Pictures'):
    print("I'm in GetSize")
    dircSize=0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                dircSize += os.path.getsize(fp)

    print(dircSize/1000000000, 'GB')
    
    global running
    if dircSize > 40000000.00 and running:
        deleteOldestImage()


## Deleting the oldest image to avoid memory overflow
def deleteOldestImage():
    print("Deleting IMAGE")
    list_of_files = os.listdir('/home/pi/Pictures/')
    list_of_files.sort()
    full_path = ["/home/pi/Pictures/{0}".format(x) for x in list_of_files]
    oldest_file = min(full_path, key=os.path.basename)
    os.remove(oldest_file)     


## Usb detector if a usb drive is connected
def UsbDetected():
    global running
    global USB_Dedected 
    for device in context.list_devices(MAJOR='8'):
        if (device.device_type == 'disk'):
            print ("{}, ({})".format(device.device_node, device.device_type)+" Usb Drive Detected")
            global TypeOfDevice
            TypeOfDevice = device.device_node
            running = False
            USB_Dedected = True
            moveAllFilesinDir()
            break
        else:
            running = True

            

def UsbRemoved():
    global TypeOfDevice
    print("im in USBREMOVED")

    detected = False
    
    print(TypeOfDevice)
    for device in context.list_devices(MAJOR='8'):
        if (device.device_node == TypeOfDevice):
            print ("{}, ({})".format(device.device_node, device.device_type)+" Usb Drive Detected")
            detected = True
            #break ############ continua da qui                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
    return detected


## Image downloader from directory to the ubs drive
def moveAllFilesinDir():
    print("im In MOVE ALL TO DIRECTORY")
    global running
    global USB_Dedected 
    running = False
    srcDir = '/home/pi/Pictures/'
    dstDir = '/media/pi/FABCREAUSB/'
    # Check if both the are directories
    if os.path.isdir(srcDir) and os.path.isdir(dstDir) :
        # Iterate over all the files in source directory
        for filePath in glob.glob(srcDir + '/*'):
            # Move each file to destination Directory
            print(filePath)
            shutil.move(filePath, dstDir)
        OnFinish()
    else:
        print("srcDir & dstDir should be Directories")
        running = True
        USB_Dedected = False
    
    while UsbRemoved():
        sleep(0.1)
    USB_Dedected = False
    running = True
    MoveStageToPoint()



def OnFinish():
    deg = 10
    my_SmPanTilt.moveSlowTiltRelative(deg,delay=0.02)
    sleep(1)
    my_SmPanTilt.moveSlowTiltRelative(-deg,delay=0.02)



## delete all Images once the upload to the usb drive is done
'''def ImageDeleteAll():  
    
    directory = '/home/pi/Pictures/'
    for i in glob.glob(os.path.join(directory,"/*")):
        try:
            os.remove(i)  
            print("All images Removed")
        except OSError:
            pass

    global running
    while not running:
        UsbRemoved()'''
    # controlla se funziona
    #if i in glob.glob(os.path.join(directory,"/*")) == 0:
       # running = True


MoveStageToMax()       