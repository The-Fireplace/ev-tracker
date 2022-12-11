import json
import os

DEFAULT_TRACKER_FILENAME = '.ev-tracker'
DEFAULT_TRACKER_PATH = os.path.expanduser(os.path.join('~', DEFAULT_TRACKER_FILENAME))
CONFIG_FILENAME = 'config.json'


class Config(object):
    def __init__(self):
        self.filename = None
        self.generation = 9
        self.is_bdsp = False

    def double_power_items_effort(self):
        return self.generation > 6 and not self.is_bdsp

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
            if filename is None and 'filename' in data:
                config.filename = data['filename']
            elif filename is None:
                config.filename = DEFAULT_TRACKER_PATH
            else:
                config.filename = filename
            if 'generation' in data:
                config.generation = data['generation']
            if 'is_bdsp' in data:
                config.is_bdsp = data['is_bdsp']
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
            'is_bdsp': config.is_bdsp,
        }

        json.dump(data, fp)
        fp.close()


instance: Config
