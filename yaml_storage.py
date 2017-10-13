import yaml
import sys
from tinydb.database import Document
from tinydb.storages import Storage, touch

def represent_doc(dumper, data):
    # Represent `Document` objects as their dict's string representation
    # which PyYAML understands
    return dumper.represent_data(dict(data))

yaml.add_representer(Document, represent_doc)

class YAMLStorage(Storage):
    def __init__(self, filename):
        self.filename = filename
        touch(filename, False)

    def read(self):
        with open(self.filename) as handle:
            data = yaml.safe_load(handle.read())
            return data

    def write(self, data):
        with open(self.filename, 'w') as handle:
            yaml.dump(data, handle)

    def close(self):
        pass
