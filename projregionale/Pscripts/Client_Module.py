import os,pyudev,glob
from time import sleep
import time,shutil
from datetime import datetime




        context = pyudev.Context()
        NameOfDevice = None
        running = False
        USB_Dedected = False
        ClientDeviceName = None





def FindUSB():
    global USB_Dedected
    while not USB_Dedected:
        UsbDetected()

        
## Looks for the client device name for future elaborations
def GetClientUsbName():
    global ClientDeviceName
    list_of_direc = os.listdir('/media/pi/')
    full_path = ["/media/pi/{0}".format(x) for x in list_of_direc]
    USBDeviceName = (full_path, os.path.basename('/media/pi/'))
    USBDeviceName = str(USBDeviceName)
    #ClientDeviceName = min(full_path, key=os.path.basename) 
    ClientDeviceName = list_of_direc    
    print("ClientDeviceName  ",ClientDeviceName)
    



## Usb detector if a usb drive is connected
def UsbDetected():
    global running
    global USB_Dedected 
    global ClientDeviceName
    for device in context.list_devices(MAJOR='8'):
        if (device.device_type == 'disk'):
            print ("{}, ({})".format(device.device_node, device.device_type)+" Usb Drive Detected")
            global NameOfDevice
            NameOfDevice = device.device_node
            running = False
            USB_Dedected = True
            sleep(1)
            GetClientUsbName()
            sleep(1)
            #moveAllFilesinDir()
            USBCreateFolder()
            break
        else:
            running = True


## Folder creator\generator nested in the client device for future elaborations
def USBCreateFolder():
    global ClientDeviceName
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y-%H:%M:%S").replace("/","_").replace(":","_")
    Dpath = ("/media/pi/"+ str(ClientDeviceName[0]+"/") +date_time)
    #path =(Dpath + folder)
    try:
        os.makedirs(Dpath)
    except OSError:
        print ("Creation of the directory %s failed" % Dpath)
        
    else:
        print ("Successfully created the directory %s " % Dpath)
        f = open(os.path.join(Dpath, 'file.txt'), 'w')
        f.write('This is the new file.')
        f.close()

    


##Act's as an Identificator when the client device removed 
def UsbRemoved():
    global NameOfDevice
    print("im in USBREMOVED")

    detected = False
    
    print(NameOfDevice)
    for device in context.list_devices(MAJOR='8'):
        if (device.device_node == NameOfDevice):
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
    dstDir = '/media/pi/'
    # Check if both the are directories
    if os.path.isdir(srcDir) and os.path.isdir(dstDir) :
        # Iterate over all the files in source directory
        for filePath in glob.glob(srcDir + '/*'):
            # Move each file to destination Directory
            print(filePath)
            shutil.move(filePath, dstDir)
        #OnFinish()
    else:
        print("srcDir & dstDir should be Directories")
        running = True
        USB_Dedected = False
    
    while UsbRemoved():
        sleep(0.1)
    USB_Dedected = False
    running = True
    #MoveStageToPoint()

FindUSB()

'''def OnFinish():
    deg = 10
    my_SmPanTilt.moveSlowTiltRelative(deg,delay=0.02)
    sleep(1)
    my_SmPanTilt.moveSlowTiltRelative(-deg,delay=0.02)'''
