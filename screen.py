import os
import numpy as np
import requests
import datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import config
from threadwithqueue.threadwithqueue import ThreadWithQueue

# Available displays https://github.com/robweber/omni-epd#displays-implemented
DISPLAY = 'waveshare_epd.epd7in5_V2'

if not config.DEBUG:
    from omni_epd import displayfactory, EPDNotFoundError

MIRACODE_FONT_NAME = 'Miracode.ttf'
MIRACODE_URL = f'https://github.com/IdreesInc/Miracode/releases/download/v1.0/{MIRACODE_FONT_NAME}'


class Screen(ThreadWithQueue):
    def __init__(self):
        super().__init__()
        self.last_temp_time = '99:99:99'
        self.last_sl_time = '99:99:99'
        self.outside_temp = -77.7
        self.outside_hum = 1337
        self.inside_temp = -77.7
        self.inside_hum = 1337

        self.departures = [(555, True, '17:43:32', '17:44:44'),
                           (535, False, '17:50:32', '17:50:44'),
                           (555, True, '18:43:32', '18:44:44'),
                           (555, True, '19:43:32', '19:44:44'),
                           (555, True, '23:43:32', '23:44:44'), ]

        self.width = config.DEBUG_WIDTH
        self.height = config.DEBUG_HEIGHT
        self.half_offset = config.DEBUG_HALF_OFFSET

        self._ensure_font_exist(MIRACODE_FONT_NAME, MIRACODE_URL)

        self.font20 = ImageFont.truetype(rf'./{MIRACODE_FONT_NAME}', 20)
        self.font30 = ImageFont.truetype(rf'./{MIRACODE_FONT_NAME}', 30)
        self.font45 = ImageFont.truetype(rf'./{MIRACODE_FONT_NAME}', 45)
        self.font60 = ImageFont.truetype(rf'./{MIRACODE_FONT_NAME}', 60)
        arr = [[1 for x in range(self.width)] for y in range(self.height)]
        arr = (np.asarray(arr) * 255).astype(np.uint8)
        self.base_image = Image.fromarray(arr)

        if not config.DEBUG:
            try:
                self.display = displayfactory.load_display_driver(DISPLAY)
            except EPDNotFoundError as e:
                raise EPDNotFoundError(f'{e} ---- {DISPLAY}')
            width = self.display.width
            height = self.display.height
            self.display.prepare()
            self.display.clear()
            self.display.sleep()

    def _download_font(self, filename, url):
        self.log.info(f'Downloading font {filename} ({url})')
        with open(filename, 'wb') as fout:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # Write response data to file
            for block in response.iter_content(4096):
                fout.write(block)

    def _ensure_font_exist(self, filename, url):
        if not os.path.exists(filename):
            self._download_font(filename, url)

    def _handle_message(self, msg):
        if msg[0] == 'out-temp':
            self.outside_temp = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime('%H:%M:%S')
        elif msg[0] == 'out-hum':
            self.outside_hum = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime('%H:%M:%S')
        elif msg[0] == 'in-temp':
            self.inside_temp = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime('%H:%M:%S')
        elif msg[0] == 'in-hum':
            self.inside_hum = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime('%H:%M:%S')
        elif msg[0] == 'buses':
            self.departures = msg[1]
            self.last_sl_time = datetime.datetime.now().strftime('%H:%M:%S')

        if self._message_queue.empty():
            self.draw_screen()

    def draw_screen(self):
        self.log.info('Draw new screen')
        image = self.base_image.copy()
        # Temperatures
        ImageDraw.Draw(image).text((10, 10), '    Utomhus:', font=self.font30)
        ImageDraw.Draw(image).text((10, 50), f'{str(self.outside_temp).rjust(5)}°C', font=self.font60)
        ImageDraw.Draw(image).text((10, 120), f'{str(self.outside_hum).rjust(5)}% ', font=self.font60)
        ImageDraw.Draw(image).text((10, 190), '     Regn:', font=self.font30)
        ImageDraw.Draw(image).text((10, 230), '77mm @ 13:37', font=self.font45)
        ImageDraw.Draw(image).text((10, 285), '    Inomhus:', font=self.font30)
        ImageDraw.Draw(image).text((10, 325), f'{str(self.inside_temp).rjust(5)}°C', font=self.font60)
        ImageDraw.Draw(image).text((10, 395), f'{str(self.inside_hum).rjust(5)}% ', font=self.font60)

        ImageDraw.Draw(image).text((10, 450), f'Last update: {self.last_temp_time}', font=self.font20)
        ImageDraw.Draw(image).text((self.half_offset + 10, 450), f'Last update: {self.last_sl_time}', font=self.font20)


        # SL Stuff
        for e, d in enumerate(self.departures):
            ImageDraw.Draw(image).text((self.half_offset + 10, 10 + e*90), f'{d[0]} |  {d[2]}\n {"X" if d[1] else " "}  | ({d[3]})\n-----------------', font=self.font30)
        # Save the image as BMP
        image = image.convert("1")
        if config.DEBUG:
            image.show()
        else:
            self.log.info('Prepare')
            self.display.prepare()
            self.log.info('clear')
            self.display.clear()
            self.log.info('display')
            self.display.display(image)
            self.log.info('sleep')
            self.display.sleep()