import lxml.etree as etree

NSMAP = {
    None: "http://checklists.nist.gov/xccdf/1.1",
    'oval-def': "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    'sce': "http://open-scap.org/page/SCE",
    'sceres': "http://open-scap.org/page/SCE_result_file",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class XmlBase(object):
    def __init__(self, name, default_ns=None):
        self.default_ns = default_ns
        self._ = etree.Element(self.tag(name), nsmap=NSMAP)

    def tag(self, name, ns=None):
        namespace = ns or self.default_ns
        return etree.QName(NSMAP[namespace], name)

    def sub_element(self, *args, **kwargs):
        return etree.SubElement(self._, self.tag(*args, **kwargs))

    def set_attr(self, name, value):
        self._.set(name, value)

    def __str__(self):
        return etree.tostring(self._, pretty_print=True).decode()


class Benchmark(XmlBase):
    def __init__(self, id, version='0.1', title=None, status='draft',
                 status_date=None):
        super().__init__('Benchmark')
        self.id = id
        self.set_attr('id', id)

        status_element = self.sub_element('status')
        status_element.text = status
        if status_date is not None:
            status_element.set('date', status_date)

        version_element = self.sub_element('version')
        version_element.text = version

        if title is not None:
            self.set_title(title)

    def set_title(self, text):
        title = self.sub_element('title')
        title.text = text

    def set_description(self, text):
        description = self.sub_element('description')
        description.text = text

    def add_platform(self, name):
        platform = self.sub_element('platform')
        platform.set('idref', name)

    def add_profile(self, id):
        profile = BenchmarkProfile(id)
        self._.append(profile._)
        return profile

    def add_group(self, id):
        group = BenchmarkGroup(id)
        self._.append(group._)
        return group


class BenchmarkProfile(XmlBase):
    def __init__(self, id):
        super().__init__('Profile')
        self.id = id
        self.set_attr('id', id)

    def set_title(self, text):
        title = self.sub_element('title')
        title.text = text

    def set_description(self, text):
        description = self.sub_element('description')
        description.text = text

    def add_rule(self, rule, selected=False):
        select_element = self.sub_element('select')
        select_element.set('idref', rule.id)
        select_element.set('selected', str(selected))


class BenchmarkGroup(XmlBase):
    def __init__(self, id):
        super().__init__('Group')
        self.id = id
        self.set_attr('id', id)

    def set_title(self, text):
        title = self.sub_element('title')
        title.text = text

    def set_description(self, text):
        description = self.sub_element('description')
        description.text = text

    def add_rule(self, id):
        rule = BenchmarkRule(id)
        self._.append(rule._)
        return rule


class BenchmarkRule(XmlBase):
    def __init__(self, id, selected=False, severity='medium'):
        super().__init__('Rule')
        self.id = id
        self.set_attr('id', id)
        self.set_attr('selected', str(selected))
        self.set_attr('severity', severity)

    def set_title(self, text):
        title = self.sub_element('title')
        title.text = text

    def set_description(self, text):
        description = self.sub_element('description')
        description.text = text

    def add_check(self, **kwargs):
        check = XccdfCheck(**kwargs)
        self._.append(check._)
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
        element = self.sub_element('check-import')
        for key, value in attrs.items():
            element.set(key, value)

    def check_content_ref(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        element = self.sub_element('check-content-ref')
        for key, value in attrs.items():
            element.set(key, value)
