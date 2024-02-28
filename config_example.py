# MQTT config
MQTT_IP = '192.168.3.236'
SENSOR_TOPICS = [('homie/homey/temp-sensor-garden/measure-temperature', 1),         # Outside temp topic
                 ('homie/homey/temp-sensor-garden/measure-humidity', 1),            # Outside humidity topic
                 ('homie/homey/temp-sensor-living-room/measure-temperature', 1),    # Inside temp topic
                 ('homie/homey/temp-sensor-living-room/measure-humidity', 1)]       # Inside humidity topic

# SL config
API_KEY = '123FART321COWABONGA' # Fill in your own API-key

# SMHI config
LAT = 17.886781
LONG = 59.322097

# Debug = not running on e-ink-display
DEBUG = False
DEBUG_WIDTH = 800
DEBUG_HEIGHT = 480
DEBUG_HALF_OFFSET = DEBUG_WIDTH / 2

