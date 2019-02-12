import lxml.etree as etree
from collections import OrderedDict
from operator import itemgetter


class XmlCommon(object):
    __elements__ = None
    __elements_order__ = None

    def __init__(self, name, ns=None, nsmap=None):
        self._name = name
        self._nsmap = nsmap or {}
        self._ns = ns
        self._children = OrderedDict()
        # Use OrderedDict for storing attributes to prevent changes in
        # attributes ordering on each convertion.
        self._attrs = OrderedDict()
        self._text = None
        self._object = None

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

    def remove_elements(self, name=None, elements=[]):
        if name:
            self._children.pop(name, None)
        else:
            for element in elements:
                name = element._name
                try:
                    self._children[name].remove(element)
                except (KeyError, IndexError):
                    pass

    def append(self, element):
        elements = self._children.setdefault(element._name, [])
        if element not in elements:
            elements.append(element)
        return element

    def sub_element(self, name, ns=None):
        if isinstance(self.__elements__, list):
            if name not in self.__elements__:
                raise Exception("Element {} is not allowed".format(name))
        namespace = ns or self._ns
        element = XmlCommon(name, ns=namespace, nsmap=self._nsmap)
        self.append(element)
        return element

    def set(self, key, *args, **kwargs):
        method_name = 'set_{}'.format(key.replace('-', '_').lower())
        return getattr(self, method_name)(*args, **kwargs)

    def set_text(self, text):
        self._text = text
        return self

    def set_object(self, obj):
        self._object = obj
        return self

    def get_attr(self, name):
        return self._attrs.get(name)

    def set_attr(self, name, value):
        self._attrs[name] = value
        return self

    def set_attrs(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        for key, value in sorted(attrs.items(), key=itemgetter(0)):
            self._attrs[key] = value
        return self

    def update_elements(self):
        return

    def xml(self):
        self.update_elements()

        element = etree.Element(self.tag(self._name), nsmap=self._nsmap)
        for key, value in self._attrs.items():
            element.set(key, value)
        if self._object:
            element.extend(self._object.xml())
        elif self._text:
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


class DublinCoreElementBase(XmlCommon):
    __elements__ = [
        'contributor',
        'coverage',
        'creator',
        'date',
        'description',
        'format',
        'identifier',
        'language',
        'publisher',
        'relation',
        'rights',
        'source',
        'subject',
        'title',
        'type',
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('nsmap', {})
        kwargs['nsmap']['dc'] = 'http://purl.org/dc/elements/1.1/'
        super(DublinCoreElementBase, self).__init__(*args, **kwargs)

    def sub_element(self, name, ns=None):
        return super(DublinCoreElementBase, self).sub_element(name, ns='dc')
