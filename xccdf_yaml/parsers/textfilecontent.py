from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import Criterion
# from xccdf_yaml.oval import Metadata
from xccdf_yaml.cpe import get_affected_from_cpe

import os

class TextfilecontentParser(GenericParser):
    __id__ = 'pattern_match'
    __ns__ = 'oval-def-indep'

    def parse(self, id, metadata):
        res = ParsedObjects(self.xccdf)
        rule = res.new_rule(id)

        if 'title' in metadata:
            rule.set_title(metadata['title'])

        if 'description' in metadata:
            rule.set_description(metadata['title'])

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
        affected = metadata.get('affected', 'Ubuntu 1604')

        for idx, f in enumerate(filenames):
            # Object
            path, filename = os.path.split(f)

            # If filename not a regular expression
            if not filename.startswith('^'):
                filename = '^{}'.format(filename)
            if not filename.endswith('$'):
                filename = '{}$'.format(filename)

            obj = OvalObject('oval:{}_{}:obj:1'.format(id, idx),
                             'textfilecontent54_object', ns=self.__ns__)

            obj.__elements_order__ = (
                'path',
                'filename',
                'pattern',
                'instance',
            )

            obj.sub_element('path')\
                .set_text(path)

            obj.sub_element('filename')\
                .set_text(filename)\
                .set_attr('operation', 'pattern match')

            obj.sub_element('pattern')\
                .set_text(pattern)\
                .set_attr('operation', 'pattern match')

            obj.sub_element('instance')\
                .set_text('1')\
                .set_attr('datatype', 'int')

            res.objects.append(obj)

            # Test
            test = OvalTest('oval:{}_{}:tst:1'.format(id, idx),
                            'textfilecontent54_test', ns=self.__ns__)

            if metadata.get('match', True):
                exists = 'all_exist'
            else:
                exists = 'none_exist'

            test.set_attr('check_existence', exists)
            test.add_object(obj)
            res.tests.append(test)

        # definition
        definition = Definition('oval:{}:def:1'.format(id))

        metadata = definition.add_metadata()
        metadata.set_title(str(id))
        metadata.set_description('Check for {}'.format(id))
        if isinstance(affected, list):
            for affect in affected:
                metadata.set_affected('unix', get_affected_from_cpe(affect))
        else:
            metadata.set_affected('unix', get_affected_from_cpe(affected))

        criteria = definition.add_criteria()
        for test in res.tests:
            criterion = Criterion(test.get_attr('id'))
            criteria.add_criterion(criterion)
        res.definition = definition
        return res
