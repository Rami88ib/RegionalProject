
from datetime import datetime
import os

'''Mypantilt = SmartPanTilt()

My_File = open("values.txt")
with open("values.txt") as file:
    lines = file.readlines()
    deg = int(lines[0].split("=")[1])
    delay = float(lines[1].split("=")[1])
My_File.close()


def ZeroDeg():
    Mypantilt.MoveStageToMax()
    sleep(2)
    moveStage()

def moveStage():
    
    for i in range(5):
        
        Mypantilt.moveSlowTiltRelative(deg,delay)
        print(i)
        sleep(0.5)'''
def CreaCartella():
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y-%H:%M:%S").replace("/","_").replace(":","_")
    folder = date_time
    Dpath = ("C:/Users/Ibrahim Rami/Desktop/projregionale/"+date_time)
    #path =(Dpath + folder)
    try:
        os.makedirs(Dpath)
    except OSError:
        print ("Creation of the directory %s failed" % Dpath)
    else:
        print ("Successfully created the directory %s " % Dpath)
    print (Dpath)


CreaCartella()
