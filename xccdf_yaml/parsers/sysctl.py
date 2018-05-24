from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import OvalTest

class SysctlParser(GenericParser):
    __id__ = 'sysctl'

    def parse(self, id, metadata):
        res = {}
        res['definition'] = None
        res['tests'] = []
        res['object'] = []
        res['states'] = []

        did = 'oval:{}:def:1'.format(id)
        oid = 'oval:{}:obj:1'.format(id)
        tid = 'oval:{}:tst:1'.format(id)
        sid = 'oval:{}:ste:1'.format(id)

        # Object
        obj = OvalObject(oid)
        fpath = obj.sub_element('name').set_text(metadata['key'])
        res['object'].append(obj)

        # State
        state = OvalState(sid)
        sysctl_value = state.sub_element('value').set_text(metadata['value'])
        sysctl_value.set_attrs({
            'datatype': 'int',
            'operation': 'equals',
        })
        res['states'].append(state)

        # Test
        test = OvalTest(tid)
        o = test.sub_element('object')
        o.set_attr('object_ref', oid)
        s = test.sub_element('state')
        s.set_attr('state_ref', sid)
        res['tests'].append(test)

        # Definition
        definition = Definition(did)
        definition.add_metadata('some meta') # ???
        criteria = definition.sub_element('criteria')
        for t in res['tests']:
            crirerion = criteria.sub_element('criterion')
            criterion.set_attr('test_ref', t.get_attr('id'))
        res['definition'] = definition

        return res
