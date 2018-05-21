import lxml.etree as etree
import datetime

from xccdf_yaml.xml import XmlCommon


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        nsmap = {
            None: "http://oval.mitre.org/XMLSchema/oval-definitions-5",
            'oval-common': "http://oval.mitre.org/XMLSchema/oval-common-5",
            'oval-def-indep': "http://oval.mitre.org/XMLSchema/oval-definitions-5#independent",
            'oval-def-linux': "http://oval.mitre.org/XMLSchema/oval-definitions-5#linux",
            'oval-def-unix': "http://oval.mitre.org/XMLSchema/oval-definitions-5#unix",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        }
        super().__init__(name, ns=ns, nsmap=nsmap)


class OvalDefinitions(XmlBase):
    def __init__(self):
        super().__init__('oval_definitions')
        generator = Generator()
        self.append(generator)

        self.definitions = self.sub_element('definitions')
        self.tests = self.sub_element('tests')
        self.objects = self.sub_element('objects')
        self.states = self.sub_element('states')

    def add_definition(self, id):
        definition = Definition(id)
        self.definitions.append(definition)
        return definition

    def add_test(self, name, ns=None):
        instance = OvalTest(name, ns)
        self.tests.append(instance)
        return instance

    def add_object(self, name, ns=None):
        instance = OvalObject(name, ns)
        self.objects.append(instance)
        return instance

    def add_state(self, name, ns=None):
        instance = OvalState(name, ns)
        self.states.append(instance)
        return instance


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

    def add_metadata(self):
        metadata = Metadata()
        self.append(metadata)
        return metadata

    def add_criteria(self, operator='OR'):
        criteria = Criteria(operator=operator)
        self.append(criteria)
        return criteria


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
        for affected in self._.findall('affected'):
            if affected.get('family') == family:
                for x in affected.findall('platform'):
                    if x.text == platform:
                        return self
                break

        if affected is None:
            affected = self.sub_element('affected').set_attr('family', family)

        affected.sub_element('platform').set_text(platform)
        return self

    def add_criteria(self, operator):
        criteria = Criteria(operator=operator)
        self.append(criteria)
        return criteria


class Criteria(XmlBase):
    def __init__(self, operator='OR'):
        super().__init__('criteria')
        self.set_attr('operator', operator)

    def add_criterion(self, test_ref):
        criterion = Criterion(test_ref=test_ref)
        self.append(criterion)
        return criterion


class Criterion(XmlBase):
    def __init__(self, test_ref):
        super().__init__('criterion')
        self.set_attr('test_ref', test_ref)


class OvalTest(XmlBase):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns)

    def add_object(self, instance):
        obj = self.sub_element('object')
        id = instance.get_attr('id')
        obj.set_attr('object_ref', id)

    def add_state(self, instance):
        state = self.sub_element('state')
        id = instance.get_attr('id')
        state.set_attr('state_ref', id)


class OvalObject(XmlBase):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns)


class OvalState(XmlBase):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns)
