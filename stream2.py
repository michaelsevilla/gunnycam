#!/usr/bin/python3
#
# feature: multiple streaming clients
# feature: turn camera off if no streamers
# feature: wifi-enabled light turns on when recording
#
# TODO: cleanup and refactor for clarity
# TODO: make sure install and setup works
# TODO: submodule linking
#
# Web streaming example
#
# Source code from the official PiCamera package
# picam: http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
# alexa: https://github.com/gravesjohnr/AlexaNotificationCurl

import io
import time
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import subprocess

PAGE="""\
<html>
<head>
<title>Gunny Cam</title>
</head>
<body>
<center><h1>Welcome to Gunny Cam</h1></center>
<center>What is he up to? Take a look below. :)</center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        # why doesn't output need to be globalized?
        global camera 
        global nstream

        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()

            nstream += 1
            log.warning(
                'Added streaming client %s, number of streamers: %d',
                self.client_address, nstream)

            if camera == None:
                log.info("... starting camera")
                camera = picamera.PiCamera(resolution='640x480', framerate=24)
                camera.rotation = 90

                log.info("... start recording")
                camera.start_recording(output, format='mjpeg')

                log.info('... minor sleep as the camera starts')
                time.sleep(1)

                log.info('... turning the recording light on')
                alexash = "/home/pi/Code/AlexaNotificationCurl/alexa.sh"
                command = ["/bin/bash", alexash, "turn the rock on"]
                with open("./alexa.out", 'w') as o:
                  with open("./alexa.err", 'w') as e:
                    subprocess.Popen(command, stdout=o, stderr=e)

            log.info("... writing stream out")
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    log.info("... actively writing")
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                nstream -= 1
                log.warning(
		    'Removed streaming client %s: %s, number of streams: %d',
                    self.client_address, str(e), nstream)

                if nstream == 0:
                    camera.stop_recording()
                    camera.close()
                    camera = None
                    log.warning('Camera is off, because %d streamers', nstream)

                    log.info('... turning the recording light on')
                    alexash = "/home/pi/Code/AlexaNotificationCurl/alexa.sh"
                    command = ["/bin/bash", alexash, "turn the rock off"]
                    with open("./alexa.out", 'w') as o:
                      with open("./alexa.err", 'w') as e:
                        subprocess.Popen(command, stdout=o, stderr=e)
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

########
# main #
########

# global variables
address = ('', 3333)
loglevl = logging.WARNING

# https://docs.python.org/2/library/logging.html#logging.Logger.debug
logging.basicConfig(format='%(asctime)-15s %(message)s')
log = logging.getLogger('htmlserver')
log.setLevel(loglevl)

log.info('... setting streaming output')
output = StreamingOutput()

log.warning('... setting up camera address=%s', address)
server = StreamingServer(address, StreamingHandler)
camera = None
nstream = 0

log.info('... serving website')
try:
    server.serve_forever()
finally:
    print("ouch. I've been killed!")
