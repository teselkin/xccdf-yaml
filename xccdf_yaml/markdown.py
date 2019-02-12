from html import escape
from lxml.html import builder
import lxml.etree as etree
import markdown


class MarkdownHtml(object):
    def __init__(self, text, plaintext=False):
        self.text = text
        if plaintext:
            self.html = builder.HTML(builder.BODY(builder.CODE(self.text)))
        else:
            self.html = etree.HTML(markdown.markdown(self.text))
        self.ns = 'xhtml'
        self.nsmap = {'xhtml': 'http://www.w3.org/1999/xhtml'}
        self.html = self.set_default_ns(self.html, default_ns=self.ns)

    def escape(self, text):
        if text:
            return escape(text)
        return text

    def set_default_ns(self, element, default_ns=None):
        e = etree.Element(etree.QName(self.nsmap[default_ns], element.tag),
                          nsmap=self.nsmap)
        for item in element:
            e.append(self.set_default_ns(item, default_ns))
        for key, value in element.attrib.items():
            e.attrib[key] = value
        e.text = self.escape(element.text)
        e.tail = self.escape(element.tail)
        return e

    def xml(self):
        elements = self.html.xpath(
            '/{ns}:html/{ns}:body'.format(ns=self.ns),
            namespaces=self.nsmap)
        for body in elements:
            for element in body:
                yield element

    def tostring(self):
        blocks = []
        for x in self.xml():
            text = etree.tostring(x, pretty_print=True).decode().strip()
            if text:
                blocks.append(text)
            if x.tail:
                blocks.append(x.tail)

        result = '\n{}\n'.format(
            '\n'.join(filter(lambda x: x.strip(), blocks)))
        return result
