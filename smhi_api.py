import datetime
import time
from queue import SimpleQueue

import dateutil
import requests

import config
from threadwithqueue.threadwithqueue import ThreadWithQueue


class SMHIApi(ThreadWithQueue):
    def __init__(self, r_queue: SimpleQueue):
        super().__init__()
        self.report_queue = r_queue

        self.timewindow = 60
        self.next_check = 0
        self.precipitation_list = []
        print('SMHI init')

    def run(self):
        print('SMHI run')
        self.log.info(f'Run')
        while True:
            msg = self._get_message()
            if msg:
                if msg[0] == 'DIE':
                    self.log.info(f'Stopping')
                    break
                else:
                    self._handle_message(msg)
            self.get_data()
            time.sleep(10)  # TODO: Change to 10 minutes

    def _handle_message(self, msg):
        if msg[0] == 'Poll':
            self.get_data()

    def get_data(self):
        url = f'https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{config.LONG}/lat/{config.LAT}/data.json'

        r = requests.get(url=url)
        data = r.json()
        data = data['timeSeries']
        self.log.debug(f'Len(data): {len(data)}')
        precipitation_list = []
        for x in data:
            pmean = 0
            pcat = 0
            par = x['parameters']
            for p in par:
                if p['name'] == 'pmean':
                    pmean = p['values'][0]
                if p['name'] == 'pcat':
                    pcat = p['values'][0]
            if pmean:
                now = datetime.datetime.now()
                self.log.debug(f'Now: {now}')
                self.log.debug(f'x[validTime]: {x["validTime"]}')
                dt = dateutil.parser.parse(x['validTime'])
                self.log.debug(f'dt: {dt}')
                zone = 'Europe/Stockholm'
                dt_zone = dt.astimezone(dateutil.tz.gettz(zone))
                self.log.debug(f'dtZone: {dt_zone}')
                self.log.debug(f'pmean: {pmean}')
                self.log.debug(f'pcat: {pcat}')
                precipitation_list.append([dt_zone, pmean, pcat])
            if len(precipitation_list) >= 3:
                break
        self.log.debug(precipitation_list)
        if self.precipitation_list != precipitation_list:
            self.precipitation_list = precipitation_list
            self.report_queue.put(('precipitation', self.precipitation_list))
