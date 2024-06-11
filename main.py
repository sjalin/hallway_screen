import screen
import mqtt_listneter
import sl_api
import smhi_api
import logging


def main():
    print('Start')
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
        level=logging.WARNING,
        datefmt='%Y-%m-%d %H:%M:%S')

    log = logging.getLogger('main')
    log.info('Making threads')

    scr = screen.Screen()
    mqtt = mqtt_listneter.MQTTListener(scr.get_message_queue())
    slapi = sl_api.SlApi(scr.get_message_queue())
    smhiapi = smhi_api.SMHIApi(scr.get_message_queue())
    log.info('Staring threads')
    mqtt.start()
    slapi.start()
    smhiapi.start()
    scr.start()
    log.info('Startup done')


if __name__ == '__main__':
    main()
