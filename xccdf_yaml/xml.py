import lxml.etree as etree


class XmlCommon(object):
    def __init__(self, name, ns=None, nsmap={}):
        self.NSMAP = nsmap
        self.default_ns = ns
        self._ = etree.Element(self.tag(name), nsmap=self.NSMAP)

    def append(self, instance):
        self._.append(instance._)

    def tag(self, name, ns=None):
        namespace = ns or self.default_ns
        return etree.QName(self.NSMAP[namespace], name)

    def sub_element(self, name, ns=None):
        element = XmlCommon(name, ns=ns, nsmap=self.NSMAP)
        self.append(element)
        return element

    def set_text(self, text):
        self._.text = text
        return self

    def get_attr(self, name):
        return self._.get(name)

    def set_attr(self, name, value):
        self._.set(name, value)
        return self

    def set_attrs(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        for key, value in attrs.items():
            self._.set(key, value)
        return self

    def __str__(self):
        return etree.tostring(self._, pretty_print=True).decode()
