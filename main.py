import datetime
import time
from typing import List, Optional
import yaml
from inky.auto import auto
from inky.inky_uc8159 import Inky # Assumes Inky Impression
from homeassistant_api import Client
from PIL import Image, ImageDraw, ImageFont

FONT = "DejaVuSans.ttf"
FONT_SIZE_UPDATED_AT = 25
FONT_SIZE_SENSOR_NAME = 30
FONT_SIZE_SENSOR_VALUE = 80
MARGIN = (10, 10)

FONT_UPDATED_AT = ImageFont.truetype(FONT, FONT_SIZE_UPDATED_AT)
FONT_SENSOR_NAME = ImageFont.truetype(FONT, FONT_SIZE_SENSOR_NAME)
FONT_SENSOR_VALUE = ImageFont.truetype(FONT, FONT_SIZE_SENSOR_VALUE)

COLOR_UPDATED_AT = 'black'
COLOR_SENSOR_NAME = 'black'
COLOR_SENSOR_VALUE = 'black'

class SensorDefinition:
    def __init__(self, entity_id: str, name: str) -> None:
        self.entity_id = entity_id
        self.name = name

    def read(self, ha_client: Client) -> 'SensorReading':
        entity = ha_client.get_entity(entity_id = self.entity_id)
        val = entity.state.state
        unit = entity.state.attributes['unit_of_measurement']
        return SensorReading(self.name, val, unit)

class SensorReading:
    def __init__(self, name: str, value: str, unit: str) -> None:
        self.name = name
        self.value = value
        self.unit = unit

    def formatted_value(self) -> str:
        return '%s %s' % (self.value, self.unit)

def main() -> None:
    print('Starting Inky Home')

    # Detect Inky display type
    try:
        display = auto()
    except RuntimeError as err:
        if str(err) != 'No EEPROM detected! You must manually initialise your Inky board.':
            raise err
        display = None
        print('No Inky display found')
    else:
        print(f'Found Inky display: {display}')

    # Load config
    with open('./config.yaml') as file:
        conf = yaml.safe_load(file)
    print(f'Loaded config: {conf}')

    client = Client(
        conf['homeassistant']['url'],
        conf['homeassistant']['access_token']
    )

    sensors: List[SensorDefinition] = []
    for sensor in conf['display']:
        sensors.append(SensorDefinition(sensor['entity_id'], sensor['name']))

    main_loop(client, display, sensors)

def main_loop(ha_client: Client, inky_display: Optional[Inky], sensors: List[SensorDefinition]) -> None:
    while True:
        readings: List[SensorReading] = []
        for sensor in sensors:
            try:
                readings.append(sensor.read(ha_client))
            except Exception as ex:
                print('Update error: ' + ex)
        display_readings(readings, inky_display)
        time.sleep(5 * 60)

def format_updated_at(updated_at: datetime.datetime) -> str:
    return 'Updated at: ' + updated_at.strftime('%H:%M')

def display_readings(readings: List[SensorReading], inky_display: Optional[Inky]):
    updated_at = datetime.datetime.now()
    display_readings_stdout(updated_at, readings)
    display_readings_inky(updated_at, readings, inky_display)

def display_readings_stdout(updated_at: datetime.datetime, readings: List[SensorReading]):
    print(format_updated_at(updated_at))
    for reading in readings:
        print('%s: %s %s' % (reading.name, reading.value, reading.unit))

def display_readings_inky(updated_at: datetime.datetime, readings: List[SensorReading], inky_display: Optional[Inky]):
    if inky_display is None:
        return
    str_updated = format_updated_at(updated_at)

    img = Image.new('RGB', inky_display.resolution, 'white')
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), str_updated, FONT_UPDATED_AT)
    offset = (MARGIN[0], img.height - MARGIN[1] - bbox[3])
    draw.text(offset, str_updated, COLOR_UPDATED_AT, FONT_UPDATED_AT)

    offset = MARGIN
    for reading in readings:
        draw.text(offset, reading.name, COLOR_SENSOR_NAME, FONT_SENSOR_NAME)
        offset = (offset[0], draw.textbbox(offset, reading.name, FONT_SENSOR_NAME)[3])
        draw.text(offset, reading.formatted_value(), COLOR_SENSOR_VALUE, FONT_SENSOR_VALUE)
        offset = (offset[0], draw.textbbox(offset, reading.formatted_value(), FONT_SENSOR_VALUE)[3])

    inky_display.set_image(img)
    inky_display.show(busy_wait=False)

if __name__ == '__main__':
    main()
