from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import Criterion
from xccdf_yaml.oval import Metadata
from xccdf_yaml.oval import NSMAP

import os

class TextfilecontentParser(GenericParser):
    __id__ = 'pattern_match'

    def parse(self, id, metadata):
        res = ParsedObjects()
        rule = res.new_rule(id)

        if 'title' in metadata:
            rule.set_title(metadata['title'])

        if 'description' in metadata:
            rule.set_description(metadata['title'])

        did = 'oval:{}:def:1'.format(id)

        if not 'filename' in metadata:
            raise KeyError('filename must be set')
        if 'pattern' not in metadata:
            raise KeyError('pattern must be set')

        filenames = []
        if isinstance(metadata['filename'], str):
            filenames.append(metadata['filename'])
        elif isinstance(metadata['filename'], list):
            filenames = metadata['filename']
        else:
            raise ValueError('Unsupported filename format')

        pattern = metadata['pattern']

        for idx, f in enumerate(filenames):
            # Object
            oid = 'oval:{}_{}:obj:1'.format(id, idx)
            path, filename = os.path.split(f)
            filename = '^{}$'.format(filename)
            obj = OvalObject(oid, 'textfilecontent54_object', ns='oval-def-indep')
            obj.__elements_order__ = (
                'path',
                'filename',
                'pattern',
                'instance',
            )
            fpath = obj.sub_element('path').set_text(path)
            fname = obj.sub_element('filename').set_text(filename)
            fname.set_attr('operation', 'pattern match')
            pattern = obj.sub_element('pattern').set_text(pattern)
            pattern.set_attr('operation', 'pattern match')
            instance = obj.sub_element('instance').set_text('1')
            instance.set_attr('datatype', 'int')
            res.objects.append(obj)

            # Test
            tid = 'oval:{}_{}:tst:1'.format(id, idx)
            test = OvalTest(tid, 'textfilecontent54_test', ns='oval-def-indep')
            exists = 'all_exist' if metadata['match'] else 'none_exist'
            test.set_attr('check_existence', exists)
            test.add_object(obj)
            res.tests.append(test)

        # definition
        definition = Definition(did)

        metadata = definition.add_metadata()
        metadata.set_title(str(id))
        metadata.set_description('Check for {}'.format(id))
        metadata.set_affected('unix', 'Ubuntu 1604')

        criteria = definition.add_criteria()
        for test in res.tests:
            criterion = Criterion(test.get_attr('id'))
            criteria.add_criterion(criterion)
        res.definition = definition
        return res
