import RPi.GPIO as GPIO
import time
import smtplib

SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8


photo_ch = 0
loop_counter = 0

#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
GPIO_TRIGGER = 18
GPIO_ECHO = 24

def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance
 
#port init
def init():
         GPIO.setwarnings(False)
         GPIO.cleanup()         #clean up at the end of your script
         GPIO.setmode(GPIO.BCM)     #to specify whilch pin numbering system
         # set up the SPI interface pins
         GPIO.setup(SPIMOSI, GPIO.OUT)
         GPIO.setup(SPIMISO, GPIO.IN)
         GPIO.setup(SPICLK, GPIO.OUT)
         GPIO.setup(SPICS, GPIO.OUT)
         #set GPIO direction (IN / OUT)
         GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
         GPIO.setup(GPIO_ECHO, GPIO.IN)
         
#read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)    

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def main():
         init()
         time.sleep(2)
         print("Starting flood water detection:\n")
         while True:
                  adc_value=readadc(photo_ch, SPICLK, SPIMOSI, SPIMISO, SPICS)
                  if adc_value == 0:
                           print("Water level: null\n")
                  elif adc_value>0 and adc_value<30 :
                           print("Water detected!\n")
                  elif adc_value>=30 and adc_value<200 :
                       dist = distance()
                       if dist<=50:
                           print ("Measured Distance = %.1f cm" % dist)
                           print("Alert! You are close to the flood gates")
                           time.sleep(0.5)
                       print("Flooding detected: Flood gates opened.")
                       print("water level:"+str("%.1f"%(adc_value/200.*100))+"%\n")
                       global loop_counter
                       loop_counter += 1
                       #print(loop_counter)
                       #print "adc_value= " +str(adc_value)+"\n"
                       time.sleep(1)
                       if loop_counter == 1:
                           server = smtplib.SMTP('smtp.gmail.com', 587)
                           server.starttls()
                           server.login("server_email_id", "server_password")
                           msg = "Alert! Flooding detected!"
                           server.sendmail("sender_email", "receiver_email", msg)
                           server.quit()
                           
                  
               
        

if __name__ == '__main__':
         try:
                  main()
                 
         except KeyboardInterrupt:
                  pass
GPIO.cleanup()