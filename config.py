import json
import os

DEFAULT_TRACKER_FILENAME = '.ev-tracker'
DEFAULT_TRACKER_PATH = os.path.expanduser(os.path.join('~', DEFAULT_TRACKER_FILENAME))
CONFIG_FILENAME = 'config.json'


class Config(object):
    def __init__(self):
        self.filename = None
        self.generation = 8
        self.is_sun_or_moon = False

    def double_power_items_effort(self):
        return self.is_sun_or_moon

    def smart_iv_cap(self):
        return self.generation > 6

    def berry_reduction_cuts_to_100(self):
        return self.generation == 4

    @classmethod
    def from_json(cls, filename):
        config = cls()
        try:
            fp = open(CONFIG_FILENAME, 'r')
            data = json.load(fp)
            if filename is None and data['filename']:
                config.filename = data['filename']
            elif filename is None:
                config.filename = DEFAULT_TRACKER_PATH
            else:
                config.filename = filename
            if data['generation']:
                config.generation = data['generation']
            if data['is_sun_or_moon']:
                config.is_sun_or_moon = data['is_sun_or_moon']
        except IOError:
            if filename is None:
                config.filename = DEFAULT_TRACKER_PATH
            else:
                config.filename = filename

        return config

    @staticmethod
    def to_json(config):
        fp = open(CONFIG_FILENAME, 'w')
        data = {
            'filename': config.filename,
            'generation': config.generation,
            'is_sun_or_moon': config.is_sun_or_moon,
        }

        json.dump(data, fp)
        fp.close()


instance: Config
