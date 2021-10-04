# Handling binary data using API Gateway HTTP APIs

This is supporting code for AWS blog [Handling binary data using Amazon API Gateway HTTP APIs](https://aws.amazon.com/blogs/compute/handling-binary-data-using-amazon-api-gateway-http-apis/)

## Pre-requisites

The demo uses [Serverless Application Model (SAM)](https://aws.amazon.com/serverless/sam/) to deploy the infrastructure. If you need to familiarize yourself with SAM see this [Hello World Tutorial](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html).

Requirements:

* AWS SAM CLI: [installation instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* An AWS account: [create an AWS account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) if you do not already have one.
* AWS credentials with permissions to create roles: see the [SAM CLI setup instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install-mac.html#serverless-sam-cli-install-mac-iam-permissions) for details. 

## Running this code

[Clone](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) this repository. There are multiple revisions of the code to support the blog post but you likely only want to look at the final version in `sam-code` so within the newly created directory run:

```bash
cd sam-code
sam build --use-container
sam deploy --guided 
```

Answer setup questions:

```
Stack Name [sam-app]: http-api
AWS Region [us-east-1]: 
#Shows you resources changes to be deployed and require a 'Y' to initiate deploy
Confirm changes before deploy [y/N]: 
#SAM needs permission to be able to create roles to connect to the resources in your template
Allow SAM CLI IAM role creation [Y/n]: 
NoiseLambdaFunction may not have authorization defined, Is this okay? [y/N]: Y
Save arguments to configuration file [Y/n]: 
SAM configuration file [samconfig.toml]: 
SAM configuration environment [default]: 
```

When the deployment process is done see the output for the API URL:

![](blog-draft/step-1-output.png)

## Tests

### Manually

The following are described in more details in the blog post. 

```bash
# Cloudformation stack name - check samconfig.toml if you don't know
STACK_NAME=http-api

ECHO_RAW_API=$( aws cloudformation describe-stacks --stack-name ${STACK_NAME} --query "Stacks[*].Outputs[?OutputKey=='EchoRawHttpApi'].OutputValue" --output text )
ECHO_JSON_API=$( aws cloudformation describe-stacks --stack-name ${STACK_NAME} --query "Stacks[*].Outputs[?OutputKey=='EchoJsonHttpApi'].OutputValue" --output text )
NOISE_API=$( aws cloudformation describe-stacks --stack-name ${STACK_NAME} --query "Stacks[*].Outputs[?OutputKey=='NoiseHttpApi'].OutputValue" --output text )

# Echo back original binary POST submission 
# We use a simple GIF iamge created with ImageMagic: 
# convert -size 1x1 xc: /tmp/white.gif
curl -X POST \
  --data-binary @../testdata/white.gif \
  -H 'content-type: image/gif' \
  "${ECHO_RAW_API}" \
  --output /tmp/echo.gif
file /tmp/echo.gif

# Echo back submission event as received by lambda
# You don't need jq but it makes things a lot more readable
curl -X POST \
  --data-binary @../testdata/white.gif \
  -H 'content-type: image/gif' \
  "${ECHO_JSON_API}" \
| jq .

# Ask for unknown image format and submit plain text answer
# Returns: "Text path: Unknown encoding requested"
curl "${NOISE_API}?demo64Flag=0" -H 'Accept: image/unknown' 

# Ask for unknown image format and submit Base64 encoded answer
# Returns: "Binary path: Unknown encoding requested"
curl "${NOISE_API}?demo64Flag=1" -H 'Accept: image/unknown' 


# Create a noise image - this is a GET so you can do this in the browser too
# Default is JPEG 512x256, range 0..255
curl -X GET \
  "${NOISE_API}" \
  --output /tmp/noise.jpg
file /tmp/noise.jpg

# Create a noise image - change size and greyscale
curl -X GET \
  "${NOISE_API}?w=100&h=50&min=192&max=240" \
  --output /tmp/noise.jpg
file /tmp/noise.jpg

# Create a noise image - change output type via accept header
curl -X GET \
  -H 'accept: image/png' \
  "${NOISE_API}?w=100&h=50&min=192&max=240" \
  --output /tmp/noise.png
file /tmp/noise.png

curl -X GET \
  -H 'accept: image/gif' \
  "${NOISE_API}?w=100&h=50&min=192&max=240" \
  --output /tmp/noise.gif
file /tmp/noise.gif

curl -X GET \
  -H 'accept: image/bmp' \
  "${NOISE_API}?w=100&h=50&min=192&max=240" \
  --output /tmp/noise.bmp
file /tmp/noise.bmp

# Overlay image with noise - use binary image data 
# We use a simple jpge image created with ImageMagick: 
# convert xc:red xc:orange xc:yellow xc:green1 xc:cyan xc:blue +append -filter Cubic -resize 100x100! rainbow-small.jpg
curl -X POST \
  --data-binary @../testdata/rainbow-small.jpg \
  -H 'content-type: image/jpeg' \
  "${NOISE_API}" \
  --output /tmp/rainbow-noise.jpg
file /tmp/rainbow-noise.jpg

# Overlay image with noise - print text on canvas first 
curl -X POST \
  --data-binary @../testdata/multiline.txt \
  -H 'content-type: text/plain' \
  -H 'Accept: image/gif' \
  "${NOISE_API}?w=100&h=100" \
  --output /tmp/text-noise.gif 
file /tmp/text-noise.gif 

# Check OPTIONS for CORS
curl -X OPTIONS \
  -v \
  --data-binary @../testdata/multiline.txt \
  -H 'content-type: text/plain' \
  -H 'Accept: image/gif' \
  -H 'Access-Control-Request-Headers: content-type' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Origin: https://rudpot.github.io' \
  "${NOISE_API}?w=100&h=100" \
  --output /tmp/text-noise.gif 
file /tmp/text-noise.gif 

```

### PyTest

Basic validation can also be done via pytest. Ensure you have `pytest` and `pytest-datafiles` installed. Then from within the step directory of your choice, after deploying, run pytest like this:

```bash
# Cloudformation stack name - check samconfig.toml if you don't know
export AWS_SAM_STACK_NAME=http-api 

# Region in which the stack is deployed - check samconfig.toml if you don't know
export AWS_REGION=us-west-2 

pytest 
```

## Cleanup

Once you are done testing you might want to remove the resources you created in AWS. SAM does not have a native way to destroy resources but you can delete the cloudformation stack for your deployment. If you don't remember the name, check `stack_name` in `samconfig.toml`. On the command line you could use the AWS CLI:

```
aws cloudformation delete-stack --stack-name [SAM_STACK_NAME]
```

or you can do this from the [CloudFormation console](https://console.aws.amazon.com/cloudformation/home). Note that if you did deploy the code in all subdirectories you will need to do the cleanup for each of the stacks separately.