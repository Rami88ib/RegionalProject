from time import sleep
from libs.smartPanTilt import SmartPanTilt
import threading
from multiprocessing import Process
from datetime import datetime
import picamera.array as pca
import picamera as Camera



class StageZoomMovment(threading.Thread):

    def __init__(self,SmartPanTilt,verbose=False,execlog=False):

        if execlog:
            print('{1}.__init__ called at\t{0}'.format(datetime.now(), type(self).__name__))

        
        threading.Thread.__init__(self)
        
        ##--------- Variabili ---------##

        self.P_T_Home = False
        self.P_T_onPosition = False
        self.P_T_onDefault = False
        self.CameraZoomHome = False
        self.CameraZoomPos = 0
        self.my_SmPanTilt=SmartPanTilt()

        ##----------Functions----------##

    
    ##Performe a Homing action to start from the Zero angel
    def MoveStageToMax(self):
        self.my_SmPanTilt.MoveStageToMax()
         
        self.P_T_Home = True
        print("homing Done")
        sleep(0.5)
        self.MoveStageToPoint()

    ## check the light intensity moving the stage to the landmark point
    def MoveStageToPoint(self):
        
        deg=1
        count=0
        while count < 45:
            self.my_SmPanTilt.moveSlowTiltRelative(deg,delay=0.02)
            count+=1
        self.P_T_onPosition = True
        if self.P_T_onPosition:
            print("im on position")
            self.MoveStageToDefault()


    def MoveStageToDefault(self):
        self.P_T_onPosition = False
        deg=-1
        count=0
        if self.P_T_Home :
            while count > -45:
                self.my_SmPanTilt.moveSlowTiltRelative(deg,delay=0.02)
                count-=1
            
            self.P_T_onDefault = True
            

    '''##Perform Homing for the camera axe
    def CameraZoomHoming(self):
        global CameraZoomPos
        step=1 # configure from client config-file.txt
        global CameraZoomHome
        while not self.CameraZoomHome:
            try:
                print("Look for the Zooming functions",step)
            
            except:
                CameraZoomHome=True
                # look for code to set the zome on x1
                CameraZoomPos =  0


    ##Performe the zoom in action Usualy increment the zoom by 1x
    def CameraZoomIn(self):
        global CameraZoomPos
        global CameraZoomHome
        step = 1 # configure from client config-file.txt
        if self.CameraZoomHome:
            print("move the Zoom X steps")
            self.CameraZoomPos = CameraZoomPos + step
        else:
            self.CameraZoomHoming()


    ##Performe the zoom out action Usualy decrement the zoom by 1x        
    def CameraZoomOut(self):
        global CameraZoomPos
        global CameraZoomHome
        if CameraZoomHome:
            print("move the Zoom -CameraZoomPos ")
            CameraZoomPos = CameraZoomPos - CameraZoomPos
            
        else:
            self.CameraZoomHoming()   '''  


