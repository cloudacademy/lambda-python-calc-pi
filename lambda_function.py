import json
import boto3
import logging
import os
import random
import textwrap
import time

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

libraries = (['botocore'])
patch(libraries)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_bucknet_name = os.environ.get("S3_BUCKET_NAME", "unknown")

print(s3_bucknet_name)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    logging.info('calculates pi to n decimal places...')

    num = event["queryStringParameters"]['num']

    subsegment = xray_recorder.begin_subsegment('pi-calc')
    subsegment.put_annotation('num', num)

    pi = 0

    try:
        if num:
            digits = [str(n) for n in list(pi_digits(int(num)))]
            pi = "%s.%s\n" % (digits.pop(0), "".join(digits))
            time.sleep(10) #simulate long running task
    except:
        pass

    subsegment.put_metadata("num", num)
    subsegment.put_metadata("pi", pi)
    xray_recorder.end_subsegment()

    response_code = 200

    #randomize response code
    random_error = random.uniform(0, 1)

    if random_error < 0.5:
        #GREEN
        response_code = 200
    elif random_error < 0.7:
        #ORANGE
        response_code = 403
    else:
        #RED
        response_code = 503

    pi_wrapped = "\n".join(textwrap.wrap(pi,32))

    subsegment = xray_recorder.begin_subsegment('s3-save')
    subsegment.put_annotation('num', num)
    subsegment.put_metadata("pi_wrapped", pi_wrapped)

    file_name = "pi.txt"
    s3_path = "data/" + file_name

    s3 = boto3.resource("s3")
    s3.Bucket(s3_bucknet_name).put_object(Key=s3_path, Body=pi_wrapped.encode("utf-8"))

    xray_recorder.end_subsegment()
    xray_recorder.end_segment()

    return {
        "statusCode": response_code,
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "application/json",
            "RandomError": random_error
        },
        "body": pi
    }

def pi_digits(x):
    k,a,b,a1,b1 = 2,4,1,12,4
    while x > 0:
        p,q,k = k * k, 2 * k + 1, k + 1
        a,b,a1,b1 = a1, b1, p*a + q*a1, p*b + q*b1
        d,d1 = a/b, a1/b1
        while d == d1 and x > 0:
            yield int(d)
            x -= 1
            a,a1 = 10*(a % b), 10*(a1 % b1)
            d,d1 = a/b, a1/b1
