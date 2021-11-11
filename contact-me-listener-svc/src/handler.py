import boto3

def lambda_handler(event, context):
    query_params = event["queryStringParameters"]