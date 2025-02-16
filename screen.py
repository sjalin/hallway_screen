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
        super().__init__(log_to_file=True)
        self.last_temp_time = ''
        self.last_sl_time = ''
        self.last_smhi_time = ''
        self.outside_temp = None
        self.outside_hum = None
        self.inside_temp = None
        self.inside_hum = None
        self.precipitation = []

        self.departures = []

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
        date_string = '%H:%M:%S %-d/%-m'
        # date_string = '%H:%M:%S %d/%m'  # For testing on windows, does not support "%-d/%-m"
        if msg[0] == 'out-temp':
            self.outside_temp = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime(date_string)
        elif msg[0] == 'out-hum':
            self.outside_hum = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime(date_string)
        elif msg[0] == 'in-temp':
            self.inside_temp = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime(date_string)
        elif msg[0] == 'in-hum':
            self.inside_hum = msg[1]
            self.last_temp_time = datetime.datetime.now().strftime(date_string)
        elif msg[0] == 'buses':
            self.departures = msg[1]
            self.last_sl_time = datetime.datetime.now().strftime(date_string)
        elif msg[0] == 'precipitation':
            self.precipitation = msg[1]
            self.last_smhi_time = datetime.datetime.now().strftime(date_string)

        if self._message_queue.empty():
            self.draw_screen()

    def draw_screen(self):
        self.log.info('Draw new screen')
        image = self.base_image.copy()

        # Temperatures
        ImageDraw.Draw(image).text((10, 10), '    Utomhus:', font=self.font30)
        if self.outside_temp is not None:
            ImageDraw.Draw(image).text((10, 50), f'{str(self.outside_temp).rjust(7)}°C', font=self.font45)
        if self.outside_hum is not None:
            ImageDraw.Draw(image).text((10, 105), f'{str(self.outside_hum).rjust(7)}% ', font=self.font45)
        ImageDraw.Draw(image).text((10, 160), '    Inomhus:', font=self.font30)
        if self.inside_temp is not None:
            ImageDraw.Draw(image).text((10, 200), f'{str(self.inside_temp).rjust(7)}°C', font=self.font45)
        if self.inside_hum is not None:
            ImageDraw.Draw(image).text((10, 255), f'{str(self.inside_hum).rjust(7)}% ', font=self.font45)
        ImageDraw.Draw(image).text((10, 310), f'Uppdaterad: {self.last_temp_time}', font=self.font20)

        # Rain
        ImageDraw.Draw(image).text((10, 340), '  Nederbörd:', font=self.font30)
        if self.precipitation:
            try:
                ImageDraw.Draw(image).text((10, 380), f'{str(self.precipitation[0][0].time())[:-3]} {self.precipitation[0][0].day}/{self.precipitation[0][0].month} - {self.precipitation[0][1]}mm', font=self.font30)
                ImageDraw.Draw(image).text((10, 420), f'{str(self.precipitation[1][0].time())[:-3]} {self.precipitation[1][0].day}/{self.precipitation[1][0].month} - {self.precipitation[1][1]}mm', font=self.font30)
            except IndexError:
                # Easier that looking at the length of the array..........
                pass
        ImageDraw.Draw(image).text((10, 460), f'Uppdaterad: {self.last_smhi_time}', font=self.font20)

        # SL Stuff
        for e, d in enumerate(self.departures):
            ImageDraw.Draw(image).text((self.half_offset + 10, 10 + e*90), f'{d[0]} | {d[2]}\n{"<--" if d[1] else "-->"} | ({d[3]})\n-----------------', font=self.font30)
        ImageDraw.Draw(image).text((self.half_offset + 10, 460), f'Uppdaterad: {self.last_sl_time}', font=self.font20)

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