import boto3
import json

def modify_instance(event, context):
    message = event['Records'][0]['Sns']['Message']

    for line in str(message).split(','):


    event_source = message['Event Source']
    event_message = message['Event Message']