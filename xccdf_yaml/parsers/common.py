import os
import shutil
import stat


class GenericParser(object):
    def __init__(self, benchmark, parsed_args=None, output_dir=None):
        self.benchmark = benchmark
        self.parsed_args = parsed_args
        self.output_dir = output_dir or parsed_args.output_dir

    @property
    def xccdf(self):
        return self.benchmark.xccdf

    @classmethod
    def name(cls):
        return cls.__id__

    @classmethod
    def about(cls):
        return ''


class SharedFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.source = None
        self.content = None
        self._executable = False

    def __eq__(self, other):
        return self.source == other.source and self.content == other.content

    def set_executable(self, executable=True):
        self._executable = executable == True

    def export(self, source_dir, output_dir):
        target = os.path.join(output_dir, os.path.basename(self.filename))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if self.content:
            with open(target, 'w') as f:
                f.write(self.content)
        else:
            source = os.path.join(source_dir, self.filename)
            if os.path.exists(source):
                shutil.copyfile(source, target)

        if os.path.exists(target):
            if self._executable:
                x = os.stat(target)
                os.chmod(target, x.st_mode | stat.S_IEXEC)


class ParsedObjects(object):
    def __init__(self, xccdf):
        self.xccdf = xccdf
        self.definition = None
        self.rule = None
        self.objects = []
        self.states = []
        self.tests = []
        self._shared_files = {}
        self._entrypoints = set()
        self.variable = None

    def new_rule(self, id):
        # self.rule = XccdfRule(id)
        self.rule = self.xccdf.rule(id)
        return self.rule

    def add_shared_file(self, filename, content=None):
        shared_file = SharedFile(filename)
        if content:
            shared_file.content = content
        if filename in self._shared_files:
            if shared_file != self._shared_files[filename]:
                raise Exception("Attempt to overwrite shared file '{}'"
                                " with different content".format(filename))
        else:
            self._shared_files[filename] = shared_file
        return shared_file

    def add_entrypoint(self, filename):
        self._entrypoints.add(filename)

    @property
    def entrypoints(self):
        return self._entrypoints

    @property
    def shared_files(self):
        return self._shared_files.values()

    @property
    def has_oval_data(self):
        return any([self.definition, self.states, self.states, self.tests])

    @property
    def has_variable(self):
        return True if self.variable else False
