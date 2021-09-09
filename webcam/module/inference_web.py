from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import logging
import threading
import argparse
import base64
import imutils
import time
import cv2
import requests
import os

outputFrame = None
lock = threading.Lock()

app = Flask(__name__)
LOGFORMAT = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
logging.basicConfig(
    filename=f'{__name__}.log', level=logging.DEBUG, format=LOGFORMAT)

vs = VideoStream(src=0).start()
time.sleep(2.0)

@app.route("/")
def index():
	# return the rendered template
	return render_template("index.html")

@app.route("/video_feed")
def video_feed():
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

def classify():
	global vs, outputFrame, lock

	while True:
		frame = vs.read()
		frame = imutils.resize(frame, width=800)
		
		retval, buffer = cv2.imencode('.jpg', frame)
		
		headers = {'accept': 'application/json'}
		res = requests.post(f"http://{os.environ['MLEDGE_DEPLOYMENT_SERVICE_HOST']}:{os.environ['MLEDGE_DEPLOYMENT_SERVICE_PORT']}/v1/vision/detection", files={'image': buffer.tobytes()}, headers=headers)
		
		resobj = res.json()
		
		if resobj['success']:
			cv2.putText(frame, f"{resobj['predictions'][0]['label']}: {resobj['predictions'][0]['score']}",
			(10, frame.shape[0] - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
		
		with lock:
			outputFrame = frame.copy()

def generate():

	global outputFrame, lock

	while True:
		with lock:
			if outputFrame is None:
				continue
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
			if not flag:
				continue
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')



def main():
    parser = argparse.ArgumentParser(
        description="Flask app inference UI"
    )
    parser.add_argument("--port", default=8502, type=int, help="port number")
    args = parser.parse_args()
    t = threading.Thread(target=classify)
    t.daemon = True
    t.start()
    # start the flask app
    app.run(host="0.0.0.0", port=args.port, threaded=True, use_reloader=False)


if __name__ == '__main__':
    main()
# release the video stream pointer
vs.stop()