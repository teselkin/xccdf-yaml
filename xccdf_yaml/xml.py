import lxml.etree as etree


class XmlCommon(object):
    __elements_order__ = None

    def __init__(self, name, ns=None, nsmap={}):
        self._name = name
        self._nsmap = nsmap
        self._ns = ns
        self._children = {}
        self._attrs = {}
        self._text = None

    def namespace(self, ns=None):
        return self._nsmap[ns]

    def elements(self, name=None):
        if name is None:
            for children in self._children.values():
                for child in children:
                    yield child
        else:
            for child in self._children.get(name, []):
                yield child

    def tag(self, name, ns=None):
        namespace = ns or self._ns
        return etree.QName(self._nsmap[namespace], name)

    def append(self, element):
        self._children.setdefault(element._name, []).append(element)
        print(self._children)
        return element

    def sub_element(self, name, ns=None):
        namespace = ns or self._ns
        element = XmlCommon(name, ns=namespace, nsmap=self._nsmap)
        self._children.setdefault(name, []).append(element)
        return element

    def set_text(self, text):
        self._text = text
        return self

    def get_attr(self, name):
        return self._attrs.get(name)

    def set_attr(self, name, value):
        self._attrs[name] = value
        return self

    def set_attrs(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self._attrs.update(attrs)
        return self

    def xml(self):
        element = etree.Element(self.tag(self._name), nsmap=self._nsmap)
        for key, value in self._attrs.items():
            element.set(key, value)
        if self._text:
            element.text = self._text
        else:
            if self.__elements_order__ is None:
                for children in self._children.values():
                    for child in children:
                        element.append(child.xml())
            else:
                for key in self.__elements_order__:
                    for child in self._children.get(key, []):
                        element.append(child.xml())
                for key in self._children.keys():
                    if key in self.__elements_order__:
                        continue
                    for child in self._children.get(key, []):
                        element.append(child.xml())
        return element

    def __str__(self):
        return etree.tostring(self.xml(), pretty_print=True).decode()
