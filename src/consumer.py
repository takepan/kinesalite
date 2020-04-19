import boto3
import json
import time
import os

session = boto3.Session(region_name='eu-west-1')
client = session.client(
    'kinesis',
    aws_access_key_id='',
    aws_secret_access_key='',
    endpoint_url='http://localhost:4567'
)

stream_details = client.describe_stream(StreamName='mystream')
shard_id = stream_details['StreamDescription']['Shards'][0]['ShardId']

response = client.get_shard_iterator(
    StreamName='mystream',
    ShardId=shard_id,
    ShardIteratorType='TRIM_HORIZON'
)

shard_iterator = response['ShardIterator']

print("Starting at {}".format(time.strftime("%H:%m:%S")))

while True:
    response = client.get_records(ShardIterator=shard_iterator, Limit=5)
    shard_iterator = response['NextShardIterator']
    if not response['Records']:
        break
    for record in response['Records']:
        if 'Data' in record and len(record['Data']) > 0:
            print(json.loads(record['Data'].decode("UTF-8")))
    time.sleep(0.75)

print("Finished at {}".format(time.strftime("%H:%m:%S")))

