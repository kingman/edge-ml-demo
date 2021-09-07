# Start the server:
# 	python3 coral-app.py
# Submit a request via cURL:
# 	curl -X POST -F image=@face.jpg 'http://localhost:5000/v1/vision/detection'

# coding=utf8

from edgetpu.classification.engine import ClassificationEngine
import argparse
from PIL import Image
from core import CloudIot
import flask
import logging
import io
import numpy as np
import sys
import glob
import zipfile

app = flask.Flask(__name__)

LOGFORMAT = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
logging.basicConfig(filename='coral.log', level=logging.DEBUG, format=LOGFORMAT)

engine = None
labels = None
cloud_iot = None
report_to_cloud = False

ROOT_URL = "/v1/vision/detection"

def get_input_tensor(engine, image):
  _, height, width, _ = engine.get_input_tensor_shape()
  return np.asarray(image.resize((width, height), Image.NEAREST)).flatten()

@app.route("/")
def info():
    info_str = "Flask app exposing tensorflow lite model {}".format(MODEL)
    return info_str


@app.route(ROOT_URL, methods=["POST"])
def predict():
    data = {"success": False}

    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image_file = flask.request.files["image"]
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes))
            # Debug only:
            #image.show()

            # data["success"] = True
            # return flask.jsonify(data)

            input = get_input_tensor(engine, image)
            # Run inference.
            predictions = engine.ClassifyWithInputTensor(input, top_k=5)

            if predictions:
                data["success"] = True
                preds = []
                for index, score in predictions:
                    preds.append(
                        {
                            "score": float(score),
                            "label": labels.get(index,index)
                        }
                    )
                data["predictions"] = preds

    # return the data dictionary as a JSON response
    if report_to_cloud:
        cloud_iot.publish_message(data)
    return flask.jsonify(data)

def load_labels(path, encoding='utf-8'):
    """Loads labels from file (with or without index numbers).
        Args:
        path: path to label file.
        encoding: label file encoding.
        Returns:
            Dictionary mapping indices to labels.
    """
    with open(path, 'r', encoding=encoding) as f:
        lines = f.readlines()

        if not lines:
            return {}

        if lines[0].split(' ', maxsplit=1)[0].isdigit():
            pairs = [line.split(' ', maxsplit=1) for line in lines]
            return {int(index): label.strip() for index, label in pairs}
        else:
            return {index: line.strip() for index, line in enumerate(lines)}

def init_mqtt_client():
    global cloud_iot
    cloud_iot = CloudIot()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing coral USB stick")
    parser.add_argument(
        "--models_directory",
        default="models/",
        help="the directory containing the model files",
    )
    parser.add_argument(
        "--model",
        default="model.tflite",
        help="model file",
    )
    parser.add_argument(
        "--report_to_cloud",
        default=True,
        help="send inference result to cloud backend",
    )
    parser.add_argument("--port", default=8501, type=int, help="port number")
    args = parser.parse_args()

    global MODEL
    model_pattern = args.models_directory + "*.tflite"
    model_list = glob.glob(model_pattern)
    if len(model_list) == 0:
        print("\n Model not found with pattern {}".format(model_pattern))
        sys.exit("Model not found with pattern {}".format(model_pattern))
    
    label_pattern = args.models_directory + "*.txt"
    label_list = glob.glob(label_pattern)
    if len(label_list) == 0:
        with zipfile.ZipFile(model_list[0], 'r') as zip_ref:
            zip_ref.extractall(args.models_directory)
        label_list = glob.glob(label_pattern)

    MODEL = model_list[0]
    model_file = model_list[0]
    labels = load_labels(label_list[0]) if len(label_list) > 0 else {}

    engine = ClassificationEngine(model_file)
    print("\n Loaded engine with model : {}".format(model_file))

    if args.report_to_cloud: {
        init_mqtt_client()
        report_to_cloud = True
    }
     

    app.run(host="0.0.0.0", port=args.port)