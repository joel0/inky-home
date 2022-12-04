from homeassistant_api import Client
import yaml

def main() -> None:
    print('Starting Inky Home')

    with open('./config.yaml') as file:
        conf = yaml.safe_load(file)
    print(f'Loaded config: {conf}')

    client = Client(
        conf['homeassistant']['url'],
        conf['homeassistant']['access_token']
    )

    for sensor in conf['display']:
        display_sensor(client, sensor)


def display_sensor(client: Client, sensor) -> None:
    entity = client.get_entity(entity_id=sensor['entity_id'])
    val = entity.state.state
    unit = entity.state.attributes['unit_of_measurement']
    print('%s: %s %s' % (sensor['name'], val, unit))

if __name__ == '__main__':
    main()
