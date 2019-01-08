from xccdf_yaml.common import SharedFiles


class GenericParser(object):
    def __init__(self, generator, benchmark, parsed_args=None,
                 shared_files=None):
        self.generator = generator
        self.benchmark = benchmark
        self.parsed_args = parsed_args
        self.shared_files = shared_files

    @property
    def xccdf(self):
        return self.benchmark.xccdf

    @classmethod
    def name(cls):
        return cls.__id__

    @classmethod
    def about(cls):
        return ''

    def add_shared_file(self, filename, content=None):
        return self.shared_files.new(name=filename, content=content)

    def parse(self, id, metadata):
        result = ParsedObjects(self.xccdf)

        rule = result.new_rule(id)

        if 'title' in metadata:
            rule.set_title(metadata['title'])

        if 'description' in metadata:
            rule.set_description(metadata['description'])

        if 'rationale' in metadata:
            rule.set_rationale(metadata['rationale'])

        for ident_name, ident_system in metadata.get('ident', {}).items():
            rule.add_ident(ident_name, ident_system)

        for reference in metadata.get('reference', []):
            if isinstance(reference, dict):
                rule.add_reference(reference['text'],
                                   href=reference.get('url'))
            else:
                rule.add_reference(reference)

        for reference in metadata.get('dc-reference', []):
            ref = rule.add_dc_reference()
            for element_name, element_value in reference.items():
                if element_name == 'href':
                    ref.set_attr('href', element_value)
                else:
                    ref.sub_element(element_name).set_text(element_value)

        return result


class ParsedObjects(object):
    def __init__(self, xccdf):
        self.xccdf = xccdf
        self.definition = None
        self.rule = None
        self.objects = []
        self.states = []
        self.tests = []
        self._shared_files = SharedFiles()
        self._entrypoints = set()
        self.variable = None

    def new_rule(self, id):
        self.rule = self.xccdf.rule(id)
        return self.rule

    def add_shared_file(self, filename, content=None):
        return self._shared_files.new(name=filename, content=content)

    def add_entrypoint(self, filename):
        self._entrypoints.add(filename)

    @property
    def entrypoints(self):
        return self._entrypoints

    @property
    def has_oval_data(self):
        return any([self.definition, self.states, self.states, self.tests])

    @property
    def has_variable(self):
        return True if self.variable else False
