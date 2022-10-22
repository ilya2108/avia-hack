#! /usr/bin/env python3

from this import d
from flask import Flask
import pika
import logging
import os

logging.basicConfig(level=logging.INFO)

class RESTApp:
    def __init__(self, host, port, rmqHost, rmqPort):
        self.host = host
        self.port = port
        self.rmqHost = rmqHost
        self.rmqPort = rmqPort

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rmqHost, port=self.rmqPort))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='task_queue', durable=True)
        # self.channel.basic_qos(prefetch_count=1)
        # self.channel.basic_consume(queue='task_queue', on_message_callback=self.callback)
        self.app = Flask(__name__)
        self._configure_requests()

    def run(self, debug=False):
        self.app.run(debug=debug, host=self.host, port=self.port)

    def _configure_requests(self):
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/add-job/<cmd>', 'add', self.add)

    # def callback(self, ch, method, properties, body):
    #     logging.info(" [x] Received %r" % body)
    #     cmd = body.decode()

    #     if cmd == 'hey':
    #         print("hey there")
    #     elif cmd == 'hello':
    #         print("well hello there")
    #     else:
    #         print("sorry i did not understand ", body)

    #     ch.basic_ack(delivery_tag=method.delivery_tag)

    def index(self):
        return 'OK'

    def add(self, cmd):
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=cmd,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        return " [x] Sent: %s" % cmd
    

# @app.route('/')
# def index():
#     return 'OK'


# @app.route('/add-job/<cmd>')
# def add(cmd):
#     connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1', port=5672))
#     channel = connection.channel()
#     channel.queue_declare(queue='task_queue', durable=True)
#     channel.basic_publish(
#         exchange='',
#         routing_key='task_queue',
#         body=cmd,
#         properties=pika.BasicProperties(
#             delivery_mode=2,  # make message persistent
#         ))
#     connection.close()
#     return " [x] Sent: %s" % cmd


if __name__ == '__main__':
    app = RESTApp("0.0.0.0", 8090, "0.0.0.0", 5672)
    app.run()