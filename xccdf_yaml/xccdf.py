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
    def __init__(self, id, version='0.1', title=None, status='draft',
                 status_date=None):
        super().__init__('Benchmark')
        self.id = id
        self.set_attr('id', id)

        status_element = self.sub_element('status').set_text(status)
        if status_date is not None:
            status_element.set_attr('date', status_date)

        self.sub_element('version').set_text(version)

        if title is not None:
            self.set_title(title)

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def add_platform(self, name):
        self.sub_element('platform').set_attr('idref', name)
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
        self.id = id
        self.set_attr('id', id)

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def add_rule(self, rule, selected=False):
        self.sub_element('select')\
            .set_attr('idref', rule.id)\
            .set_attr('selected', str(selected))


class BenchmarkGroup(XmlBase):
    def __init__(self, id):
        super().__init__('Group')
        self.id = id
        self.set_attr('id', id)

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def add_rule(self, id):
        rule = BenchmarkRule(id)
        self.append(rule)
        return rule


class BenchmarkRule(XmlBase):
    def __init__(self, id, selected=False, severity='medium'):
        super().__init__('Rule')
        self.id = id
        self.set_attr('id', id)
        self.set_attr('selected', str(selected))
        self.set_attr('severity', severity)

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
    def __init__(self, namespace='oval-def', negate=None, id=None,
                 selector=None, multi_check=None):
        super().__init__('check')
        self.set_attr('system', NSMAP[namespace])
        if id is not None:
            self.set_attr('id', id)
        if negate is not None:
            self.set_attr('negate', negate)
        if selector is not None:
            self.set_attr('selector', selector)
        if multi_check is not None:
            self.set_attr('multi-check', multi_check)

    def check_import(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self.sub_element('check-import').set_attrs(attrs)

    def check_content_ref(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self.sub_element('check-content-ref').set_attrs(attrs)
