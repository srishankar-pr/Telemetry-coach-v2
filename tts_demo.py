import pyttsx3  
import time #to set refresh times
import ac_reader #to read the data from shared memory 


#static info doesnt change and  hence no need to refresh 

engine=pyttsx3.init()

engine.say("Good morning , i am your race engineer for the day")



#reading the physics info  and graphic 

while True:
    p=ac_reader.read_physics()
    g=ac_reader.read_graphics()
    if p and g:
        engine.say(f"Speed:{p.SpeedKmh:.1f} kilometres per hour")
        engine.runAndWait()
        time.sleep(3) #approx 60fps
    else:
        engine.say("Waiting for AC to start...")
        engine.runAndWait()
        time.sleep(1)
#initialising the text to speech engine 

