# original
https://blog.ruanbekker.com/blog/2019/06/22/play-with-kinesis-data-streams-for-free/

# with docker-compose
docker-compose build  
docker-compose up -d  
docker-compose exec kinesalite bash


$ python3
```python3
>>> import boto3, json  
>>> client = boto3.Session(  
    region_name='eu-west-1').client('kinesis', aws_access_key_id='', aws_secret_access_key='', endpoint_url='http://localhost:4567'  
)  
>>> client.list_streams()  
{u'StreamNames': [], u'HasMoreStreams': False, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '637xx', 'HTTPHeaders': {'x-amzn-requestid': '6xx', 'content-length': '41', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:17:34 GMT', 'content-type': 'application/x-amz-json-1.1'}}}  
>>> client.create_stream(StreamName='mystream', ShardCount=1)  
>>> client.list_streams()
{u'StreamNames': [u'mystream'], u'HasMoreStreams': False, 'ResponseMetadata': ...  
>>> response = client.put_record(StreamName='mystream', Data=json.dumps({"name": "ruan"}), PartitionKey='a01')  
>>> response  
{u'ShardId': u'shardId-000000000000', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'cb0xx', 'HTTPHeaders': {'x-amzn-requestid': 'xx', 'content-length': '110', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:20:27 GMT', 'content-type': 'application/x-amz-json-1.1'}}, u'SequenceNumber': u'490xx'}  
>>> shard_id = response['ShardId']
>>> response = client.get_shard_iterator(StreamName='mystream', ShardId=shard_id, ShardIteratorType='TRIM_HORIZON')
>>> response  
{u'ShardIterator': u'AAAxx=', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '22dxx', 'HTTPHeaders': {'x-amzn-requestid': '22dxx', 'content-length': '224', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:22:55 GMT', 'content-type': 'application/x-amz-json-1.1'}}}  
>>> shard_iterator = response['ShardIterator']  
>>> response = client.get_records(ShardIterator=shard_iterator)  
>>> response  
{u'Records': [{u'Data': '{"name": "ruan"}', u'PartitionKey': u'a01', u'ApproximateArrivalTimestamp': datetime.datetime(2019, 6, 22, 21, 20, 27, 937000, tzinfo=tzlocal()), u'SequenceNumber': u'495xx'}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '2b6xx', 'HTTPHeaders': {'x-amzn-requestid': '2b6xx', 'content-length': '441', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:30:19 GMT', 'content-type': 'application/x-amz-json-1.1'}}, u'NextShardIterator': u'AAAxx=', u'MillisBehindLatest': 0}  
>>> for record in response['Records']:  
...     if 'Data' in record:  
...         json.loads(record['Data'].decode("UTF-8"))  
...  
{u'name': u'ruan'}
>>> client.delete_stream(StreamName='mystream')
```

Our Kinesis Producer
The following will create a Kinesis Local Stream and Write 25 JSON Documents to our stream:
```python3
import boto3
import random
import json
import time

names = ['james', 'stefan', 'pete', 'tom', 'frank', 'peter', 'ruan']

session = boto3.Session(region_name='eu-west-1')
client = session.client(
    'kinesis',
    aws_access_key_id='',
    aws_secret_access_key='',
    endpoint_url='http://localhost:4567'
)

list_streams = client.list_streams()

if 'mystream' not in list_streams['StreamNames']:
    client.create_stream(StreamName='mystream', ShardCount=1)
    time.sleep(1)

count = 0
print("Starting at {}".format(time.strftime("%H:%m:%S")))

while count != 25:
    count += 1
    response = client.put_record(
        StreamName='mystream',
        Data=json.dumps({
            "number": count,
            "name": random.choice(names),
            "age": random.randint(20,50)}
        ),
        PartitionKey='a01'
    )
    time.sleep(1)

print("Finished at {}".format(time.strftime("%H:%m:%S")))
```

Our Kinesis Local Consumer:
This will read 5 records at a time from our stream, you will notice if you run them on the same time it will only read one at a time as the producer only writes one per second.


```python3
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

while True:
    response = client.get_records(ShardIterator=shard_iterator, Limit=5)
    shard_iterator = response['NextShardIterator']
    for record in response['Records']:
        if 'Data' in record and len(record['Data']) > 0:
            print(json.loads(record['Data']))
    time.sleep(0.75)
Demo Time!
Now that we have our producer.py and consumer.py, lets test this out.
```

```
$ python3 producer.py
Starting at 00:06:16
Finished at 00:06:42
```

```
$ python3 consumer.py
Starting Consuming at 00:06:31
{u'age': 30, u'number': 1, u'name': u'pete'}
{u'age': 23, u'number': 2, u'name': u'ruan'}
{u'age': 22, u'number': 3, u'name': u'peter'}
{u'age': 45, u'number': 4, u'name': u'stefan'}
{u'age': 49, u'number': 5, u'name': u'tom'}
{u'age': 47, u'number': 6, u'name': u'pete'}
{u'age': 35, u'number': 7, u'name': u'stefan'}
{u'age': 45, u'number': 8, u'name': u'ruan'}
{u'age': 38, u'number': 9, u'name': u'frank'}
{u'age': 20, u'number': 10, u'name': u'tom'}
{u'age': 38, u'number': 11, u'name': u'james'}
{u'age': 20, u'number': 12, u'name': u'james'}
{u'age': 38, u'number': 13, u'name': u'tom'}
{u'age': 25, u'number': 14, u'name': u'tom'}
{u'age': 20, u'number': 15, u'name': u'peter'}
{u'age': 50, u'number': 16, u'name': u'james'}
{u'age': 29, u'number': 17, u'name': u'james'}
{u'age': 42, u'number': 18, u'name': u'pete'}
{u'age': 25, u'number': 19, u'name': u'pete'}
{u'age': 36, u'number': 20, u'name': u'tom'}
{u'age': 45, u'number': 21, u'name': u'peter'}
{u'age': 39, u'number': 22, u'name': u'ruan'}
{u'age': 43, u'number': 23, u'name': u'tom'}
{u'age': 38, u'number': 24, u'name': u'pete'}
{u'age': 40, u'number': 25, u'name': u'frank'}
Finshed Consuming at 00:06:35
```
