from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import OvalTest

class DpkginfoParser(GenericParser):
    __id__ = 'pkg'

    def parse(self, id, metadata):
        res = {}
        res['definition'] = None
        res['tests'] = []
        res['object'] = []
        res['states'] = []

        did = 'oval:{}:def:1'.format(id)
        oid = 'oval:{}:obj:1'.format(id)
        sid = 'oval:{}:ste:1'.format(id)
        tid = 'oval:{}:tst:1'.format(id)

        # Object
        if 'name' in metadata:
            obj = OvalObject(oid)
            pkgname = obj.sub_element('name').set_text(metadata['name'])
            res['object'].append(obj)
        else:
            raise Exception('name must be set')

        # State
        state = OvalState(oid)
        if 'version' in metadata:
            version = metadata['version']
            operation = metadata.get('match')
            if ':' not in version:
                version = '0:{}'.format(version) # we need to have evr
            if operation == 'eq':
                operation = 'equal'
            elif operation == 'ge':
                operation = 'greater than or equal'
            elif operation == 'gt':
                operation = 'greater than'
            else:
                raise Exception('Unsupported pkg version matching')
            evr = state.sub_element('evr').set_text(version)
            evr.set_attrs({
                'datatype': 'evr_string',
                'operation': operation,
            })
        res['states'].append(state)

        # Test
        test = OvalTest(tid)
        o = test.sub_element('object')
        o.set_attr('object_ref', oid)
        s = test.sub_element('state')
        s.set_attr('state_ref', sid)
        res['tests'].append(test)

        # definition
        definition = Definition(did)
        definition.add_metadata('some meta') # ???
        criteria = definition.sub_element('criteria')
        for t in res['tests']:
            crirerion = criteria.sub_element('criterion')
            criterion.set_attr('test_ref', t.get_attr('id'))
        res['definition'] = definition

        return res
