import inspect
import os
import pkgutil

import yaml
import re

from importlib import import_module
from io import StringIO

re_include = re.compile(r'^#%include%\s*(.*?)\s*$', re.MULTILINE)


class ClassLoader(object):
    def __init__(self, name=None):
        self._classes = {}
        self.name = name or __name__

        loader = pkgutil.get_loader(self.name)
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
            module_name = '{}.{}'.format(self.name, name)
            module = import_module(module_name)
            for cls_name, cls in inspect.getmembers(module, inspect.isclass):
                if startswith is not None:
                    if not cls_name.startswith(startswith):
                        continue
                class_id = getattr(cls, '__id__', None)
                if class_id:
                    self._classes.setdefault(class_id, cls)


class YamlLoader(yaml.Loader):
    def __init__(self, stream):
        try:
            self._root = os.path.split(stream.name)[0]
        except AttributeError:
            self._root = os.path.curdir
        super().__init__(self._load(stream.name))

    def _load(self, filename):
        tree = self._build_tree(filename)
        files = self._compact_tree(tree)
        data = self._load_yaml_files(files)
        return data

    def _parse_file(self, filename):
        if not os.path.exists(filename):
            return []

        with open(filename) as f:
            subimports = []
            for name in re.findall(re_include, f.read()):
                subimports.append(name)

        return subimports

    def _build_tree(self, filename, tree=None, level=0):
        if tree is None:
            tree = {}

        tree.setdefault(level, []).append(filename)
        for x in self._parse_file(filename):
            self._build_tree(x, tree, level + 1)

        return tree

    def _compact_tree(self, tree):
        compacted = []
        for x in reversed(sorted(tree)):
            for name in tree[x]:
                if name not in compacted:
                    compacted.append(name)
        return compacted

    def _load_yaml_files(self, files):
        stream = StringIO()
        for filename in files:
            if os.path.exists(filename):
                stream.write('### {} ###\n'.format(filename))
                stream.write(open(filename).read())
        return stream.getvalue()
