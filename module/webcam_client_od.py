# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A usb camera client 
  - captures image from first USB cam
  - sends jpeg to inference API via rest call.
  - print predicted class
  - shows image on desktop with captions
"""
from __future__ import print_function
import base64
import requests
import cv2
import sys
import time
import argparse
#from PIL import Image
import io
# The server URL specifies the endpoint of your server running the ResNet
# model with the name "resnet" and using the predict interface.
#SERVER_URL = 'http://localhost:8501/v1/models/resnet:predict'
#SERVER_URL = 'http://localhost:4000/v1/vision/detection'
SERVER_URL = 'http://10.152.183.45:5000/v1/vision/detection'
UPLOAD_URL = 'https://europe-west3-edgeml-demo.cloudfunctions.net/mledge-image-gateway-1/images/'
CONFIDENCE_THRESHOLD = 0.20
BOX_COLOR  = [100, 250, 100]
BOX_THICKNESS = 2
FONT_COLOR = [100, 250, 100]
FONT_THICKNESS = 1
FONT_RATIO = 0.6
def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
def main():
  parser = argparse.ArgumentParser(description="Camera module captures image from USB camera and send picture to object detection inference API.")
  parser.add_argument("--frame", "-f", type=str2bool, help="Show captioned images in a window", default=True)
  parser.add_argument("--log", "-l", type=str2bool, help="Show text logs of inference results", default=True)
  parser.add_argument("--camera", "-c", type=int, help="Camera number", default=0)
  parser.add_argument("--inferenceurl", "-iu",  help="URL of model serving API", default=SERVER_URL)
  parser.add_argument("--uploadurl", "-up",  help="URL of image upload API", default=UPLOAD_URL)
  parser.add_argument("--upload", "-u", type=str2bool, help="Upload prepared image", default=False)
  parser.add_argument("--channel", "-ch",  help="Channel name for upload", default="demo1")
  parser.add_argument("--interval", "-i", type=int, help="Interval between two model serving requests in milliseconds", default=100)
  parser.add_argument("--counter", "-o", type=str2bool, help="Show object counter roster", default=True)
  # Note: wrong aspect ratio or high resolution has effect on prediction!
  parser.add_argument("--width", "-wi", type=int, help="Camera X resolution", default=800)
  parser.add_argument("--height", "-he", type=int, help="Camera Y resolution", default=600)
  args = parser.parse_args()
  # Capture the image
  video_capture = cv2.VideoCapture(args.camera)
  video_capture.set(3, args.width)
  video_capture.set(4, args.height)
  if not video_capture.isOpened():
    raise IOError("Cannot open usb camera " + args.camera)
  print("Usb camera opened...")
  if (args.frame):
    # window on the desktop
    cv2.namedWindow("frame")
  while True:
    try:
      # Capture frame-by-frame
      ret, frame = video_capture.read()
      if not ret:
        print ("Image capture error")
        key = cv2.waitKey(args.interval)
        continue
      # Extracted for drawing object
      # windowWidth=frame.shape[1]
      # windowHeight=frame.shape[0]
      cv2_im = frame
      res, jpg = cv2.imencode('.jpg', cv2_im)
      # Send image to prediction
      response = requests.post(args.inferenceurl, files={'image': jpg.tobytes()}, timeout=0.1)
      response.raise_for_status()
      if args.log:
        print('latency: {}ms'.format(round(response.elapsed.total_seconds() * 1000)))
      labelcounter = {}
      for prediction in response.json()['predictions']:
        label = '%s' % (prediction['label'])
        confidence = prediction['confidence']
        if label == 'unknown' or confidence < CONFIDENCE_THRESHOLD:
            continue
        labelcounter[label] = labelcounter[label] + 1 if label in labelcounter else 1
        if args.log:
          print('  conf: {}%, Label: {}'.format(round(confidence * 100), label))
        y_min = prediction['y_min']
        x_min = prediction['x_min']
        x_max = prediction['x_max']
        y_max = prediction['y_max']
        cv2.rectangle(img=cv2_im, pt1=(x_min, y_min), pt2=(x_max, y_max), color=BOX_COLOR, thickness=BOX_THICKNESS)
        x = x_min + (x_max - x_min)//2 - int(len(label)/2*17*FONT_RATIO)
        if y_max + 20 < frame.shape[0]:
           # below
           y = y_max + int(30 * FONT_RATIO)
           cv2_im = cv2.putText(cv2_im, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, FONT_RATIO, FONT_COLOR, FONT_THICKNESS)
        else:
           # in frame
           y = y_max - int(15 * FONT_RATIO)
           cv2_im = cv2.putText(cv2_im, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, FONT_RATIO, FONT_COLOR, FONT_THICKNESS)
      if args.counter:
        alpha = 0.3  # Transparency factor.
        overlay = cv2_im.copy()
        #Backgound layer for text
        #cv2.rectangle(img=cv2_im, pt1=(0,0), pt2=(120,windowHeight), color=[100, 100, 100], thickness=-1)
        cv2_im = cv2.addWeighted(overlay, alpha, cv2_im, 1 - alpha, 0)
        label_y = 20
        for label, count in labelcounter.items():
          labelout="{0:3d}*{1}".format(count, label)
          cv2_im = cv2.putText(cv2_im, labelout, (3, label_y), cv2.FONT_HERSHEY_SIMPLEX, FONT_RATIO, (0,0,255), 1)
          label_y += 20
      # Upload to http sink
      if args.upload:
        url = args.uploadurl+args.channel
        res2, jpg2 = cv2.imencode('.jpg', cv2_im)
        response = requests.post(url, files=dict(image= jpg2.tobytes()))
        response.raise_for_status()
      # Update demo window on the desktop
      if args.frame:
        cv2.imshow('frame', cv2_im)
    except requests.exceptions.ConnectionError:
      print("Model server API unavailable")
    except:
      print("Unexpected error:", sys.exc_info())
    key = cv2.waitKey(args.interval)
  video_capture.release()
  cv2.destroyAllWindows()
if __name__ == '__main__':
  main()