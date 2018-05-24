import datetime

from xccdf_yaml.xml import XmlCommon

NSMAP = {
    None: "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    'oval-common': "http://oval.mitre.org/XMLSchema/oval-common-5",
    'oval-def-indep': "http://oval.mitre.org/XMLSchema/oval-definitions-5#independent",
    'oval-def-linux': "http://oval.mitre.org/XMLSchema/oval-definitions-5#linux",
    'oval-def-unix': "http://oval.mitre.org/XMLSchema/oval-definitions-5#unix",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns, nsmap=NSMAP)


class OvalDefinitions(XmlBase):
    __elements_order__ = (
        'generator',
        'definitions',
        'tests',
        'objects',
        'states',
    )

    def __init__(self):
        super().__init__('oval_definitions')
        generator = Generator()
        self.append(generator)

        self._definitions = []
        self._tests = []
        self._objects = []
        self._states = []

    def add_definition(self, id):
        definition = Definition(id)
        self._definitions.append(definition)
        return definition

    def add_test(self, name, ns=None):
        instance = OvalTest(name, ns)
        self._tests.append(instance)
        return instance

    def add_object(self, id, name, ns=None):
        instance = OvalObject(id, name, ns)
        self._objects.append(instance)
        return instance

    def add_state(self, id, name, ns=None):
        instance = OvalState(id, name, ns)
        self._states.append(instance)
        return instance

    def update_elements(self):
        self.remove_elements(name='definitions')
        definitions = self.sub_element('definitions')
        for x in self._definitions:
            definitions.append(x)

        self.remove_elements(name='tests')
        tests = self.sub_element('tests')
        for x in self._tests:
            tests.append(x)

        self.remove_elements(name='objects')
        objects  = self.sub_element('objects')
        for x in self._objects:
            objects.append(x)

        self.remove_elements(name='states')
        states = self.sub_element('states')
        for x in self._states:
            states.append(x)


class Generator(XmlBase):
    def __init__(self):
        super().__init__('generator')

        self.sub_element('product_name', ns='oval-common')\
            .set_text('xccdf_yaml generator')
        self.sub_element('product_version', ns='oval-common').set_text('0.1')
        self.sub_element('schema_version', ns='oval-common').set_text('5.11')
        self.sub_element('timestamp', ns='oval-common')\
            .set_text(str(datetime.datetime.now()))


class Definition(XmlBase):
    def __init__(self, id, version='1', class_name='compliance'):
        super().__init__('definition')
        self.set_attr('id', id)
        self._metadata = None
        self._criteria = []

    def add_metadata(self):
        metadata = Metadata()
        self._metadata = metadata
        return metadata

    def add_criteria(self, operator='OR'):
        criteria = Criteria(operator=operator)
        self._criteria.append(criteria)
        return criteria

    def update_elements(self):
        self.remove_elements(name='metadata')
        if self._metadata:
            self.append(self._metadata)

        self.remove_elements(name='criteria')
        for x in self._criteria:
            self.append(x)


class Metadata(XmlBase):
    def __init__(self):
        super().__init__('metadata')

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def set_affected(self, family, platform):
        affected = None
        for affected in self.elements('affected'):
            if affected.get_attr('family') == family:
                for x in affected.elements('platform'):
                    if x._text == platform:
                        return self
                break

        if affected is None:
            affected = self.sub_element('affected').set_attr('family', family)

        affected.sub_element('platform').set_text(platform)
        return self


class Criteria(XmlBase):
    def __init__(self, operator='OR'):
        super().__init__('criteria')
        self.set_attr('operator', operator)
        self._criterion = []

    def add_criterion(self, instance):
        self._criterion.append(instance)
        return instance

    def new_criterion(self, test_ref):
        criterion = Criterion(test_ref=test_ref)
        self._criterion.append(criterion)
        return criterion

    def update_elements(self):
        self.remove_elements(name='criterion')
        for x in self._criterion:
            self.append(x)


class Criterion(XmlBase):
    def __init__(self, test_ref):
        super().__init__('criterion')
        self.set_attr('test_ref', test_ref)


class OvalTest(XmlBase):
    def __init__(self, id, name, ns=None):
        super().__init__(name, ns=ns)
        self.set_attr('id', id)
        self._objects = set()
        self._states = set()

    def add_object(self, instance):
        print(repr(instance))
        self._objects.add(instance)

    def add_state(self, instance):
        self._states.add(instance)

    def update_elements(self):
        self.remove_elements(name='object')
        for x in self._objects:
            self.sub_element('object')\
                .set_attr('object_ref', x.get_attr('id'))

        self.remove_elements(name='state')
        for x in self._states:
            self.sub_element('state')\
                .set_attr('state_ref', x.get_attr('id'))


class OvalObject(XmlBase):
    def __init__(self, id, name, ns=None):
        super().__init__(name, ns=ns)
        self.set_attr('id', id)


class OvalState(XmlBase):
    def __init__(self, id, name, ns=None):
        super().__init__(name, ns=ns)
        self.set_attr('id', id)
