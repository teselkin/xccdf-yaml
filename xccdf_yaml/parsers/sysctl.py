from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
# from xccdf_yaml.oval import Metadata
from xccdf_yaml.cpe import get_affected_from_cpe

class SysctlParser(GenericParser):
    __id__ = 'sysctl'
    __ns__ = 'oval-def-unix'

    def parse(self, id, metadata):
        res = ParsedObjects(self.xccdf)
        res.new_rule(id)

        affected = metadata.get('affected', 'Ubuntu 1604')

        # Object
        obj = OvalObject('oval:{}:obj:1'.format(id),
                         'sysctl_object', ns=self.__ns__)
        obj.sub_element('name').set_text(metadata['key'])
        res.objects.append(obj)

        # State
        state = OvalState('oval:{}:ste:1'.format(id),
                          'sysctl_state', ns=self.__ns__)
        sysctl_value = state.sub_element('value').set_text(metadata['value'])
        sysctl_value.set_attrs({
            'datatype': 'int',
            'operation': 'equals',
        })
        res.states.append(state)

        # Test
        test = OvalTest('oval:{}:tst:1'.format(id),
                        'sysctl_test', ns=self.__ns__)
        test.add_object(obj)
        test.add_state(state)
        res.tests.append(test)

        # Definition
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
