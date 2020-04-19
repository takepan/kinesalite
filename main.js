//main.js
var AWS = require('aws-sdk')
AWS.config.update({region:'us-east-1'});

var kinesis = new AWS.Kinesis({endpoint: 'http://localhost:4567'})
kinesis.listStreams(console.log.bind(console))
