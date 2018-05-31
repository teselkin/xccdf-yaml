import os
import re
import yaml

from io import StringIO

re_include = re.compile(r'^#%include%\s*(.*?)\s*$', re.MULTILINE)


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

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))

        with open(filename, 'r') as f:
            return yaml.load(f, YamlLoader)


YamlLoader.add_constructor('!include', YamlLoader.include)
