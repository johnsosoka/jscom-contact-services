import boto3
import json


class SNSPublisher:

    def __init__(self):
        self._sns_client = boto3.client("sns")

    def publish_message(self, topic_arn, message_json):
        client = boto3.client("sns")
        response = self._sns_client.publish(
            TargetArn=topic_arn,
            Message=json.dumps({'default': message_json}),
            MessageStructure='json'
        )
