#! /usr/bin/env python3

from tkinter import W
from flask import Flask, send_from_directory, request
import pika
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
ROOT = Path(os.path.abspath(__file__)).parent
WEBPAGE = ROOT/Path("webpage")

class RESTApp:
    def __init__(self, host, port, rmqHost, rmqPort):
        self.host = host
        self.port = port
        self.rmqHost = rmqHost
        self.rmqPort = rmqPort

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rmqHost, port=self.rmqPort))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='task_queue', durable=True)
        self.app = Flask(__name__)
        self._configure_requests()

    def run(self, debug=False):
        self.app.run(debug=debug, host=self.host, port=self.port)

    def _configure_requests(self):
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/add-job/<cmd>', view_func=self.add, methods=['GET', 'POST'])
        self.app.add_url_rule("/client.js", view_func=self.javascript, methods=['GET'])

    def index(self):
        content = open(WEBPAGE/Path("index.html"), "r").read()
        return content
    
    def javascript(self):
        content = open(WEBPAGE/Path("client.js"), "r").read()
        return content

    def add(self, cmd):
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=cmd,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        return " [x] Sent: %s" % cmd

if __name__ == '__main__':
    app = RESTApp("0.0.0.0", 8090, "0.0.0.0", 5672)
    app.run()