import RPi.GPIO as GPIO
import os
import pyrebase
import drivers
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from gpiozero import MotionSensor, CPUTemperature
from time import sleep
from matrixKeypad_RPi_GPIO import keypad
from threading import Thread
from picamera import PiCamera
from twilio.rest import Client

#Host ip address and port
host_name = '192.168.43.115'
host_port = 8000

#Global variable
count = 1
count2 = 1
count3 = 1

#GPIO Port Numbers & Initializing classes
greenLED = 21
redLED = 16
orangeLED = 20
buzzer = 26
pir = MotionSensor(19)
kp = keypad()
display = drivers.Lcd()
camera = PiCamera()

#For email alerts
from_email_addr = 'kamoraspi98@gmail.com'
from_email_password = 'Kamogelo@1998'
to_email_addr = "mrditshego98@gmail.com"      

def digitreturn():
    r = None
    while r == None:
        r = kp.getKey()
    return r

def countDown():
    countD = 5
    while countD >= 0:
        display.lcd_display_string("System armimg in: ", 1)
        display.lcd_display_string(str(countD) + "       ", 2)
        countD = countD - 1
        sleep(1)
                
def emailNotify():
    global count2
    #Camera setup
    #camera.resolution = (640,480)
    #camera.rotation = 180
    #camera.start_recording('alert_video.h264')
    #camera.wait_recording(5)
    #camera.stop_recording()
                 
    #convert from h264 to .mp4
    #command = "MP4Box -add alert_video.h264 alert_video.mp4"
    #call([command], shell=True)
    #print("Video Converted")
    
    #Mail body content
    mail_content = '''Good Day Kamogelo,

Please note that there is an intruder at your house, motion has been detected. See an attachment(Video) below for reference.

Send by Smart Security System
    '''
    
    #Message creation
    msg = MIMEMultipart()
    msg['Subject'] = 'INTRUDER ALERT..!!'
    msg['From'] = from_email_addr
    msg['To'] = to_email_addr
    
    #Body content
    msg.attach(MIMEText(mail_content,'plain'))
    
    #Video attachment
    filename = "Alert_video.mp4"
    Captured = '/home/pi/Desktop/' + str(count2) + 'Alert_video.mp4'
    count2 = count2 + 1
    ft=open(Captured,'rb')
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((ft).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition','attachment',filename='video' + datetime.now().strftime(' %a %d-%m-%Y %H:%M:%S')+".mp4")
    msg.attach(p)
    print("attach successful")
    
    #removing .h264 and .mp4 extra files
    #os.remove("/home/pi/Desktop/alert_video.h264")
    #os.rename('alert_video.mp4',datetime.now().strftime('%d-%m-%Y_%H:%M:%S')) 

    #Sending an email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email_addr, from_email_password)
    server.sendmail(from_email_addr, to_email_addr, msg.as_string())
    server.quit()
    print("email sent")
    
def smsNotify():
    account_sid = "ACe225d30b9a3cde29a74d154527fb17b9"
    auth_token = "1f3f8de9026857a77aaacc9d16aa3e46"

    client = Client(account_sid, auth_token)

    message = client.api.account.messages.create(
                    to = "+27761083017",
                    from_ = "+14435438417",
                    body = "Good Day Kamogelo, Please note that there is an intruder at your house, motion has been detected. Check your emails for additional information, call 10111")
    
    print("SMS Sent")
 
def smsNotifyDisarm():
    account_sid = "ACe225d30b9a3cde29a74d154527fb17b9"
    auth_token = "1f3f8de9026857a77aaacc9d16aa3e46"

    client = Client(account_sid, auth_token)

    message = client.api.account.messages.create(
                    to = "+27761083017",
                    from_ = "+14435438417",
                    body = "System has been disarmed")
    
    print("SMS Sent")


def control_local():
    #Keypad variables
    digitCount = 0
    pin = [0,0,0,0]
    control_local.finalPin = "0000"
    validPin = "1231"
    armPin = "7789"
    incorrectPin = 2
    setupGPIO()

    # Initializing classes
    kp = keypad()
    display = drivers.Lcd()
    
    #Default message on LCD
    display.lcd_display_string("Hello there!!!", 1)
    
    while True:
        setupGPIO()
        digit = digitreturn()
        print (digit)
        display.lcd_display_string("Arm or Disarm                       ", 1)
        display.lcd_display_string("Code: " + str(digit) + "         ", 2)
        pin[digitCount] = digit
        digitCount = digitCount + 1
        sleep(0.25)
        
        if digitCount == 4:
            control_local.finalPin = (str(pin[0]) + str(pin[1]) + str(pin[2]) + str(pin[3]))
            print(control_local.finalPin)
            
            if validPin == control_local.finalPin:
                display.lcd_display_string(str(control_local.finalPin) + "       ", 2)
                display.lcd_display_string("Correct Pin", 1)
                sleep(0.8)
                countDown()
                sleep(0.5)
                display.lcd_display_string("                 ", 2)
                display.lcd_display_string("System Armed      ", 1)
                GPIO.output(greenLED, GPIO.HIGH)
                if motionD() == "Intruder alert!!!":
                    display.lcd_display_string("                ", 2)
                    display.lcd_display_string("Motion Detected      ", 1)
                    sleep(5)
                    GPIO.output(buzzer, GPIO.HIGH)
                    firebaseDB()
                    emailNotify()
                    smsNotify()
                    
            elif control_local.finalPin == armPin:
                GPIO.output(greenLED, GPIO.LOW)
                display.lcd_display_string("                ", 2)
                display.lcd_display_string("System Disarmed      ", 1)
                GPIO.output(buzzer, GPIO.LOW)
                smsNotifyDisarm()
             
            elif control_local.finalPin != validPin or control_local.finalPin != armPin:
                display.lcd_display_string("incorrect Pin", 1)
                display.lcd_display_string("attempts left: " + str(incorrectPin), 2)
                incorrectPin = incorrectPin - 1 
                
                if incorrectPin < 0:
                    print("Buzzer on")
                    GPIO.output(buzzer, GPIO.HIGH)
                    incorrectPin = 3
                               
            digitCount = 0


def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(greenLED, GPIO.OUT)
    GPIO.setup(redLED, GPIO.OUT)
    GPIO.setup(orangeLED, GPIO.OUT)
    GPIO.setup(buzzer, GPIO.OUT)

def alarmStatus():
    setupGPIO()
    alarmState = GPIO.input(greenLED)
    date = datetime.now().strftime('%a %d-%m-%Y %H:%M:%S')
    
    if alarmState == True:
        dat = date
        LEDs = "Armed" + " at: " + str(dat)
        
    else:
        dat = date
        LEDs = "Disarmed" + " at: " + str(dat)
        
    return LEDs

def motionStatus():
    setupGPIO()
    #Motion status on web app
    updateWeb = "Motion Status: Undetected"
    motionState = GPIO.input(buzzer)
    
    if motionState == True:
        updateWeb = "Motion Status: Detected"
    else:
        updateWEb = "Motion Status: Undetected"
        
    return updateWeb

def motionD():
    sleep(4)
    if pir.wait_for_motion():
        Motion = "Intruder alert!!!"
        GPIO.output(orangeLED, GPIO.HIGH)
        sleep(1)
        GPIO.output(orangeLED, GPIO.LOW)
        sleep(1)
        
    return Motion

def onStatus():
    setupGPIO()
    while True:
        GPIO.output(redLED, GPIO.HIGH)
        sleep(0.5)
        GPIO.output(redLED, GPIO.LOW)
        sleep(0.5)
        
def beep():
    setupGPIO()
    while True:
        GPIO.output(buzzer, GPIO.HIGH)
        sleep(0.5)
        GPIO.output(buzzer, GPIO.LOW)
        sleep(0.5)
        
def printTemp():
    cpu = CPUTemperature()
    tempS = str(cpu.temperature)
    decTemp = "CPU Temperature: {}'C".format(tempS[:4])
    
    return decTemp
        
def firebaseDB():
    
    global count
    global count3
    
    config = {
      "apiKey": "AIzaSyDjrWGNvhM14JQduPjfUj7LhXrqfugzmjk",
      "authDomain": "smart-security-system-5235a.firebaseapp.com",
      "databaseURL": "https://smart-security-system-5235a-default-rtdb.firebaseio.com",
      "projectId": "smart-security-system-5235a",
      "storageBucket": "smart-security-system-5235a.appspot.com",
      "messagingSenderId": "366664596426",
      "appId": "1:366664596426:web:c9655c3020e8c1a3e2ed33",
      "measurementId": "G-P00QDZHT0D"
    };

    firebase = pyrebase.initialize_app(config)
    storage = firebase.storage()
    database = firebase.database()
    
    #Information data for DB
    a = motionD()
    b = datetime.now().strftime('%a %d-%m-%Y %H.%M')
    c = alarmStatus()

    database.child("Case number: " + str(count))
    count = count + 1
    data = {"System status": c,"Status": a, "Time Detected":b}
    database.set(data)
    
    #Storing alert videos on the cloud
    d = datetime.now().strftime('%a %d-%m-%Y')
    path_on_cloud = str(d) + " Videos/" +str(count3) + ".video_alert.mp4"
    count3 = count3 + 1
    path_local = '/home/pi/Desktop/' + str(count2) + 'Alert_video.mp4'
    storage.child(path_on_cloud).put(path_local)
    print("Video attached")

def viewDB():
    
    global count
    
    config = {
      "apiKey": "AIzaSyDjrWGNvhM14JQduPjfUj7LhXrqfugzmjk",
      "authDomain": "smart-security-system-5235a.firebaseapp.com",
      "databaseURL": "https://smart-security-system-5235a-default-rtdb.firebaseio.com",
      "projectId": "smart-security-system-5235a",
      "storageBucket": "smart-security-system-5235a.appspot.com",
      "messagingSenderId": "366664596426",
      "appId": "1:366664596426:web:c9655c3020e8c1a3e2ed33",
      "measurementId": "G-P00QDZHT0D"
    };

    firebase = pyrebase.initialize_app(config)
    storage = firebase.storage()
    database = firebase.database()
    
    viewDB.out1 = database.child("Case number: " + str(1)).get().val()
    viewDB.out2 = database.child("Case number: " + str(2)).get().val()
    viewDB.out3 = database.child("Case number: " + str(3)).get().val()
    
class MyServer(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        post_data = post_data.split("=")[1]
        
        setupGPIO()
        
        if post_data == 'Arm':
            display.lcd_display_string("System Arming in ", 1)
            display.lcd_display_string("5 seconds", 2)
            sleep(4)
            display.lcd_display_string("System Armed       ", 1)
            display.lcd_display_string("                  ", 2)
            GPIO.output(greenLED, GPIO.HIGH)
            if motionD() == "Intruder alert!!!":
                display.lcd_display_string("                ", 2)
                display.lcd_display_string("Motion Detected      ", 1)
                sleep(5)
                GPIO.output(buzzer, GPIO.HIGH)
                firebaseDB()
                emailNotify()
                smsNotify()
           
        elif post_data == 'Disarm':
            GPIO.output(greenLED, GPIO.LOW)
            display.lcd_display_string("System Disarmed", 1)
            display.lcd_display_string("                  ", 2)
            GPIO.output(buzzer, GPIO.LOW)
            smsNotifyDisarm()

        self._redirect('/')  # Redirect back to the root url
        
        return post_data
        
        
    def do_GET(self):
        html = '''
           <html>
           <body 
               style="width:960px; margin: 10px auto; background-color: #f2f3f4">
               <h1 style="text-shadow: 6px 6px 9px gray; text-align: center; font-size: 70px; color: black;">SMART</h1>
               <h1 style="text-shadow: 6px 6px 9px gray; text-align: center; font-size: 70px; color: black;">SECURITY SYSTEM</h1>
               <p style="text-align: center;text-shadow: 4px 6px 8px grey; font-size: 26px; color: black">A New Freedom of Security</p>
               <br>
               <br>
               <h2 style="text-align: center; font-size: 20px; background-color: gray; color: white; text-shadow: 2px 4px 6px green;">SYSTEM STATUS:</h2>
               <p style="text-align: center; font-size: 15px; color: black">{}</p>
           </body>
           </html>
        '''
        
        motionStat = '''
           <html>
           <body 
                style="width:960px; margin: 20px auto; background-color: #f2f3f4">
                <p style="text-align: center; font-size: 15px; color: black">{}</p>
           </body>
           </html>
        '''
        
        htmlBtn = '''
           <html>
           <body
               style="width:960px; margin: 20px auto; background-color: #f2f3f4">
               <br><br><br><br>
               <form action="/" method="POST">
                   <input type="submit" name="submit" value="Arm" style="width: 300px; height: 300px; background-color: #32cd32; color: white; font-size: 30px; font-weight: Bold; margin-left: 80px; border-radius: 250px; border: 10px solid #696969">
                   <input type="submit" name="submit" value="Disarm" style="width: 300px; height: 300px; background-color: #ff0000; color: white; font-size: 30px; font-weight: Bold; margin-left: 220px; border-radius: 250px; border: 10px solid #696969">
               </form>
               <br><br><br><br>
               <button style=" width: 450px; height: 80px; margin-left: 250px; background: gray" border-radius: 1px; border: 5px solid white;"><a style="text-decoration: none; color: white; font-size: 30px; ont-weight: Bold;" href="https://smart-security-system-5235a-default-rtdb.firebaseio.com/">View Database</a></button>
               <br><br><br>
               <button style=" width: 450px; height: 80px; margin-left: 250px; background: gray" border-radius: 1px; border: 5px solid white;"><a style="text-decoration: none; color: white; font-size: 30px; ont-weight: Bold;" href="https://speedtest-3d73f.web.app">Check Connection Speed</a></button>
               <br><br><br>
               <button style=" width: 450px; height: 80px; margin-left: 250px; background: gray" border-radius: 1px; border: 5px solid white;"><a style="text-decoration: none; color: white; font-size: 30px; ont-weight: Bold;" href="https://mail.google.com/mail/u/0/#inbox">Access Emails</a></button>
               <br><br><br><br><br><br><br>
           </body>
           </body>
           </html>
        '''
        
        support = '''
           <html>
           <body>
           <div style="background-color: #c0c0c0; text-align: center;">
               <h1 style="color: white;">Help:</h1>
               <a href="https://smart-security-system-manual.web.app" style="color: black;text-align: right">How to use the system</a>
               <h1 style="font-weight: bold; color: white;">Technical Support:</h1>
               <a href="mailto: kamogelotd98@gmail.com" style="color:black;">kamogelotd98@gmail.com</a>
               <h3 style="color: black;><b style= "color: black;">T</b>: +27 76 108 3017</h3>
               <a style="text-decration: none; color: black;" href="https://wa.me/<+27761083017>">WhatsApp Support</a>
           </div>
           </body>
           </html>
        '''
        
        tem = '''
           <html>
           <body 
                style="width:960px; margin: 20px auto; background-color: #f2f3f4">
                <p style="text-align: center; font-size: 15px; color: black">{}</p>
           </body>
           </html>
        '''

        data1 = '''
           <html>
           <body
                style="width:960px; margin: 20px auto; background-color: #f2f3f4">
                <h2 style="text-align: center; font-size: 20px; background-color: gray; color: white; text-shadow: 2px 4px 6px red;">RECENT INCIDENTS:</h2>
                <p style="text-align: center; font-size: 10px; color: black;">(Press the buttons below to view data)</p>
                <button ONCLICK="ShowAndHide()" style=" width: 190px; height: 60px; margin-left: 400px; background: gray; color:white; font-size: 20px;"><b>Case Number: 1</b></button>
                <p ID="SectionName" style="text-align: center; font-size: 15px; color: black; display:none;">{}</p>
                <hr>
                <script>
                    function ShowAndHide(){{
                        var x = document.getElementById('SectionName');
                        if (x.style.display == 'none')
                        {{
                            x.style.display = 'block';
                        }}
                        else
                        {{
                            x.style.display = 'none';
                        }}
                    }}
                        
                </script>
           </body>
           </html>
        '''
        
        data2 = '''
           <html>
           <body
                style="width:960px; margin: 20px auto; background-color: #f2f3f4">
                <button ONCLICK="ShowAndHides()" style=" width: 190px; height: 60px; margin-left: 400px; background: gray; color:white; font-size: 20px"><b>Case Number: 2</b></button>
                <p ID="SectionNames" style="text-align: center; font-size: 15px; color: black; display:none;">{}</p>
                <hr>
                <script>
                    function ShowAndHides(){{
                        var x = document.getElementById('SectionNames');
                        if (x.style.display == 'none')
                        {{
                            x.style.display = 'block';
                        }}
                        else
                        {{
                            x.style.display = 'none';
                        }}
                    }}
                        
                </script>
           </body>
           </html>
        '''
        
        data3 = '''
           <html>
           <body
                style="width:960px; margin: 20px auto; background-color: #f2f3f4">
                <button ONCLICK="ShowsAndHide()" style=" width: 190px; height: 60px; margin-left: 400px; background: gray; color:white; font-size:20px;"><b>Case Number: 3</b></button>
                <p ID="SectionsName" style="text-align: center; font-size: 15px; color: black; display:none;">{}</p>
                <hr>
                <script>
                    function ShowsAndHide(){{
                        var x = document.getElementById('SectionsName');
                        if (x.style.display == 'none')
                        {{
                            x.style.display = 'block';
                        }}
                        else
                        {{
                            x.style.display = 'none';
                        }}
                    }}
                        
                </script>
           </body>
           </html>
        '''
        
        update = alarmStatus()
        updateM = motionStatus()
        temp = printTemp()
        viewDB()
        setupGPIO()
                    
        self.do_HEAD()
        self.wfile.write(html.format(update).encode("utf-8"))
        self.wfile.write(motionStat.format(updateM).encode("utf-8"))
        self.wfile.write(tem.format(temp).encode("utf-8"))
        self.wfile.write(htmlBtn.format(" ").encode("utf-8"))
        self.wfile.write(data1.format(viewDB.out1).encode("utf-8"))
        self.wfile.write(data2.format(viewDB.out2).encode("utf-8"))
        self.wfile.write(data3.format(viewDB.out3).encode("utf-8"))
        self.wfile.write(support.format(" ").encode("utf-8"))

# # # # # Main FUNCTION# # # # #
if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))
    Thread(target = control_local).start()
    Thread(target = onStatus).start()
    
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()