from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from data_capture import DataCapture
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
    filename=f'{__name__}.log', level=logging.INFO, format=LOGFORMAT)

frameUpdateWaitSeconds = 5
frameUpdateWaitHasPassed = None

inference_service_url = f"http://{os.environ['MLEDGE_DEPLOYMENT_SERVICE_HOST']}:{os.environ['MLEDGE_DEPLOYMENT_SERVICE_PORT']}/v1/vision/detection"

vs = VideoStream(src=0).start()
time.sleep(2.0)
dataCapture = None

@app.route("/")
def index():
	# return the rendered template
	return render_template("index.html")

@app.route("/video_feed")
def video_feed():
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route("/store_data", methods=['POST'])
def store_data():
	global dataCapture
	threshold = request.form['threshold']
	try:
		if dataCapture is None:
			dataCapture = DataCapture(threshold, getFramBytes, generateInferenceResultMessage)
		dataCapture.setThreshold(threshold)
		dataCapture.toggleEnabled()
	except ValueError as ve:
		print(ve)
	return jsonify({'threshold': dataCapture.getThreshold(), 'enabled': dataCapture.isEnabled()})

def classify():
    global vs, outputFrame, lock, inference_service_url, dataCapture
    
    while True:
        if outputFrame is None or frameUpdateWaitHasPassed():
            frame = vs.read()
            frame = imutils.resize(frame, width=800)
            
            retval, buffer = cv2.imencode('.jpg', frame)
            
            headers = {'accept': 'application/json'}
            res = requests.post(inference_service_url, files={'image': buffer.tobytes()}, headers=headers)
            
            resobj = res.json()
            
            if resobj['success']:
                start_point = (resobj['predictions'][0]['x_min'], resobj['predictions'][0]['y_min'])
                end_point = (resobj['predictions'][0]['x_max'], resobj['predictions'][0]['y_max'])

                frame = cv2.rectangle(frame, start_point, end_point, (255, 0, 0), 2) 

                cv2.putText(frame, f"{resobj['predictions'][0]['label']}: {resobj['predictions'][0]['confidence']}",
                (10, frame.shape[0] - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if dataCapture and dataCapture.isEligibleForCapture(resobj['predictions'][0]['confidence']):
                    captureEntry = {'frame': frame.copy(), 'predictions': resobj['predictions'], 'ts':time.time()}
                    dataCapture.put(captureEntry)
            
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

def getFramBytes(task):
	(flag, buffer) = cv2.imencode(".jpg", task['frame'])
	return buffer.tobytes()

def generateInferenceResultMessage(task, fileUrl):
	return {'predictions': task['predictions'], 'ts': task['ts'], 'fileUrl': fileUrl}

def generateTimePeriodCheckFunction(periodLength):
	periodStart = time.time()
	def periodHasPassed():
		nonlocal periodStart
		now = time.time()
		timePassed = now - periodStart
		if timePassed >= periodLength:
			periodStart = now
			return True
		return False
	return periodHasPassed

def main():
    global frameUpdateWaitHasPassed
    parser = argparse.ArgumentParser(
        description="Flask app inference UI"
    )
    parser.add_argument("--port", default=8502, type=int, help="port number")
    args = parser.parse_args()
    frameUpdateWaitHasPassed = generateTimePeriodCheckFunction(frameUpdateWaitSeconds)
    t = threading.Thread(target=classify)
    t.daemon = True
    t.start()
    # start the flask app
    app.run(host="0.0.0.0", port=args.port, threaded=True, use_reloader=False)


if __name__ == '__main__':
    main()
# release the video stream pointer
vs.stop()