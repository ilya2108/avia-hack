#! /usr/bin/env python3

import json
import pika
import time
import logging
from collections import namedtuple
import requests as req
import model
logging.basicConfig(level=logging.INFO)

ResponseRMQ = namedtuple('ResponseRMQ', ['key', 'in_file'])
RequestDB = namedtuple('RequestDB', ['key', 'status', 'out_file'])

class RMQHandler:
    def __init__(self, appPort, dbhPort, data_handler):
        self.host = "broker"
        self.appPort = appPort
        self.dbHost = "db_handler"
        self.dbhPort = dbhPort
        self.data_handler = data_handler
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.appPort))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='task_queue', durable=True)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='task_queue', on_message_callback=self.callback, auto_ack=True)
    
    def start(self):
        logging.info(" [*] Waiting for messages. To exit press CTRL+C")
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        cmd = body.decode("utf-8")
        try:
            # logging.info(" [x] Received %r" % cmd)
            cmd_dict = json.loads(cmd)
            response = ResponseRMQ(**cmd_dict)

        except json.decoder.JSONDecodeError as e:
            logging.error("Invalid JSON received from RMQ: %s" % cmd)
            return
        except TypeError:
            logging.error("Error occured while getting data from JSON")
            return
        else:
            output = self.data_handler(response.in_file)
            request = RequestDB(key=response.key, status="done", out_file=output)
            d = request._asdict()
            post = {"params": {key: d[key] for key in d.keys()
                        & {'key', 'status'}}, "data": d['out_file']}
            r = req.post("http://{}:{}/api/tasks/update".format(self.dbHost, self.dbhPort), **post)
            logging.info(" [x] Done")

def data_handler(data):
    logging.info("[x] Received data")
    try:
        ret = {}
        model_out = model.plan_to_zagr(data)
        print(model_out)
        for key, value in enumerate(model_out):
            value.reset_index(inplace=True)
            ret[str(key)] = value.to_json()
        model_out = json.dumps(ret)
    except Exception as e:
        logging.error("Error occured while processing data: %s" % e)
        return "Error occured while processing data"
    return model_out

if __name__ == "__main__":
    node = RMQHandler(appPort=5672, dbhPort=8070, data_handler=data_handler)
    node.start()
