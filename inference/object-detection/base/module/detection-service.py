# Lint as: python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Example using TF Lite to detect objects in a given image."""

import argparse
import detect
import flask
import glob
import io
import logging
import tflite_runtime.interpreter as tflite
import time
import zipfile

from PIL import Image
from PIL import ImageDraw

app = flask.Flask(__name__)
LOGFORMAT = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
logging.basicConfig(
    filename=f'{__name__}.log', level=logging.DEBUG, format=LOGFORMAT)
HOLDER = {}


@app.route("/")
def info():
    info_str = "Flask app exposing tensorflow lite model {}".format(MODEL)
    return info_str


@app.route("/v1/vision/detection", methods=["POST"])
def predict():
    data = {"success": False}
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image_file = flask.request.files["image"]
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            scale = detect.set_input(
                HOLDER['interpreter'], image.size,
                lambda size: image.resize(size, Image.ANTIALIAS)
            )

            start = time.perf_counter()
            HOLDER['interpreter'].invoke()
            inference_time = time.perf_counter() - start
            objs = detect.get_output(
                HOLDER['interpreter'], HOLDER['threshold'], scale)

            data["inference-time"] = '%.2f ms' % (inference_time * 1000)

            if len(objs) > 0:
                data["success"] = True
                preds = []
                for obj in objs:
                    bbox = obj.bbox
                    preds.append(
                        {
                            "confidence": obj.score,
                            "label": HOLDER['labels'].get(obj.id, obj.id),
                            "y_min": bbox.ymin,
                            "x_min": bbox.xmin,
                            "y_max": bbox.ymax,
                            "x_max": bbox.xmax,
                        }
                    )
                data["predictions"] = preds

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


def init(args):
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

    labels = load_labels(label_list[0]) if len(label_list) > 0 else {}

    model_file = model_list[0]
    interpreter = make_interpreter(model_file)
    interpreter.allocate_tensors()

    global HOLDER
    HOLDER['labels'] = labels
    HOLDER['interpreter'] = interpreter
    HOLDER['threshold'] = args.threshold


def make_interpreter(model_file):
    model_file, *device = model_file.split('@')
    return tflite.Interpreter(model_path=model_file)


def main():
    parser = argparse.ArgumentParser(
        description="Flask app exposing Coral Edge TPU"
    )
    parser.add_argument(
        "--models_directory",
        default="models/",
        help="the directory containing the model & labels files",
    )
    parser.add_argument(
        "--threshold", default=0.4, type=float,
        help="Score threshold for detected objects."
    )
    parser.add_argument("--port", default=8501, type=int, help="port number")
    args = parser.parse_args()

    init(args)

    app.run(host="0.0.0.0", port=args.port)


if __name__ == '__main__':
    main()
