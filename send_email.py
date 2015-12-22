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
import syslog



BASE_URL = 'https:// WEB PAGE IP ADDRESS HERE :8090'

#debug = True
debug = False

disable_transcription = False
#disable_transcription = True

send_from = ' FROM EMAIL ADDRESS HERE '
send_to = ' TO EMAIL ADDRESS HERE '

syslog.syslog('Processing started')

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

syslog.syslog("Pieces length: " + str(len(pieces)))

callee = pieces[0]
syslog.syslog("CallEE: " + callee)
caller = pieces[1]
syslog.syslog("CallER: " + caller)
timestamp = pieces[2]
syslog.syslog("TIMESTAMP: " + timestamp)
callmebackgsmno = ""

if (len(pieces) >= 4):
    callmebackgsmno = pieces[3]

syslog.syslog("Callmeback GSM no: " + callmebackgsmno)

extracted_audio_file_base = callee + '_' + caller + '_' + timestamp
command_to_execute = 'ffmpeg -i ' + video_file + ' -vn -acodec copy ' + extracted_audio_file_base + '.ogg'
print("Preparing to run command: " + command_to_execute)
syslog.syslog("Preparing to run command: " + command_to_execute)
if not debug:
    subprocess.call(command_to_execute, shell=True)
print("Extracted!")
syslog.syslog("Extracted!")

command_to_execute = 'ffmpeg -i ' + extracted_audio_file_base + '.ogg ' + extracted_audio_file_base + '.wav'
print("Preparing to run command: " + command_to_execute)
syslog.syslog("Preparing to run command: " + command_to_execute)
if not debug:
    subprocess.call(command_to_execute, shell=True)

extracted_audio_file = extracted_audio_file_base + '.wav'

print("Extracted: " + extracted_audio_file)
files = [extracted_audio_file]

print("Transcribing..........")
syslog.syslog("Transcribing..........")

transcription = ""
if (not disable_transcription):
    #transcription = transcript("man1_nb.wav")
    transcription = transcript(extracted_audio_file)
syslog.syslog("Transcription: " + transcription)

video_file = callee + '_' + caller + '_' + timestamp
if (callmebackgsmno):
    video_file += '_' + callmebackgsmno
video_file += '.webm'

video_url = BASE_URL + '/play.html?file_uri=' + video_file

transcription_sentence = ""
if (transcription):
    transcription_sentence = "It says: <br>" + transcription + "<br>"

callmeback_sentence = ""
if (callmebackgsmno):
    callmeback_url = BASE_URL + '/call.html?number=' + callmebackgsmno + '&name=' + caller
    callmeback_sentence = "<a href='" + callmeback_url + "'>Please call me back at +" + callmebackgsmno + "</a><br>"

body = """ \
<html>
  <head></head>
  <body>
    <p>Hi %s!<br>
       Here is a <a href="%s">videomessage</a> from %s.<br>
       %s <br>
       %s <br>
       Yours,<br>
       The Cool Voicemail<br> 
    </p>
  </body>
</html>
""" % (callee, video_url, caller, transcription_sentence, callmeback_sentence)

subject = 'Videomessage from ' + caller

print "sending email now... with body:         " + body
syslog.syslog("sending email now... with body:         " + body)
if not debug:
    send_mail(send_from, send_to, subject, body, files)

print("DONE.")
