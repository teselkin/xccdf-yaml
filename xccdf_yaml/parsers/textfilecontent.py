from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest

import os

class TextfilecontentParser(GenericParser):
    __id__ = 'pattern_match'

    def parse(self, id, metadata):
        res = {}
        res['definition'] = None
        res['tests'] = []
        res['object'] = []
        res['states'] = []

        did = 'oval:{}:def:1'.format(id)

        if not 'filename' in metadata:
            raise Exception('filename must be set')
        if 'pattern' not in metadata:
            raise Exception('pattern must be set')

        filenames = []
        if isinstance(metadata['filename'], (str, unicode)):
            filenames.append(metadata['filename'])
        elif isinstance(metadata['filename'], list):
            filenames = metadata['filename']
        else:
            raise Exception('Unsupported filename format')

        for idx, f in enumerate(filenames):
            # Object
            oid = 'oval:{}_{}:obj:1'.format(id, idx)
            path, filename = os.path.split(filename)
            obj = OvalObject(oid, 'textfilecontent54_object')
            fpath = obj.sub_element('path').set_text(path)
            fname = obj.sub_element('filename').set_text(filename)
            fname.set_attr('operation', 'pattern match')
            pattern = obj.sub_element('pattern').set_text(pattern)
            pattern.set_attr('operation', 'pattern match')
            instance = obj.sub_element('instance').set_text('1')
            instance.set_attr('datatype', 'int')
            res['object'].append(obj)

            # Test
            tid = 'oval:{}_{}:obj:1'.format(id, idx)
            test = OvalTest(tid, 'textfilecontent54_test')
            o = test.sub_element('object')
            o.set_attr('object_ref', oid)
            res['tests'].append(test)

        # definition
        definition = Definition(did)
        definition.add_metadata('some meta') # ?
        criteria = definition.sub_element('criteria')
        criteria.set_attr('operator', 'OR') # Really?
        for t in res['tests']:
            crirerion = criteria.sub_element('criterion')
            criterion.set_attr('test_ref', t.get_attr('id'))
        res['definition'] = definition

        return res
