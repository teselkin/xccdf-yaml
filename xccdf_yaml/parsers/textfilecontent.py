from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
# from xccdf_yaml.oval import Metadata
from xccdf_yaml.oval import ExternalVariable
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

        if 'pattern' not in metadata and 'variable' not in metadata:
            raise KeyError('pattern or variable must be set')

        filenames = []
        if isinstance(metadata['filename'], str):
            filenames.append(metadata['filename'])
        elif isinstance(metadata['filename'], list):
            filenames = metadata['filename']
        else:
            raise ValueError('Unsupported filename format')

        pattern = metadata.get('pattern')
        variable = metadata.get('variable')
        subexpression = metadata.get('subexpression')

        oval_var_id = 'oval:{}:var:1'.format(variable)

        affected = metadata.get('affected', 'Ubuntu 1604')

        for idx, f in enumerate(filenames):
            state = None
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

            if pattern:
                obj.sub_element('pattern')\
                    .set_text(pattern)\
                    .set_attr('operation', 'pattern match')
            else:
                if not subexpression:
                    obj.sub_element('pattern')\
                        .set_attr('var_ref', oval_var_id)\
                        .set_attr('operation', 'pattern match')

            obj.sub_element('instance')\
                .set_text('1')\
                .set_attr('datatype', 'int')

            res.objects.append(obj)

            # State
            if subexpression and pattern:
                state = OvalState('oval:{}_{}:ste:1'.format(id, idx),
                                  'textfilecontent54_state', ns=self.__ns__)
                if variable:
                    state.sub_element('subexpression')\
                        .set_attr('var_check', 'all')\
                        .set_attr('var_ref', oval_var_id)
                res.states.append(state)

            # Test
            test = OvalTest('oval:{}_{}:tst:1'.format(id, idx),
                            'textfilecontent54_test', ns=self.__ns__)

            if metadata.get('match', True):
                exists = 'all_exist'
            else:
                exists = 'none_exist'

            test.set_attr('check_existence', exists)
            test.add_object(obj)
            if state:
                test.add_state(state)
            res.tests.append(test)

        # variable
        if variable:
            var_type = metadata['external-variables'][variable]
            res.variable = ExternalVariable(oval_var_id, var_type)

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
