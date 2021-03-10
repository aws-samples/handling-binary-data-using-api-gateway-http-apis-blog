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
import re
from io     import BytesIO
from random import random
from base64 import b64encode,b64decode
from PIL    import Image, ImageFont, ImageDraw

xdim = 512
ydim = 256
cmin = 0
cmax = 255

known_conversions = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/apng": "PNG",
    "image/gif": "GIF",
    "image/bmp": "BMP",
}

def generate_noise_bytes(xdim=50,ydim=50,cmin=0,cmax=255):
    # Generate data - this is a substantial performance hit for larger images!
    img_bytes = bytes([int((cmax-cmin)*random())+cmin for x in range(xdim*ydim)])
    return img_bytes

def generate_noise_img(xdim,ydim,cmin=0,cmax=255):
    # Use PIL to create image
    img_bytes = generate_noise_bytes(xdim,ydim,cmin,cmax)
    image = Image.frombytes('L',(xdim,ydim), img_bytes, "raw", "L", 0, 1)
    return image

def get_mime_type(accept_string):
    # Accept string is a comma separated list of preferences. Find first one we can handle
    for option in accept_string.split(","):
        mime_type = option.split(";")[0]
        if mime_type == "*/*":
            mime_type = "image/jpeg"
        if mime_type in known_conversions:
            return mime_type
    return "unknown/unknown"

def encode_img(image,accept_string):
    # Convert image data into an image file and base64 encode it
    mime_type = get_mime_type(accept_string)
    if mime_type in known_conversions:
        # Use BytesIO to write to a virtual file
        img_buffer = BytesIO()
        image.save(img_buffer,format=known_conversions[mime_type])
        img_binary = img_buffer.getvalue()
        img_buffer.close()
        return { "success": True,  "mimetype": mime_type,    "data": img_binary }
    else:
        return { "success": False, "mimetype": "text/plain", "data": "Unknown encoding requested" }

def decode_img(img_data,mime_type,xdim,ydim):
    # If the content type claims we received an image/binary:
    if re.match("image/",mime_type) or mime_type=='application/x-www-form-urlencoded':
        # This function relies entirely on PIL to identify image type, no mime type checking
        img_buffer = BytesIO(img_data)
        img_buffer.seek(0)
        image = Image.open(img_buffer)
    else:
        # Render the plain text as black text on a white background
        image = Image.new("RGB", (xdim,ydim), (255, 255, 255))
        draw  = ImageDraw.Draw(image)
        draw.multiline_text((0,0),img_data.decode('utf-8'),fill=(0,0,0))
    if image.mode == 'P':
        image = image.convert('RGB')
    return image

def overlay_noise_on_image(image,cmin=0,cmax=255):
    xdim_src, ydim_src = image.size
    noise_image = generate_noise_img(xdim=xdim_src, ydim=ydim_src, cmin=cmin, cmax=cmax)
    image.paste(noise_image,(0,0),noise_image)
    return image

def lambda_handler(event, context):
    print(event)

    # Define desired image dimentions from query string if provided
    xdim_requested = int(event.get("queryStringParameters",{}).get("w",  xdim))
    ydim_requested = int(event.get("queryStringParameters",{}).get("h",  ydim))
    cmin_requested = int(event.get("queryStringParameters",{}).get("min",cmin))
    cmax_requested = int(event.get("queryStringParameters",{}).get("max",cmax))

    # For demo purposes only - define whether plain text response in base64 encoded
    demo64Flag   = int(event.get("queryStringParameters",{}).get("demo64Flag",0))

    # Define desired output formate from accept header, default to JPEG 
    accept = event.get("headers",{}).get("accept","image/jpeg")



    # Get the RESTful VERB
    verb = event.get("requestContext",{}).get("http",{}).get("method","GET").split()[0]
    # On OPTIONS we don't return data so save time
    if verb == "OPTIONS":
        image = Image.new('RGB',(1,1))
        result = encode_img(image,accept)
    # On POST, take an image, overlay noise
    elif verb == "POST":
        # Base64 decode data it it came in encoded
        img_string = event.get("body","")
        if event.get("isBase64Encoded",False)==True:
            img_data = b64decode(img_string)
        else:
            img_data = img_string.encode('utf-8')
        # Get a PIL image object from data and overlay noise
        image = decode_img(
            img_data, 
            event.get("headers",{}).get("content-type","text/plain"),
            xdim_requested,ydim_requested
            )
        image = overlay_noise_on_image(image,cmin_requested,cmax_requested)
        result = encode_img(image,accept)
    # On GET, just return the noise
    elif verb == "GET":
        image = generate_noise_img(xdim_requested,ydim_requested,cmin_requested,cmax_requested)
        result = encode_img(image,accept)
    # On all other calls return error
    else:
        result = { "success": False, "mimetype": "text/plain", "data": "Unsupported HTTP method" }

    if result["success"]:
        return {
            # Status code 200 HTTP OK
            'statusCode': 200,
            # Return the mime type of the image
            'headers': {
                'Content-Type': result["mimetype"],
                'Access-Control-Allow-Origin': '*'
            },
            # Return the image
            'body': b64encode(result["data"]),
            # Tell API-GW that it's Base64 encoded. 
            'isBase64Encoded': True
        }       
    else: # fail
        # Return failure message as unencoded string to API-GW
        if demo64Flag == 0:
            return_string = "Text path: " + result["data"]
            return_encode = False
        # Return failure message as unencoded string to API-GW
        else:
            return_string = b64encode(("Binary path: " + result["data"]).encode('utf-8'))
            return_encode = True

        return {                
            # Status code 400 HTTP BAD REQUEST
            'statusCode': 400,
            # Return the mime type of the response
            'headers': {
                'Content-Type': 'text/plain'
            },
            # Return message, might be Base64 encoded
            'body': return_string,
            # Tell API-GW whether it's Base64 encoded. 
            'isBase64Encoded': return_encode
        }
