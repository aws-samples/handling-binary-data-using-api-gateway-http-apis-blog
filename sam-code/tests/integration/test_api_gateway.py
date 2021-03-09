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

import os
from unittest import TestCase
from io       import BytesIO
from PIL      import Image

import boto3
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestApiGateway(TestCase):
    api_endpoint: str

    EVENTS_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '../../../testdata'
    ))

    @classmethod
    def get_stack_name(cls) -> str:
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")
        if not stack_name:
            raise Exception(
                "Cannot find env var AWS_SAM_STACK_NAME. \n"
                "Please setup this environment variable with the stack name where we are running integration tests."
            )

        return stack_name

    def setUp(self) -> None:
        """
        Based on the provided env variable AWS_SAM_STACK_NAME,
        here we use cloudformation API to find out what the NoiseHttpApi URL is
        """
        stack_name = TestApiGateway.get_stack_name()

        client = boto3.client("cloudformation")

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name}. \n" f'Please make sure stack with the name "{stack_name}" exists.'
            ) from e

        stacks = response["Stacks"]

        stack_outputs = stacks[0]["Outputs"]
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "NoiseHttpApi"]
        self.assertTrue(api_outputs, f"Cannot find output NoiseHttpApi in stack {stack_name}")

        self.api_endpoint = api_outputs[0]["OutputValue"]

    # def test_api_gateway(self):
    #     """
    #     Call the API Gateway endpoint and check the response
    #     """
    #     response = requests.get(self.api_endpoint)
    #     self.assertDictEqual(response.json(), {"message": "hello world"})

    def test_api_gateway_unknown_image_type_plain(self):
        headers = {"accept": "image/unknown"}
        response = requests.get(self.api_endpoint,headers=headers)
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.content, b'Text path: Unknown encoding requested')

    def test_api_gateway_unknown_image_type_b64(self):
        headers = {"accept": "image/unknown"}
        params = {"demo64Flag": 1}
        response = requests.get(self.api_endpoint,headers=headers,params=params)
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.content, b'Binary path: Unknown encoding requested')

    def test_api_gateway_general(self):
        headers = {"accept": "*/*"}
        response = requests.get(self.api_endpoint,headers=headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'JPEG')

    def test_api_gateway_general_size_and_greyscale(self):
        headers = {"accept": "*/*"}
        params = {
            "h": "50",
            "max": "240",
            "min": "192",
            "w": "100"
        }
        response = requests.get(self.api_endpoint,headers=headers,params=params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'JPEG')
        self.assertEqual(Image.open(BytesIO(response.content)).size, (100,50))

    def test_api_gateway_png_size_and_greyscale(self):
        headers = {"accept": "image/png"}
        params = {
            "h": "50",
            "max": "240",
            "min": "192",
            "w": "100"
        }
        response = requests.get(self.api_endpoint,headers=headers,params=params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'PNG')
        self.assertEqual(Image.open(BytesIO(response.content)).size, (100,50))

    def test_api_gateway_gif_size_and_greyscale(self):
        headers = {"accept": "image/gif"}
        params = {
            "h": "50",
            "max": "240",
            "min": "192",
            "w": "100"
        }
        response = requests.get(self.api_endpoint,headers=headers,params=params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'GIF')
        self.assertEqual(Image.open(BytesIO(response.content)).size, (100,50))

    def test_api_gateway_bmp_size_and_greyscale(self):
        headers = {"accept": "image/bmp"}
        params = {
            "h": "50",
            "max": "240",
            "min": "192",
            "w": "100"
        }
        response = requests.get(self.api_endpoint,headers=headers,params=params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'BMP')
        self.assertEqual(Image.open(BytesIO(response.content)).size, (100,50))

    def test_api_gateway_overlay_grescale_on_image(self):
        headers = {"accept": "*/*"}
        with open(os.path.join(self.EVENTS_DIR,"rainbow-small.jpg"),"rb") as fh:
            data = fh.read()
        response = requests.get(self.api_endpoint,headers=headers,data=data)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'JPEG')

    def test_api_gateway_overlay_grescale_on_text(self):
        headers = {"accept": "*/*"}
        with open(os.path.join(self.EVENTS_DIR,"multiline.txt"),"rb") as fh:
            data = fh.read()
        response = requests.get(self.api_endpoint,headers=headers,data=data)
        self.assertEqual(response.status_code,200)
        self.assertEqual(Image.open(BytesIO(response.content)).format, 'JPEG')

    def test_api_gateway_check_cors_headers(self):
        headers = {
            "accept": "image/gif",
            "content-type": "text/plain",
            "Access-Control-Request-Headers": "content-type",
            "Access-Control-Request-Method": "POST",
            "Origin": "https://rudpot.github.io"
        }
        with open(os.path.join(self.EVENTS_DIR,"multiline.txt"),"rb") as fh:
            data = fh.read()
        response = requests.get(self.api_endpoint,headers=headers,data=data)
        self.assertEqual(response.status_code,200)
        print(response.headers)
        self.assertEqual(response.headers.get("access-control-allow-origin",""),"*")
        # self.assertEqual(response.headers.get("access-control-allow-headers",""),"access-control-allow-origin,content-type,x-requested-with")
        # self.assertEqual(response.headers.get("access-control-allow-methods",""),"GET,OPTIONS,POST")
