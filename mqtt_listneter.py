import socket
import time
from queue import SimpleQueue

import paho.mqtt.subscribe as subscribe
import config

from threadwithqueue.threadwithqueue import ThreadWithQueue

report_queue = None
log = None


class MQTTListener(ThreadWithQueue):
    def __init__(self, r_queue: SimpleQueue):
        super().__init__()
        global report_queue
        report_queue = r_queue
        global log
        log = self.log

    def run(self):
        # Todo: Rewrite this so tht it is not blocking and stuff
        while True:
            try:
                subscribe.callback(self.report_temp, config.SENSOR_TOPICS,
                                   hostname=config.MQTT_IP,
                                   userdata={"message_count": 0})
                break
            except (TimeoutError, socket.timeout) as e:
                self.log.warning(e)
            time.sleep(10)

    @staticmethod
    def report_temp(client, userdata, message):
        global report_queue
        log.info("New MQTT update: %s %s" % (message.topic, message.payload))
        if message.topic == config.SENSOR_TOPICS[0][0]:
            report_queue.put(('out-temp', message.payload.decode('UTF-8')))
        elif message.topic == config.SENSOR_TOPICS[1][0]:
            report_queue.put(('out-hum', message.payload.decode('UTF-8')))
        elif message.topic == config.SENSOR_TOPICS[2][0]:
            report_queue.put(('in-temp', message.payload.decode('UTF-8')))
        elif message.topic == config.SENSOR_TOPICS[3][0]:
            report_queue.put(('in-hum', message.payload.decode('UTF-8')))
