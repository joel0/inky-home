from inky.auto import auto
from homeassistant_api import Client
import yaml
import time
import datetime

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

    main_loop(client, conf)

def main_loop(ha_client, conf) -> None:
    while True:
        print()
        for sensor in conf['display']:
            try:
                display_sensor(ha_client, sensor)
            except Exception as ex:
                print('Update error: ' + ex)
        display_now()
        time.sleep(5 * 60)

def display_sensor(client: Client, sensor) -> None:
    entity = client.get_entity(entity_id=sensor['entity_id'])
    val = entity.state.state
    unit = entity.state.attributes['unit_of_measurement']
    print('%s: %s %s' % (sensor['name'], val, unit))

def display_now() -> None:
    now = datetime.datetime.now()
    print('Updated at: ' + now.strftime('%H:%M'))

if __name__ == '__main__':
    main()
