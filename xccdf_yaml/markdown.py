import lxml.etree as etree
import markdown


class MarkdownHtml(object):
    def __init__(self, text):
        self.text = text
        self.html = etree.HTML(markdown.markdown(self.text.rstrip()))
        self.ns = 'xhtml'
        self.nsmap = {'xhtml': 'http://www.w3.org/1999/xhtml'}
        self.html = self.set_default_ns(self.html, default_ns=self.ns)

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
        elements = self.html.xpath(
            '/{ns}:html/{ns}:body'.format(ns=self.ns),
            namespaces=self.nsmap)
        blocks = []
        for element in elements:
            for x in element:
                text = etree.tostring(x, pretty_print=True).decode().strip()
                if text:
                    blocks.append(text)
                if x.tail:
                    blocks.append(x.tail)
        return '\n{}\n'.format(
            '\n'.join(filter(lambda x: x.strip(), blocks)))
