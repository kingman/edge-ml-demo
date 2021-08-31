# Start the server:
# 	python3 coral-app.py
# Submit a request via cURL:
# 	curl -X POST -F image=@face.jpg 'http://localhost:5000/v1/vision/detection'
# coding=utf8

import argparse
import time
from PIL import Image
import flask
import logging
import io
import numpy as np
from pycoral.adapters import classify
from pycoral.adapters import common
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

app = flask.Flask(__name__)
LOGFORMAT = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
logging.basicConfig(filename='coral.log', level=logging.DEBUG, format=LOGFORMAT)
HOLDER = {}
ROOT_URL = "/v1/vision/detection"

@app.route("/")
def info():
    info_str = "Flask app exposing tensorflow lite model {}".format(HOLDER['model'])
    return info_str

@app.route(ROOT_URL, methods=["POST"])
def predict():
    data = {"success": False}
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image_file = flask.request.files["image"]
            image = Image.open(image_file).convert('RGB').resize(HOLDER['size'], Image.ANTIALIAS)
            params = common.input_details(HOLDER['interpreter'], 'quantization_parameters')
            scale = params['scales']
            zero_point = params['zero_points']
            mean=128.0
            std=128.0
            if abs(scale * std - 1) < 1e-5 and abs(mean - zero_point) < 1e-5:
                # Input data does not require preprocessing.
                common.set_input(HOLDER['interpreter'], image)
            else:
                # Input data requires preprocessing
                normalized_input = (np.asarray(image) - mean) / (std * scale) + zero_point
                np.clip(normalized_input, 0, 255, out=normalized_input)
                common.set_input(HOLDER['interpreter'], normalized_input.astype(np.uint8))
            
            start = time.perf_counter()
            HOLDER['interpreter'].invoke()
            inference_time = time.perf_counter() - start
            classes = classify.get_classes(HOLDER['interpreter'], HOLDER['top_k'], 0.0)
            
            if classes:
                data["success"] = True
                data["inference-time"] = '%.2f ms' % (inference_time * 1000)
                preds = []
                for c in classes:                    
                    preds.append(
                        {
                            "score": float(c.score),
                            "label": HOLDER['labels'].get(c.id, c.id)
                        }
                    )
                data["predictions"] = preds
    return flask.jsonify(data)

def init(args):
    global HOLDER
    HOLDER['model'] = args.model

    labels_file = args.models_directory + args.labels
    labels = read_label_file(labels_file) if args.labels else {}
    
    model_file = args.models_directory + args.model    
    interpreter = make_interpreter(model_file)
    interpreter.allocate_tensors()

    print("\n Loaded engine with model : {}".format(model_file))
    
    # Model must be uint8 quantized
    if common.input_details(interpreter, 'dtype') != np.uint8:
        raise ValueError('Only support uint8 input type.')
    size = common.input_size(interpreter)

    HOLDER['labels'] = labels
    HOLDER['interpreter'] = interpreter
    HOLDER['size'] = size
    HOLDER['top_k'] = args.top_k

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing coral USB stick")
    parser.add_argument(
        "--models_directory",
        default="models/",
        help="the directory containing the model & labels files",
    )
    parser.add_argument(
        "--model",
        default="base.tflite",
        help="model file",
    )
    parser.add_argument(
        "--labels", default="base_labels.txt", help="labels file of model"
    )
    parser.add_argument(
        "--top_k", default=1, type=int, help="Max number of classification results"
    )
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()

    init(args)    

    app.run(host="0.0.0.0", port=args.port)