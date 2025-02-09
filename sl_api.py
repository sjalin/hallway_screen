import logging
import time
from json import JSONDecodeError
from queue import SimpleQueue

import requests

import config
from threadwithqueue.threadwithqueue import ThreadWithQueue


class SlApi(ThreadWithQueue):
    def __init__(self, r_queue: SimpleQueue):
        super().__init__(log_to_file=True)
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
                if self.next_departure == 0:
                    self.next_check = now + 600
                elif self.next_departure - now < 300:
                    self.next_check = now + 60
                else:
                    self.next_check = self.next_departure - 290
                self.log.info(f'Next check in  {int(self.next_check - now)}')
            time.sleep(30)

    def _handle_message(self, msg):
        if msg[0] == 'Poll':
            self.get_data()

    def get_data(self):
        self.log.info('Get new data from SL')
        URL = f'https://transport.integration.sl.se/v1/sites/{config.SITE_ID}/departures?transport=BUS&forecast={config.TIME_WINDOW}'
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
            for b in data['departures']:
                if b['destination'] == config.DESTINATION:
                    if not self.next_departure:
                        self.next_departure = time.mktime(time.strptime(b['expected'], '%Y-%m-%dT%H:%M:%S'))
                        self.log.info(f'New next departure {self.next_departure} ({time.time()})')
                    buses.append((b['line']['designation'],
                                  b['direction_code'] == 1,
                                  b['scheduled'].split('T')[1],
                                  b['expected'].split('T')[1]))
                    if len(buses) >= 5:
                        break
        except KeyError as e:
            self.log.warning(e)
            return

        self.log.info(f'Next departure in {int(self.next_departure - time.time())}s')
        if self.last_buses != buses:
            if not self.next_departure:
                self.next_departure = time.time() + 60 * 1
                self.log.warning(f'No departures {data["departures"]}')
            self.report_queue.put(('buses', buses))
        self.log.info(buses)
        self.last_buses = buses
