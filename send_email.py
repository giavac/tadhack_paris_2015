#!/usr/bin/env python

import speech_recognition as sr

import sys
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

import subprocess
from urllib import quote

def send_mail(send_from, send_to, subject, text, files=None, server="127.0.0.1"):
    assert isinstance(send_to, list)
    print("Subject: " + subject)

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg.attach(MIMEText(text, 'html'))

    for f in files or []:
        with open(f, "rb") as fil:
            msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition='attachment; filename="%s"' % basename(f),
                Name=basename(f)
            ))

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

#########################################
def transcript(WAV_FILE):
    r = sr.Recognizer()
    with sr.WavFile(WAV_FILE) as source:
        audio = r.record(source) # read the entire WAV file

    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return ""
##############################################

video_file = sys.argv[1]

print("Processing video file: " + video_file)

#/tmp/kurento/alice_bob_1449919920.webm

tmp = video_file[13:-5]
pieces = tmp.split('_')
#print pieces


callee = pieces[0]
caller = pieces[1]
timestamp = pieces[2]


#debug = True
debug = False



send_from = 'noreply@coolvoicemail.io'
send_to = ['XXXXX']


extracted_audio_file_base = callee + '_' + caller + '_' + timestamp
command_to_execute = 'ffmpeg -i ' + video_file + ' -vn -acodec copy ' + extracted_audio_file_base + '.ogg'
print("Preparing to run command: " + command_to_execute)
if not debug:
    subprocess.call(command_to_execute, shell=True)
print("Extracted!")

command_to_execute = 'ffmpeg -i ' + extracted_audio_file_base + '.ogg ' + extracted_audio_file_base + '.wav'
print("Preparing to run command: " + command_to_execute)
if not debug:
    subprocess.call(command_to_execute, shell=True)

extracted_audio_file = extracted_audio_file_base + '.wav'

print("Extracted: " + extracted_audio_file)
files = [extracted_audio_file]

print("Transcribing..........")
transcription = transcript(extracted_audio_file)
print("Transcription: " + transcription)



#video_url = 'https://127.0.0.1:8090/play.html?file_uri=' + video_file
#text = '<html>Hi ' + callee + ',<br><a href=https://127.0.0.1:8090/play.html?file_uri=' + video_file + '>This is your video message from ' + caller + '</a><br></html>'

text = '<html>This is the message from ' + caller + ':<br> ' + transcription + '<br></html>'

subject = 'Videomessage from ' + caller

print "sending email now... with text:         " + text
if not debug:
    send_mail(send_from, send_to, subject, text, files)

print("DONE.")
