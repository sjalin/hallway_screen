import datetime
import time
from queue import SimpleQueue

import dateutil
import requests

import config
from threadwithqueue.threadwithqueue import ThreadWithQueue


class SMHIApi(ThreadWithQueue):
    def __init__(self, r_queue: SimpleQueue):
        super().__init__(log_to_file=True)
        self.report_queue = r_queue

        self.timewindow = 60
        self.next_check = 0
        self.precipitation_list = []

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
            self.get_data()
            time.sleep(10 * 60)

    def _handle_message(self, msg):
        if msg[0] == 'Poll':
            self.get_data()

    def get_data(self):
        rain_max = 'precipitation_amount_max'
        rain_min = 'precipitation_amount_min'
        rain_type = 'predominant_precipitation_type_at_surface'
        url = f'https://opendata-download-metfcst.smhi.se/api/category/snow1g/version/1/geotype/point/lon/{config.LONG}/lat/{config.LAT}/data.json?parameters={rain_max},{rain_min},{rain_type}'

        try:
            r = requests.get(url=url)
        except requests.exceptions.ConnectionError:
            time.sleep(30 * 60)
            return

        data = r.json()
        data = data['timeSeries']
        precipitation_list = []
        for x in data:
            rmin = x['data'][rain_min]
            rmax = x['data'][rain_max]
            pcat = x['data'][rain_type]

            if rmax:
                dt = dateutil.parser.parse(x['time'])
                precipitation_list.append([dt, rmin, rmax, pcat])
            if len(precipitation_list) >= 3:
                break

        if self.precipitation_list != precipitation_list:
            self.precipitation_list = precipitation_list
            self.report_queue.put(('precipitation', self.precipitation_list))
