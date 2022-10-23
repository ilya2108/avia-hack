#! /usr/bin/env python3

from flask import Flask, request
import requests as req
import pika
from pika import exceptions as pe
import logging
import os
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)

ROOT = Path(os.path.abspath(__file__)).parent
WEBPAGE = ROOT/Path("webpage")

class RESTApp:
    def __init__(self, appPort, rmqPort, dbhPort):
        self.host = "0.0.0.0"
        self.port = appPort
        self.rmqHost = "broker"
        self.rmqPort = rmqPort
        self.dbHost = "db_handler"
        self.dbhPort = dbhPort

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rmqHost, port=self.rmqPort))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='task_queue', durable=True)
        self.app = Flask(__name__)
        self._configure_requests()

    def run(self, debug=False):
        self.app.run(debug=debug, host=self.host, port=self.port)

    def _configure_requests(self):
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/api/tasks/send', view_func=self.add, methods=['POST'])
        self.app.add_url_rule('/api/tasks/lookup', view_func=self.check_task, methods=['GET'])
        # self.app.add_url_rule("/client.js", view_func=self.javascript, methods=['GET'])

    def index(self):
        return "Server is running"
    
    # def javascript(self):
    #     content = open(WEBPAGE/Path("client.js"), "r").read()
    #     return content

    def add(self):
        try:
            name = request.args['name']
        except KeyError:
            name = "default"
        r = req.put("http://{}:{}/api/tasks/append".format(self.dbHost, self.dbhPort), params={'name': name})
        task = r.json()
        in_file = request.data.decode("utf-8")
        rmq_task = {'key': task['key'], 'in_file': in_file}
        try:
            self._rmq_pub(json.dumps(rmq_task))
        except (pe.ConnectionClosed, pe.AMQPConnectionError, pe.ChannelWrongStateError) as e: 
            return {'status': 'error', 'message': 'RMQ connection error %s' % e}
        else:
            return {'key': task['key'], 'status': task['status']}

    def check_task(self):
        key = request.args.get('key')
        r = req.get("http://{}:{}/api/tasks/lookup".format(self.dbHost, self.dbhPort), params={'key': key})
        return r.json()

    def _rmq_pub(self, cmd):
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=str(cmd),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))

if __name__ == '__main__':
    app = RESTApp(appPort=8090, rmqPort=5672, dbhPort=8070)
    app.run()