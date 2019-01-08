import os

from threading import local


class AppData(local):
    def __init__(self):
        self._ = {
            'workdir': os.getcwd(),
        }

    def __getitem__(self, item):
        return self._[item]

    def __setitem__(self, key, value):
        self._[key] = value


APPDATA = AppData()
