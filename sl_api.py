import logging
import time
from json import JSONDecodeError
from queue import SimpleQueue

import requests

import config
from threadwithqueue.threadwithqueue import ThreadWithQueue


class SlApi(ThreadWithQueue):
    def __init__(self, r_queue: SimpleQueue):
        super().__init__()
        self.last_buses = None
        self.report_queue = r_queue

        self.site_id = 5761
        self.timewindow = 60
        # self._message_queue.put(('Poll', None))
        self.next_check = 0
        self.next_departure = None

    def run(self):
        self.log.info(f'Run')
        while True:
            msg = self._get_message()
            if msg:
                if msg[0] == 'DIE':
                    self.log.info(f'Stopping')
                    break
                else:
                    self._handle_message(msg)
            if self.next_check < time.time():
                self.get_data()
                now = time.time()
                if self.next_departure - now < 300:
                    self.next_check = now + 60
                else:
                    self.next_check = self.next_departure - 300
                self.log.info(f'Next check in  {int(self.next_check - now)}')
            time.sleep(30)

    def _handle_message(self, msg):
        if msg[0] == 'Poll':
            self.get_data()

    def get_new_data(self):
        URL = f'https://transport.integration.sl.se/v1/sites/{9192}/departures'

        URL = f'https://transport.integration.sl.se/v1/sites/5761/departures?transport=BUS&forecast=60'
        r = requests.get(url=URL)
        data = r.json()

        buses = []
        for b in data['ResponseData']['Buses']:
            if b['Destination'] == 'Kallhälls station':
                buses.append((b['LineNumber'],
                              b['JourneyDirection'] == 2,
                              b['TimeTabledDateTime'].split('T')[1],
                              b['ExpectedDateTime'].split('T')[1]))
        self.report_queue.put(('buses', buses))

    def get_data(self):
        self.log.info('Get new data from SL')
        URL = f'https://api.sl.se/api2/realtimedeparturesV4.json?key={config.API_KEY}&siteid={self.site_id}&timewindow={self.timewindow}'
        self.next_departure = 0

        try:
            r = requests.get(url=URL)
        except requests.exceptions.ConnectionError as e:
            self.log.warning(e)
            return

        try:
            data = r.json()
        except JSONDecodeError as e:
            logging.warning(e)

        buses = []
        try:
            for b in data['ResponseData']['Buses']:
                if b['Destination'] == 'Kallhälls station':
                    if not self.next_departure:
                        self.next_departure = time.mktime(time.strptime(b['ExpectedDateTime'], '%Y-%m-%dT%H:%M:%S'))
                        self.log.info(f'New next departure {self.next_departure} ({time.time()})')
                    buses.append((b['LineNumber'],
                                  b['JourneyDirection'] == 1,
                                  b['TimeTabledDateTime'].split('T')[1],
                                  b['ExpectedDateTime'].split('T')[1]))
        except KeyError as e:
            self.log.warning(e)
            return

        self.log.info(f'Next departure in {int(self.next_departure - time.time())}s')
        if self.last_buses != buses:
            if not self.next_departure:
                self.next_departure = time.time() + 60 * 1
                self.log.warning(f'No departures {data["ResponseData"]["Buses"]}')
            self.report_queue.put(('buses', buses))
        self.log.info(buses)
        self.last_buses = buses
