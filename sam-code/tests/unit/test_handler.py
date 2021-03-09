# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import os

import pytest

from img_api import app
from base64  import b64decode
from PIL     import Image
from io      import BytesIO

EVENTS_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '../../events'
    ))

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_unknown_image_type_default.json'))
def test_lambda_handler_unknown_image_type_plain(datafiles, mocker):
    with open(os.path.join(datafiles,'event_unknown_image_type_default.json')) as fh:
        event_unknown_image_type_default = json.load(fh)        
    ret = app.lambda_handler(event_unknown_image_type_default, "")
    assert ret["statusCode"] == 400
    assert ret["body"] == 'Text path: Unknown encoding requested'

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_unknown_image_type_b64.json'))
def test_lambda_handler_unknown_image_type_b64(datafiles, mocker):
    with open(os.path.join(datafiles,'event_unknown_image_type_b64.json')) as fh:
        event_unknown_image_type_b64 = json.load(fh)        
    ret = app.lambda_handler(event_unknown_image_type_b64, "")
    assert ret["statusCode"] == 400
    assert b64decode(ret["body"]) == b'Binary path: Unknown encoding requested'

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_general_invoke.json'))
def test_lambda_handler_general(datafiles, mocker):
    with open(os.path.join(datafiles,'event_general_invoke.json')) as fh:
        event_unknown_image_type_plain = json.load(fh)        
    ret = app.lambda_handler(event_unknown_image_type_plain, "")
    assert ret["statusCode"] == 200
    assert Image.open(BytesIO(b64decode(ret["body"]))).format == 'JPEG'

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_general_size_and_greyscale.json'))
def test_lambda_handler_general_size_and_greyscale(datafiles, mocker):
    with open(os.path.join(datafiles,'event_general_size_and_greyscale.json')) as fh:
        event_general_size_and_greyscale = json.load(fh)        
    ret = app.lambda_handler(event_general_size_and_greyscale, "")
    assert ret["statusCode"] == 200
    assert Image.open(BytesIO(b64decode(ret["body"]))).format == 'JPEG'
    assert Image.open(BytesIO(b64decode(ret["body"]))).size == (100,50)

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_png_size_and_greyscale.json'))
def test_lambda_handler_png_size_and_greyscale(datafiles, mocker):
    with open(os.path.join(datafiles,'event_png_size_and_greyscale.json')) as fh:
        event_png_size_and_greyscale = json.load(fh)        
    ret = app.lambda_handler(event_png_size_and_greyscale, "")
    assert ret["statusCode"] == 200
    assert Image.open(BytesIO(b64decode(ret["body"]))).format == 'PNG'
    assert Image.open(BytesIO(b64decode(ret["body"]))).size == (100,50)

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_gif_size_and_greyscale.json'))
def test_lambda_handler_gif_size_and_greyscale(datafiles, mocker):
    with open(os.path.join(datafiles,'event_gif_size_and_greyscale.json')) as fh:
        event_gif_size_and_greyscale = json.load(fh)        
    ret = app.lambda_handler(event_gif_size_and_greyscale, "")
    assert ret["statusCode"] == 200
    assert Image.open(BytesIO(b64decode(ret["body"]))).format == 'GIF'
    assert Image.open(BytesIO(b64decode(ret["body"]))).size == (100,50)

@pytest.mark.datafiles(os.path.join(EVENTS_DIR,'event_bmp_size_and_greyscale.json'))
def test_lambda_handler_bmp_size_and_greyscale(datafiles, mocker):
    with open(os.path.join(datafiles,'event_bmp_size_and_greyscale.json')) as fh:
        event_bmp_size_and_greyscale = json.load(fh)        
    ret = app.lambda_handler(event_bmp_size_and_greyscale, "")
    assert ret["statusCode"] == 200
    assert Image.open(BytesIO(b64decode(ret["body"]))).format == 'BMP'
    assert Image.open(BytesIO(b64decode(ret["body"]))).size == (100,50)

