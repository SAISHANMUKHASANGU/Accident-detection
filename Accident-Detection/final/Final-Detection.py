import cv2
from detection import AccidentDetectionModel
import numpy as np
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, Response, request, redirect, url_for, make_response

import time 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage



import requests

def get_location():
    latitude=0
    longitude=0
    try:

        import subprocess as sp
        import re
        import time

        wt = 5 # Wait time -- I purposefully make it wait before the shell command
        accuracy = 3 #Starting desired accuracy is fine and builds at x1.5 per loop

        time.sleep(wt)
        pshellcomm = ['powershell']
        pshellcomm.append('add-type -assemblyname system.device; '\
                        '$loc = new-object system.device.location.geocoordinatewatcher;'\
                        '$loc.start(); '\
                        'while(($loc.status -ne "Ready") -and ($loc.permission -ne "Denied")) '\
                        '{start-sleep -milliseconds 100}; '\
                        '$acc = %d; '\
                        'while($loc.position.location.horizontalaccuracy -gt $acc) '\
                        '{start-sleep -milliseconds 100; $acc = [math]::Round($acc*1.5)}; '\
                        '$loc.position.location.latitude; '\
                        '$loc.position.location.longitude; '\
                        '$loc.position.location.horizontalaccuracy; '\
                        '$loc.stop()' %(accuracy))



        p = sp.Popen(pshellcomm, stdin = sp.PIPE, stdout = sp.PIPE, stderr = sp.STDOUT, text=True)
        (out, err) = p.communicate()
        out = re.split('\n', out)

        lat = float(out[0])
        long = float(out[1])
        radius = int(out[2])

        print(lat, long, radius)
        latitude = lat
        longitude = long 
            
    except Exception as e:
        print("Error:", e)
    return latitude, longitude
lat,lon=get_location()




def send_email(subject, message, sender_email, receiver_email, password, attachment_path):
    # Create a MIMEMultipart object
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_email)

    # Attach the body of the email to the MIME message
    msg.attach(MIMEText(message, 'plain'))

    # Open the file to be sent as an attachment
    try:
        with open(attachment_path, 'rb') as attachment:
            img = MIMEImage(attachment.read())
            # Add a header to manage file names
            img.add_header('Content-Disposition', 'attachment', filename='detectedframe.jpg')
            msg.attach(img)
    except Exception as e:
        print(f"Failed to attach image: {e}")

    # Send the email via Gmail's SMTP server, or use another server as needed
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)  # Use send_message instead of sendmail
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Example of calling send_email'vaishnavibarla2003@gmail.com', '20981a4248@raghuenggcollege.in', '20981a4261@raghuenggcollege.in'
sender = 'sangusaishanmukha@gmail.com'
receiver = [ 'sangusaishanmukha@gmail.com' '20981a4248@raghuenggcollege.in']
subject = 'Accident Detection'
message = 'An accident has been identified based on the provided data feed.'  +"Current Cooridinates[" +str(lat)+","  +str(lon)+"]"
attachment_path = 'detectedframe.jpg'
password = 'cmmzyhcnqtbgabma'

model = AccidentDetectionModel(r"C:\Users\ASUS\Downloads\Accident-Detection\final\model (3).json", r"C:\Users\ASUS\Downloads\Accident-Detection\final\model_weights (3).h5")
font = cv2.FONT_HERSHEY_SIMPLEX

import cv2

video = cv2.VideoCapture(0)

while True:
    ret, frame = video.read()
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    roi = cv2.resize(gray_frame, (250, 250))
    pred, prob = model.predict_accident(roi[np.newaxis, :, :])
    print(pred)

    if pred == "Accident":
        prob = round(prob[0][0]*100, 2)
        if prob > 97:
            
            import winsound

            # Set the frequency (in Hertz) and duration (in milliseconds)
            frequency = 2500
            duration = 1000  # 1 second

            # Make the computer beep
            winsound.Beep(frequency, duration)

            print("accident")

            cv2.imwrite('detectedframe.jpg', frame)

            try:

                send_email(subject, message, sender, receiver, password, attachment_path)
                time.sleep(1)
            except Exception as exp:
                print("oops ", exp)
                pass 


        cv2.rectangle(frame, (0, 0), (280, 40), (0, 0, 0), -1)
        cv2.putText(frame, pred+" "+str(prob), (20, 30), font, 1, (255, 255, 0), 2)
    else:
        cv2.rectangle(frame, (0, 0), (280, 40), (0, 0, 0), -1)
        cv2.putText(frame, "No Accident", (20, 30), font, 1, (255, 255, 0), 2)


    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
