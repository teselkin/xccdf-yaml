from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import OvalTest

import os

class SystemdParser(GenericParser):
    __id__ = 'systemd'

    def __build_test__(self, oid, sid, tid, _type):
        test = OvalTest(tid, _type)
        o = test.sub_element('object')
        o.set_attr('object_ref', oid)
        s = test.sub_element('state')
        s.set_attr('state_ref', sid)
        return test

    def parse(self, id, metadata):
        res = {}
        res['definition'] = None
        res['tests'] = []
        res['object'] = []
        res['states'] = []

        did = 'oval:{}:def:1'.format(id)

        if 'name' not in metadata:
            raise Exception('name of service must be set')

        name = metadata['name']
        target = metadata.get('target', 'multi-user.target')

        service_state = 'active'
        dep_check = 'at least one'
        test_running_attrs = {
            'check': 'at least one',
            'check_existence': 'at_least_one_exists'
        }

        if metadata.get('disabled', False):
            service_state = 'inactive'
            dep_check = 'none satisfy'
            operator = 'OR'
            test_running_attrs = {
                'check': 'all',
                'check_existence': 'any_exists'
            }

        # Check target
        # object
        oid = 'oval:target_for_{}:obj:1'.format(name)
        obj = OvalObject(oid, 'systemdunitdependency_object')
        unit = obj.sub_element('unit').set_text(target)
        res['objects'].append(obj)
        # state
        sid = 'oval:systemd_service_{}:ste:1'.format(name)
        state = OvalState(sid, 'systemdunitdependency_state')
        dep = state.sub_element('dependency').set_text('{}.service'.format(name))
        dep.set_attr('entity_check', dep_check)
        res['states'].append(state)
        # test
        tid = 'oval:target_wants_{}:tst:1'.format(name)
        test = self.__build_test(oid, sid, tid, 'systemdunitdependency_test')
        res['tests'].append(test)

        # Check socket
        # object
        oid = 'oval:target_for_{}_socket:obj:1'.format(name)
        obj = OvalObject(oid, 'systemdunitdependency_object')
        unit = obj.sub_element('unit').set_text(target)
        res['objects'].append(obj)
        # state
        sid = 'oval:systemd_{}_socket:ste:1'.format(name)
        state = OvalState(sid, 'systemdunitdependency_state')
        dep = state.sub_element('dependency').set_text('{}.socket'.format(name))
        dep.set_attr('entity_check', dep_check)
        res['states'].append(state)
        # test
        tid = 'oval:target_wants_{}_socket:tst:1'.format(name)
        test = self.__build_test__(oid, sid, tid, 'systemdunitdependency_test')
        res['tests'].append(test)

        # Check service [not]running
        # object
        oid = 'oval:service_{}_state:obj:1'.format(name)
        obj = OvalObject(oid, 'systemdunitproperty_object')
        unit = obj.sub_element('unit').set_text('{}\.(socket|service)'.format(name))
        unit.set_attr('operation', 'pattern_match')
        prop = obj.sub_element('property').set_text('ActiveState')
        res['objects'].append(obj)
        # state
        sid = 'oval:service_{}_state:ste:1'.format(name)
        state = OvalState(sid, 'systemdunitproperty_state')
        val = state.sub_element('value').set_text(service_state)
        res['states'].append(state)
        # test
        tid = 'oval:service_{}_state:tst:1'.format(name)
        test = self.__build_test__(oid, sid, tid, 'systemdunitproperty_test')
        test.set_attrs(test_running_attrs)
        res['tests'].append(test)

        # definition
        definition = Definition(did)
        definition.add_metadata('some meta') # ???
        criteria = definition.sub_element('criteria')
        criteria.set_attr('operator', 'AND')
        statecriterion = criteria.sub_element('criterion')
        statecriterion.set_attr('test_ref', 'oval:service_{}_state:tst:1'.format(name))
        if metadata.get('disable', False):
            srvcriterion = criteria.sub_element('criterion')
            srvcriterion.set_attr('test_ref', 'oval:target_wants_{}:tst:1'.format(name))
            sockcriterion = criteria.sub_element('criterion')
            sockcriterion.set_attr('test_ref', 'oval:target_wants_{}_socket:tst:1'.format(name))
        else:
            srvcrit = criteria.sub_element('criteria')
            srvcrit.set_attr('operator', 'OR')
            srvcriterion = srvcrit.sub_element('criterion')
            srvcriterion.set_attr('test_ref', 'oval:target_wants_{}:tst:1'.format(name))
            sockcriterion = srvcrit.sub_element('criterion')
            sockcriterion.set_attr('test_ref', 'oval:target_wants_{}_socket:tst:1'.format(name))

        res['definition'] = definition

        return res
