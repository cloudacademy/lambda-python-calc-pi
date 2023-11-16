export LAMBDA_NAME=cloudacademy-calc-pi
export LAMBDA_REGION=us-west-2
export IAM_ROLE_ARN=TOKEN_IAM_ROLE_ARN

SHELL = bash

.DEFAULT_GOAL := all

build:
	pip3.10 install -r requirements.txt \
		--platform manylinux2014_x86_64 \
		--target=./package \
		--implementation cp \
		--only-binary=:all: --upgrade

deploy:
	pushd ./package && zip -r ../function.zip ./ && popd
	zip function.zip lambda_function.py
	aws lambda create-function \
		--function-name "${LAMBDA_NAME}" \
		--runtime python3.10 \
		--zip-file fileb://function.zip \
		--handler lambda_function.lambda_handler \
		--role "${IAM_ROLE_ARN}" \
		--environment '{"Variables":{"S3_BUCKET_NAME":"TOKEN_S3_BUCKET_NAME"}}' \
		--tracing-config 'Mode=Active' \
		--region "${LAMBDA_REGION}"
	aws lambda create-function-url-config \
		--function-name "${LAMBDA_NAME}" \
		--auth-type "NONE"
	aws lambda wait function-updated \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}"
	@echo "The function has been deployed."

run:
	aws lambda invoke \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}" \
		--cli-binary-format raw-in-base64-out \
		--payload '{"queryStringParameters": {"num": "100"}}' \
		--log-type Tail \
		out \
		| jq ".LogResult" -r | base64 -d

all:
	make build
	make deploy
	make run