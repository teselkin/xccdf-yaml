
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

    def add_shared_file(self, filename, content):
        if filename in self._shared_files:
            if self._shared_files[filename].get('content') != content:
                raise Exception("Attempt to overwrite shared file '{}'"
                                " with different content".format(filename))
        else:
            self._shared_files[filename] = {
                'content': content,
            }

    def add_entrypoint(self, filename):
        self._entrypoints.add(filename)

    @property
    def entrypoints(self):
        return self._entrypoints

    @property
    def shared_files(self):
        return self._shared_files.items()

    @property
    def has_oval_data(self):
        return any([self.definition, self.states, self.states, self.tests])

    @property
    def has_variable(self):
        return True if self.variable else False
