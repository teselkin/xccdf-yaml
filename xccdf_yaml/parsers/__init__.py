import inspect
import os
import pkgutil

from importlib import import_module


class GenericParser(object):
    def __init__(self):
        pass

    @classmethod
    def name(cls):
        return cls.__id__


class ClassLoader(object):
    def __init__(self):
        self._classes = {}

        loader = pkgutil.get_loader(__name__)
        try:
            self.module_dir = loader.path
        except AttributeError:
            self.module_dir = loader.filename

        if os.path.isfile(self.module_dir):
            self.module_dir = os.path.dirname(self.module_dir)

    def __iter__(self):
        for _, cls in self._classes.items():
            yield cls

    def __getattr__(self, item):
        return self._classes.get(item)

    def get(self, item):
        return self._classes.get(item)

    def load(self, startswith=None):
        for (loader, name, ispkg) in pkgutil.iter_modules([self.module_dir]):
            module_name = '{}.{}'.format(__name__, name)
            module = import_module(module_name)
            for cls_name, cls in inspect.getmembers(module, inspect.isclass):
                if startswith is not None:
                    if not cls_name.startswith(startswith):
                        continue
                class_id = getattr(cls, '__id__', None)
                if class_id:
                    self._classes.setdefault(class_id, cls)


PARSERS = ClassLoader()
PARSERS.load(startswith='YamlParser')
