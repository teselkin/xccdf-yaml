from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
from xccdf_yaml.oval import Criteria
from xccdf_yaml.oval import Metadata
from xccdf_yaml.oval import NSMAP
from xccdf_yaml.cpe import get_affected_from_cpe

import os

class SystemdParser(GenericParser):
    __id__ = 'systemd'
    __ns__ = 'oval-def-linux'

    def parse(self, id, metadata):
        res = ParsedObjects()
        rule = res.new_rule(id)

        did = 'oval:{}:def:1'.format(id)

        if 'name' not in metadata:
            raise KeyError('name of service must be set')

        affected = metagata.get('affected', 'Ubuntu 1604')
        name = metadata['name']
        target = metadata.get('target', 'multi-user.target')

        service_disabled = metadata.get('disabled', False)

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
                'check_existence': 'any_exist'
            }

        # Check target
        # object
        oid = 'oval:target_for_{}:obj:1'.format(name)
        obj = OvalObject(oid, 'systemdunitdependency_object', ns=self.__ns__)
        unit = obj.sub_element('unit').set_text(target)
        res.objects.append(obj)
        # state
        sid = 'oval:systemd_service_{}:ste:1'.format(name)
        state = OvalState(sid, 'systemdunitdependency_state', ns=self.__ns__)
        dep = state.sub_element('dependency')\
                .set_text('{}.service'.format(name))
        dep.set_attr('entity_check', dep_check)
        res.states.append(state)
        # test
        tid = 'oval:target_wants_{}:tst:1'.format(name)
        test = OvalTest(tid, 'systemdunitdependency_test', ns=self.__ns__)
        test.__elements_order__ = (
            'object',
            'state',
        )
        test.add_object(obj)
        test.add_state(state)
        res.tests.append(test)

        # Check socket
        # object
        oid = 'oval:target_for_{}_socket:obj:1'.format(name)
        obj = OvalObject(oid, 'systemdunitdependency_object', ns=self.__ns__)
        unit = obj.sub_element('unit').set_text(target)
        res.objects.append(obj)
        # state
        sid = 'oval:systemd_{}_socket:ste:1'.format(name)
        state = OvalState(sid, 'systemdunitdependency_state', ns=self.__ns__)
        dep = state.sub_element('dependency')\
                .set_text('{}.socket'.format(name))
        dep.set_attr('entity_check', dep_check)
        res.states.append(state)
        # test
        tid = 'oval:target_wants_{}_socket:tst:1'.format(name)
        test = OvalTest(tid, 'systemdunitdependency_test', ns=self.__ns__)
        test.__elements_order__ = (
            'object',
            'state',
        )
        test.add_object(obj)
        test.add_state(state)
        res.tests.append(test)

        # Check service [not]running
        # object
        oid = 'oval:service_{}_state:obj:1'.format(name)
        obj = OvalObject(oid, 'systemdunitproperty_object', ns=self.__ns__)
        obj.__elements_order__ = (
            'unit',
            'property',
        )
        unit = obj.sub_element('unit')\
                .set_text('{}\.(socket|service)'.format(name))
        unit.set_attr('operation', 'pattern match')
        prop = obj.sub_element('property').set_text('ActiveState')
        res.objects.append(obj)
        # state
        sid = 'oval:service_{}_state:ste:1'.format(name)
        state = OvalState(sid, 'systemdunitproperty_state', ns=self.__ns__)
        val = state.sub_element('value').set_text(service_state)
        res.states.append(state)
        # test
        tid = 'oval:service_{}_state:tst:1'.format(name)
        test = OvalTest(tid, 'systemdunitproperty_test', ns=self.__ns__)
        test.__elements_order__ = (
            'object',
            'state',
        )
        test.set_attrs(test_running_attrs)
        test.add_object(obj)
        test.add_state(state)
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


        criteria = definition.add_criteria(operator='AND')

        statecriterion = Criterion('oval:service_{}_state:tst:1'.format(name))
        criteria.add_criterion(statecriterion)

        if service_disabled:
            srvcriterion = Criterion('oval:target_wants_{}:tst:1'\
                                     .format(name))
            sockcriretion = Criterion('oval:target_wants_{}_socket:tst:1'\
                                      .format(name))
            criteria.add_criterion(srvcriterion)
            criteria.add_criterion(sockcriretion)
        else:
            srvcrit = Criteria()
            srvcriterion = Criterion('oval:target_wants_{}:tst:1'\
                                     .format(name))
            sockcriterion = Criterion('oval:target_wants_{}_socket:tst:1'\
                                      .format(name))
            srvcrit.add_criterion(srvcriterion)
            srvcrit.add_criterion(sockcriterion)
            criteria.add_criteria(srvcrit)

        res.definition = definition

        return res
