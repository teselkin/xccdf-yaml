from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
from xccdf_yaml.oval import Metadata
from xccdf_yaml.oval import NSMAP
from xccdf_yaml.cpe import get_affected_from_cpe

class DpkginfoParser(GenericParser):
    __id__ = 'pkg'
    __ns__ = 'oval-def-linux'

    def parse(self, id, metadata):
        res = ParsedObjects()
        rule = res.new_rule(id)

        did = 'oval:{}:def:1'.format(id)
        oid = 'oval:{}:obj:1'.format(id)
        sid = 'oval:{}:ste:1'.format(id)
        tid = 'oval:{}:tst:1'.format(id)

        # Object
        if 'name' in metadata:
            obj = OvalObject(oid, 'dpkginfo_object', ns=self.__ns__)
            pkgname = obj.sub_element('name').set_text(metadata['name'])
            res.objects.append(obj)
        else:
            raise KeyError('name must be set')

        affected = metadata.get('affected', 'Ubuntu 1604')

        # State
        state = OvalState(sid, 'dpkginfo_state', ns=self.__ns__)
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
                raise ValueError('Unsupported pkg version matching')
            evr = state.sub_element('evr').set_text(version)
            evr.set_attrs({
                'datatype': 'evr_string',
                'operation': operation,
            })
        res.states.append(state)

        # Test
        test = OvalTest(tid, 'dpkginfo_test', ns=self.__ns__)
        if metadata.get('removed', False):
            check_existence = 'none_exist'
        else:
            check_existence = 'all_exist'
        test.set_attr('check_existence', check_existence)
        test.add_object(obj)
        res.tests.append(test)

        # definition
        definition = Definition(did)

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
