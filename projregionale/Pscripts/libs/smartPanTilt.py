from pantilthat import *
from time import sleep
from datetime import datetime

## Class for PanTilt smart movements
class SmartPanTilt(PanTilt):
    ## Class constructor
    # @param enable_lights Boolean: ?
    # @param safepanmax Float: The maximum wanted pan angle (default value is 90)
    # @param safepanmin Float: The minimum wanted pan angle (default value is -90)
    # @param safetiltmax Float: The maximum wanted tilt angle (default value is 90)
    # @param safetiltmin Float: The minimum wanted tilt angle (default value is -90)
    # @param verbose Boolean: If True enables a series of print useful for debugging
    # @param execlog Boolean: If True all the class member functions will print their name when called
    def __init__(self,
                 enable_lights=True,
                 idle_timeout=2, # Idle timeout in seconds
                 light_mode=WS2812,
                 light_type=RGB,
                 servo1_min=575,
                 servo1_max=2325,
                 servo2_min=575,
                 servo2_max=2325,
                 address=0x15,
                 i2c_bus=None,
                 safepanmax=90,
                 safepanmin=-90,
                 safetiltmax=90,
                 safetiltmin=-90,
                 verbose=False,
                 execlog=False):
        if execlog:
            print('{1}.__init__ called at\t{0}'.format(datetime.now(), type(self).__name__))
        PanTilt.__init__(self,enable_lights,idle_timeout,light_mode,light_type,servo1_min,servo1_max,servo2_min,servo2_max,address,i2c_bus)
        
        self._safePanMax = safepanmax
        self._safePanMin = safepanmin
        self._safeTiltMax = safetiltmax
        self._safeTiltMin = safetiltmin
        self._verbose = verbose
        self._execLog = execlog
     
    
    ## Genereric function to perform a slow continuous movement
    # @param moveFun Callable: A callable object that performs the actual movement
    # @param getFun Callable: A callable object that returns the current angle value for the wanted direction
    # @param deg Integer: The angle absolute value to travel to
    # @param delay Float: The time to wait between two consegutive movements (each of 1 degree) in seconds
    def moveSlowGen(self,moveFun,getFun,deg,delay):
        if self._execLog:
            print('{1}.moveSlowGen called at\t{0}'.format(datetime.now(), type(self).__name__))
        if not callable(moveFun):
            raise TypeError("MoveFun must be a callable obhject")
        if not callable(getFun):
            raise TypeError("GetFun must be a callable obhject")
        curr_angle = getFun()  # The current position of the motor
        if deg == curr_angle:
            if self._verbose:
                print("No movement to make")
            return

        diff = deg - curr_angle
        travel = diff if diff>0 else -1*diff  # Used to define the for loop range
        increment = 1 if diff>0 else -1
        toGoTo = curr_angle  # The intermediate angle value for the motor
        for i in range(travel):
            sleep(delay)
            toGoTo += increment
            moveFun(toGoTo)
    
    
    ## Performs a slow pan absolute movement 
    # @param deg Integer: The angle absolute value to travel to
    # @param delay Float: The time to wait between two consegutive movements (each of 1 degree) in seconds
    def moveSlowPan(self,deg,delay=0.25):
        if self._execLog:
            print('{1}.moveSlowPan called at\t{0}'.format(datetime.now(), type(self).__name__))
        if type(deg) != int:
            raise TypeError("deg must be integer")
        if deg<self._safePanMin:
            raise ValueError("Angle too low")
        elif deg>self._safePanMax:
            raise ValueError("Angle too high")
        self.moveSlowGen(self.pan,self.get_pan,deg,delay)
    
    
    ## Performs a slow pan relative movement 
    # @param deg Integer: The angle relative value to travel
    # @param delay Float: The time to wait between two consegutive movements (each of 1 degree) in seconds
    def moveSlowPanRelative(self,deg,delay=0.25):
        if self._execLog:
            print('{1}.moveSlowPanRelative called at\t{0}'.format(datetime.now(), type(self).__name__))
        if type(deg) != int:
            raise TypeError("deg must be integer")
        curr_pan = self.get_pan()
        finalDeg = deg+curr_pan
        if finalDeg<self._safePanMin:
            raise ValueError("Angle too low")
        elif finalDeg>self._safePanMax:
            raise ValueError("Angle too high")
        self.moveSlowGen(self.pan,self.get_pan,finalDeg,delay)
    
    
    ## Performs a slow tilt absolute movement 
    # @param deg Integer: The angle absolute value to travel to
    # @param delay Float: The time to wait between two consegutive movements (each of 1 degree) in seconds
    def moveSlowTilt(self,deg,delay=0.25):
        if self._execLog:
            print('{1}.moveSlowTilt called at\t{0}'.format(datetime.now(), type(self).__name__))
        if type(deg) != int:
            raise TypeError("deg must be integer")
        if deg<self._safePanMin:
            raise ValueError("Angle too low")
        elif deg>self._safePanMax:
            raise ValueError("Angle too high")
        self.moveSlowGen(self.tilt,self.get_tilt,deg,delay)
    
    
    ## Performs a slow tilt relative movement 
    # @param deg Integer: The angle relative value to travel
    # @param delay Float: The time to wait between two consegutive movements (each of 1 degree) in seconds
    def moveSlowTiltRelative(self,deg,delay=0.25):
        if self._execLog:
            print('{1}.moveSlowTiltRelative called at\t{0}'.format(datetime.now(), type(self).__name__))
        if type(deg) != int:
            raise TypeError("deg must be integer")
        curr_tilt = self.get_tilt()
        finalDeg = deg+curr_tilt
        if finalDeg<self._safePanMin:
            raise ValueError("Angle too low")
        elif finalDeg>self._safePanMax:
            raise ValueError("Angle too high")
        self.moveSlowGen(self.tilt,self.get_tilt,finalDeg,delay)


    
    ## Performs a Homing sction to start from 0 angel in tilt
    def MoveStageToMax(self):
        deg=1
        TiltHome = False
        while not TiltHome:
            try:
                self.moveSlowTiltRelative(deg,delay=0.01)
        
            except:
                TiltHome=True
                sleep(0.02)
                deg = -105
                self.moveSlowTiltRelative(deg,delay=0.02)