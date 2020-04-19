docker-compose build
docker-compose up -d

Interact with Kinesis Local:
In this next steps we will setup our environment, which will only require python and boto3. To keep things isolated, I will do this with a docker container:

1
$ docker run -it python:3.7-alpine sh
Now we need to install boto3 and enter the python repl:

1
2
3
4
5
6
$ pip3 install boto3
$ python3
Python 3.7.3 (default, May 11 2019, 02:00:41)
[GCC 8.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
Import boto and create the connection to our kinesis local instance:

1
2
3
4
>>> import boto3, json
>>> client = boto3.Session(
    region_name='eu-west-1').client('kinesis', aws_access_key_id='', aws_secret_access_key='', endpoint_url='http://localhost:4567'
)
Let’s list our streams and as expected, we should have zero streams available:

1
2
>>> client.list_streams()
{u'StreamNames': [], u'HasMoreStreams': False, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '637xx', 'HTTPHeaders': {'x-amzn-requestid': '6xx', 'content-length': '41', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:17:34 GMT', 'content-type': 'application/x-amz-json-1.1'}}}
Let’s create a stream named mystream with 1 primary shard:

1
>>> client.create_stream(StreamName='mystream', ShardCount=1)
Let’s list our streams again:

1
2
>>> client.list_streams()
{u'StreamNames': [u'mystream'], u'HasMoreStreams': False, 'ResponseMetadata': ...
Let’s put some data in our kinesis stream, we will push a payload with the body: {"name": "ruan"} to our kinesis stream with partition key: a01 which is used for sharding:

1
2
3
>>> response = client.put_record(StreamName='mystream', Data=json.dumps({"name": "ruan"}), PartitionKey='a01')
>>> response
{u'ShardId': u'shardId-000000000000', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'cb0xx', 'HTTPHeaders': {'x-amzn-requestid': 'xx', 'content-length': '110', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:20:27 GMT', 'content-type': 'application/x-amz-json-1.1'}}, u'SequenceNumber': u'490xx'}
Now that we have data in our stream we need to read data from our kinesis stream. Before data can be read from the stream we need to obtain the shard iterator for the shard we are interested in. A shard iterator represents the position of the stream and shard from which the consumer will read, in this case we will call the get_shard_operator method and passing the stream name, shard id and shard iterator type.

There are 2 comman iterator types:

TRIM_HORIZON: Points to the last untrimmed record in the shard
LATEST: Reads the most recent data in the shard
We will use TRIM_HORIZON in this case, get the shard iterator id:

1
2
3
4
>>> shard_id = response['ShardId']
>>> response = client.get_shard_iterator(StreamName='mystream', ShardId=shard_id, ShardIteratorType='TRIM_HORIZON')
>>> response
{u'ShardIterator': u'AAAxx=', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '22dxx', 'HTTPHeaders': {'x-amzn-requestid': '22dxx', 'content-length': '224', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:22:55 GMT', 'content-type': 'application/x-amz-json-1.1'}}}
Now that we have the shard iterator id, we can call the get_records method with the shard iterator id, to read the data from the stream:

1
2
3
4
>>> shard_iterator = response['ShardIterator']
>>> response = client.get_records(ShardIterator=shard_iterator)
>>> response
{u'Records': [{u'Data': '{"name": "ruan"}', u'PartitionKey': u'a01', u'ApproximateArrivalTimestamp': datetime.datetime(2019, 6, 22, 21, 20, 27, 937000, tzinfo=tzlocal()), u'SequenceNumber': u'495xx'}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '2b6xx', 'HTTPHeaders': {'x-amzn-requestid': '2b6xx', 'content-length': '441', 'x-amz-id-2': 'xx', 'connection': 'keep-alive', 'date': 'Sat, 22 Jun 2019 19:30:19 GMT', 'content-type': 'application/x-amz-json-1.1'}}, u'NextShardIterator': u'AAAxx=', u'MillisBehindLatest': 0}
To loop and parse through the response to make it more readable:

1
2
3
4
5
>>> for record in response['Records']:
...     if 'Data' in record:
...         json.loads(record['Data'])
...
{u'name': u'ruan'}
Once we are done, we can delete our stream:

1
>>> client.delete_stream(StreamName='mystream')
Now that we have the basics, lets create our producer and consumer for a demonstration on pushing data to a kinesis stream from one process and consuming it from another process. As this demonstration we will be producing and consuming data from the same laptop, in real use-cases, you will do them from seperate servers and using Amazon Kinesis.

Our Kinesis Producer
The following will create a Kinesis Local Stream and Write 25 JSON Documents to our stream:

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
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
Our Kinesis Local Consumer:
This will read 5 records at a time from our stream, you will notice if you run them on the same time it will only read one at a time as the producer only writes one per second.

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
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

Start the server:

1
2
$ docker run -it -p 4567:4567 ruanbekker/kinesis-local:latest
Listening at http://:::4567
Run the Producer from your Python Environment:

1
2
3
$ python producer.py
Starting at 00:06:16
Finished at 00:06:42
Run the Consumer from your Python Environment:

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
$ python consumer.py
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

