from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
from xccdf_yaml.oval import Metadata
from xccdf_yaml.oval import NSMAP

class SysctlParser(GenericParser):
    __id__ = 'sysctl'
    __ns__ = 'oval-def-unix'

    def parse(self, id, metadata):
        res = ParsedObjects()
        rule = res.new_rule(id)

        did = 'oval:{}:def:1'.format(id)
        oid = 'oval:{}:obj:1'.format(id)
        tid = 'oval:{}:tst:1'.format(id)
        sid = 'oval:{}:ste:1'.format(id)

        # Object
        obj = OvalObject(oid, 'sysctl_object', ns=self.__ns__)
        fpath = obj.sub_element('name').set_text(metadata['key'])
        res.objects.append(obj)

        # State
        state = OvalState(sid, 'sysctl_state', ns=self.__ns__)
        sysctl_value = state.sub_element('value').set_text(metadata['value'])
        sysctl_value.set_attrs({
            'datatype': 'int',
            'operation': 'equals',
        })
        res.states.append(state)

        # Test
        test = OvalTest(tid, 'sysctl_test', ns=self.__ns__)
        test.add_object(obj)
        test.add_state(state)
        res.tests.append(test)

        # Definition
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
