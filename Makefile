export LAMBDA_NAME=cloudacademy-calc-pi
export LAMBDA_REGION=us-west-2

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
	aws lambda update-function-code \
		--function-name "${LAMBDA_NAME}" \
		--zip-file fileb://function.zip \
		--region="${LAMBDA_REGION}" \
		| jq ".LastUpdateStatusReason" -r
	aws lambda update-function-configuration \
		--function-name "${LAMBDA_NAME}" \
		--environment '{"Variables":{"S3_BUCKET_NAME":"TOKEN_S3_BUCKET_NAME"}}' >/dev/null
	aws lambda wait function-updated \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}"
	@echo "The function has been deloyed."

run:
	aws lambda invoke \
		--function-name "${LAMBDA_NAME}" \
		--region="${LAMBDA_REGION}" out \
		--log-type Tail \
		| jq ".LogResult" -r | base64 -d

all:
	make build
	make deploy
	make run