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

    def set_attr(self, name, value):
        self._.set(name, value)

    def __str__(self):
        return etree.tostring(self._, pretty_print=True).decode()


class Benchmark(XmlBase):
    def __init__(self, id, version='0.1', title=None, status='draft',
                 status_date=None):
        super().__init__('Benchmark')

        self.set_attr('id', id)

        status_element = etree.SubElement(self._, self.tag('status'))
        status_element.text = status
        if status_date is not None:
            status_element.set('date', status_date)

        version_element = etree.SubElement(self._, self.tag('version'))
        version_element.text = version

        if title is not None:
            self.set_title(title)

    def set_title(self, text):
        title = etree.SubElement(self._, self.tag('title'))
        title.text = text

    def set_description(self, text):
        description = etree.SubElement(self._, self.tag('description'))
        description.text = text

    def add_platform(self, name):
        platform = etree.SubElement(self._, self.tag('platform'))
        platform.set('idref', name)


class BenchmarkProfile(XmlBase):
    def __init__(self):
        super().__init__('Profile')
        pass

    def xml(self):
        pass


class BenchmarkGroup(XmlBase):
    def __init__(self):
        super().__init__('Group')

    def xml(self):
        pass


class BenchmarkRule(XmlBase):
    def __init__(self):
        super().__init__('Rule')
        self.title = ''
        self.description = ''
        self.xml()

    def xml(self):
        pass

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
        element = etree.SubElement(self._, self.tag('check-import'))
        for key, value in attrs.items():
            element.set(key, value)

    def check_content_ref(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        element = etree.SubElement(self._, self.tag('check-content-ref'))
        for key, value in attrs.items():
            element.set(key, value)
