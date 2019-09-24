import os,pyudev,glob
from datetime import datetime
import sched,time,shutil
from PIL import Image
from math import sqrt
import numpy as np
from time import sleep
from shutil import copytree, ignore_patterns
import matplotlib.pyplot as plt
import threading
from queue import Queue



class ImageSaving(threading.Thread):

    def __init__(self,C_queue,verbose=False,execlog=False):

        if execlog:
            print('{1}.__init__ called at\t{0}'.format(datetime.now(), type(self).__name__))

        threading.Thread.__init__(self)


        self.q1 = C_queue
        self.running = False
        self.paused = False

        self.t1 = None
        #self.run()


    def SaveLoop(self):
        while not self.q1.empty():
            Qimage = self.q1.get()
            sleep(0.2)
            plt.imsave("/home/pi/Pictures/"+ str(datetime.today()).replace(" ","_").replace(":","_") +'.tiff',Qimage)
            sleep(0.1)



    def pauseThread(self):
        
        self.paused = True



    def continueThreah(self):
        
        self.paused = False


    
    def run(self):
        
        self.running = True
        while self.running:
            if self.paused:
                sleep(0.5)
                pass
            else:
                self.t1 = threading.Timer(2,self.SaveLoop)
                self.t1.start()
                self.t1.join()
                