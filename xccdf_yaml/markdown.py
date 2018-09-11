import lxml.etree as etree
import markdown


class MarkdownHtml(object):
    def __init__(self, text):
        self.text = text
        self.html = etree.fromstring(markdown.markdown(self.text.rstrip()))
        self.nsmap = {'xhtml': 'http://www.w3.org/1999/xhtml'}
        self.html = self.set_default_ns(self.html, default_ns='xhtml')

    def set_default_ns(self, element, default_ns=None):
        e = etree.Element(etree.QName(self.nsmap[default_ns], element.tag),
                          nsmap=self.nsmap)
        for item in element:
            e.append(self.set_default_ns(item, default_ns))
        for key, value in element.attrib.items():
            e.attrib[key] = value
        e.text = element.text
        e.tail = element.tail
        return e

    def __str__(self):
        return etree.tostring(self.html).decode()
