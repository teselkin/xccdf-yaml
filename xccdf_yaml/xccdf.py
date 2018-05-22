import lxml.etree as etree

from xccdf_yaml.xml import XmlCommon


NSMAP = {
    None: "http://checklists.nist.gov/xccdf/1.1",
    'oval-def': "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    'sce': "http://open-scap.org/page/SCE",
    'sceres': "http://open-scap.org/page/SCE_result_file",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns, nsmap=NSMAP)


class Benchmark(XmlBase):
    __elements_order__ = [
        'status',
        'version',
        'title',
        'description',
        'platform',
        'Profile',
    ]

    def __init__(self, id, version='0.1', status='draft', status_date=None):
        super().__init__('Benchmark')
        self.set_attr('id', id)
        self.set_status(status, status_date)
        self.set_version(version)

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def set_status(self, status='draft', status_date=None):
        element = self.sub_element('status').set_text(status)
        if status_date:
            element.set_attr('date', status_date)
        return self

    def set_version(self, version):
        self.sub_element('version').set_text(version)

    def add_platform(self, name):
        self.sub_element('platform').set_text(name)
        return self

    def add_profile(self, id):
        profile = BenchmarkProfile(id)
        self.append(profile)
        return profile

    def add_group(self, id):
        group = BenchmarkGroup(id)
        self.append(group)
        return group


class BenchmarkProfile(XmlBase):
    def __init__(self, id):
        super().__init__('Profile')
        self.set_attr('id', id)

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def append_rule(self, rule, selected=False):
        self.sub_element('select').set_attrs({
            'idref': rule.get_attr('id'),
            'selected': str(selected)
        })
        return self


class BenchmarkGroup(XmlBase):
    def __init__(self, id):
        super().__init__('Group')
        self.set_attr('id', id)

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def append_rule(self, rule):
        self.append(rule)
        return rule

    def add_rule(self, id):
        rule = BenchmarkRule(id)
        self.append(rule)
        return rule


class BenchmarkRule(XmlBase):
    def __init__(self, id, selected=False, severity='medium'):
        super().__init__('Rule')
        self.set_attrs({
            'id': id,
            'severity': severity,
            'selected': str(selected),
        })

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def add_check(self, **kwargs):
        check = XccdfCheck(**kwargs)
        self.append(check)
        return check


class XccdfCheck(XmlBase):
    def __init__(self, id=None, system_ns='oval-def'):
        super().__init__('check')
        if id:
            self.set_attr('id', id)
        self.set_attr('system', self.namespace(system_ns))

    def check_import(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self.sub_element('check-import').set_attrs(attrs)
        return self

    def check_content_ref(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self.sub_element('check-content-ref').set_attrs(attrs)
        return self
