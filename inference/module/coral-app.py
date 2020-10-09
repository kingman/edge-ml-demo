# Start the server:
# 	python3 coral-app.py
# Submit a request via cURL:
# 	curl -X POST -F image=@face.jpg 'http://localhost:5000/v1/vision/detection'
# coding=utf8
from edgetpu.detection.engine import DetectionEngine
import argparse
from PIL import Image
import flask
import logging
import io
import numpy as np
app = flask.Flask(__name__)
LOGFORMAT = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
logging.basicConfig(filename='coral.log', level=logging.DEBUG, format=LOGFORMAT)
engine = None
labels = None
ROOT_URL = "/v1/vision/detection"
def get_input_tensor(engine, image):
  _, height, width, _ = engine.get_input_tensor_shape()
  return np.asarray(image.resize((width, height), Image.NEAREST)).flatten()
# Function to read labels from text files.
def ReadLabelFile(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        ret = {}
        for line in lines:
            pair = line.strip().split(maxsplit=1)
            ret[int(pair[0])] = pair[1].strip()
    return ret
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
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            # input = get_input_tensor(engine, image)
            # Run inference.
            predictions = engine.detect_with_image(
                image,
                threshold=0.05,
                keep_aspect_ratio=True,
                relative_coord=False,
                top_k=10,
            )
            if predictions:
                data["success"] = True
                preds = []
                for prediction in predictions:
                    preds.append(
                        {
                            "confidence": float(prediction.score),
                            "label": labels[prediction.label_id],
                            "y_min": int(prediction.bounding_box[0, 1]),
                            "x_min": int(prediction.bounding_box[0, 0]),
                            "y_max": int(prediction.bounding_box[1, 1]),
                            "x_max": int(prediction.bounding_box[1, 0]),
                        }
                    )
                data["predictions"] = preds
    # return the data dictionary as a JSON response
    return flask.jsonify(data)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing coral USB stick")
    parser.add_argument(
        "--models_directory",
        default="models/",
        help="the directory containing the model & labels files",
    )
    parser.add_argument(
        "--model",
        default="mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite",
        help="Model file for inference",
    )
    parser.add_argument(
        "--labels", default="coco_labels.txt", help="labels file of model"
    )
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    global MODEL
    MODEL = args.model
    model_file = args.models_directory + args.model
    labels_file = args.models_directory + args.labels
    engine = DetectionEngine(model_file)
    print("\n Loaded engine with model : {}".format(model_file))
    labels = ReadLabelFile(labels_file)
    app.run(host="0.0.0.0", port=args.port)
