import json
import boto3
import logging
import os
import random

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

libraries = (['botocore'])
patch(libraries)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs_queue_url = os.environ.get("SQS_QUEUE_URL", "unknown")
#sqs_queue_url = 'https://sqs.us-west-2.amazonaws.com/379242798045/calc.fifo'

print(sqs_queue_url)

service_name = 'ADD'

sqs = boto3.client('sqs')

def lambda_handler(event, context):
    logging.info('calculates pi to n decimal places...')

    num = event["queryStringParameters"]['num']
    calcid = event["queryStringParameters"]['calcid']

    subsegment = xray_recorder.begin_subsegment('add_service')
    subsegment.put_annotation('calcid', calcid)

    pi = 0

    try:
        if num:
            digits = [str(n) for n in list(pi_digits(int(num)))]
            pi = "%s.%s\n" % (digits.pop(0), "".join(digits))
    except:
        pass

    subsegment.put_metadata("num", num)
    subsegment.put_metadata("pi", pi)

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

    sqs.send_message(
        QueueUrl=sqs_queue_url,
        MessageGroupId=calcid,
        MessageDeduplicationId=calcid,
        MessageBody=pi,
        MessageAttributes={
            'Num': {
                'StringValue': num,
                'DataType': 'Number'
            },
            'CalcId': {
                'StringValue': calcid,
                'DataType': 'String'
            }
        }
    )

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
