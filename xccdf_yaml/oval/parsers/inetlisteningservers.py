from xccdf_yaml.oval.parsers.common import ParsedObjects
from xccdf_yaml.oval.parsers.common import GenericParser

from xccdf_yaml.oval.elements import Definition
from xccdf_yaml.oval.elements import OvalObject
from xccdf_yaml.oval.elements import OvalState
from xccdf_yaml.oval.elements import OvalTest
from xccdf_yaml.oval.elements import Criterion
from xccdf_yaml.oval.elements import ExternalVariable
from xccdf_yaml.cpe import get_affected_from_cpe

class InetlisteningserversParser(GenericParser):
    """Return inetlisteningservers objects.
       You can pass the address as a variable.
       Be aware, what the address will be ignored
       if you passed the variable"""
    __id__ = 'listen'
    __ns__ = 'oval-def-linux'

    def parse(self, id, metadata):
        res = ParsedObjects()
        rule = res.new_rule(id)

        if 'title' in metadata:
            rule.set_title(metadata['title'])

        if 'description' in metadata:
            rule.set_description(metadata['title'])

        if not 'port' in metadata:
            if not 'local_full_address' in metadata:
                raise KeyError('port or local_full_address must be set')

        protocol = metadata.get('protocol', 'tcp')

        if 'local_full_address' in metadata:
            address, port = metadata['local_full_address'].split(':')
        else:
            address = metadata.get('address', '127.0.0.1')
            port = str(metadata['port'])

        listen = metadata.get('listen', True)
        program = metadata.get('program')
        uid = metadata.get('uid')


        variable = metadata.get('variable')
        oval_var_id = 'oval:{}:var:1'.format(variable)

        address = variable if variable else address

        affected = metadata.get('affected', 'Ubuntu 1604')

        any_addr_re = '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'

        elements_order = (
            'protocol',
            'local_address',
            'local_port',
            'program_name',
            'pid',
            'user_id',
        )


        # Objects
        if listen \
            and address not in ['all', 'any', '0.0.0.0', '*'] \
            and not variable:
            any_listen_obj = OvalObject('oval:{}_listen_any:obj:1'.format(id),
                             'inetlisteningservers_object', ns=self.__ns__)
            any_listen_obj.__elements_order__ = elements_order

            any_listen_obj.sub_element('protocol')\
                .set_text(protocol)
            any_listen_obj.sub_element('local_address')\
                .set_text(any_addr_re)\
                .set_attr('operation', 'pattern match')
            any_listen_obj.sub_element('local_port')\
                .set_text(port)\
                .set_attr('datatype', 'int')
            res.objects.append(any_listen_obj)

        obj = OvalObject('oval:{}:obj:1'.format(id),
                         'inetlisteningservers_object', ns=self.__ns__)
        obj.__elements_order__ = elements_order

        obj.sub_element('protocol')\
            .set_text(protocol)

        if address in ['any', '*']:
            obj.sub_element('local_address')\
                .set_text(any_addr_re)\
                .set_attr('operation', 'pattern match')
        elif address in ['all', '0.0.0.0']:
            obj.sub_element('local_address')\
                .set_text('0.0.0.0')
        elif variable:
            obj.sub_element('local_address')\
                .set_attr('var_ref', oval_var_id)
        else:
            obj.sub_element('local_address')\
                .set_text(address)

        obj.sub_element('local_port')\
            .set_text(port)\
            .set_attr('datatype', 'int')

        res.objects.append(obj)

        # State
        state = OvalState('oval:{}:ste:1'.format(id),
                          'inetlisteningservers_state', ns=self.__ns__)
        state.__elements_order__ = elements_order

        if program:
            state.sub_element('program_name')\
                .set_text(program)

        state.sub_element('pid')\
            .set_text('0')\
            .set_attr('operation', 'greater than')\
            .set_attr('datatype', 'int')

        if 'uid' in metadata:
            state.sub_element('user_id')\
                .set_text(str(metadata['uid']))\
                .set_attr('operation', 'equals')\
                .set_attr('datatype', 'int')

        res.states.append(state)

        # Tests
        if listen \
            and address not in ['all', 'any', '0.0.0.0', '*'] \
            and not variable:
            listen_any_test = OvalTest('oval:{}_listen_any:tst:1'.format(id),
                            'inetlisteningservers_test', ns=self.__ns__)
            listen_any_test.set_attr('check', 'none exist')
            listen_any_test.add_object(any_listen_obj)
            res.tests.append(listen_any_test)

        test = OvalTest('oval:{}:tst:1'.format(id),
                        'inetlisteningservers_test', ns=self.__ns__)

        test.__elements_order__ = (
            'object',
            'state',
        )
        test.set_attr('check', 'at least one')
        test.add_object(obj)
        test.add_state(state)
        res.tests.append(test)

        # Variable
        if variable:
            var_type = metadata['external-variables'][variable]
            res.variable = ExternalVariable(oval_var_id, var_type)


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

        if listen \
            and address not in ['all', 'any', '0.0.0.0', '*'] \
            and not variable:
            operator = 'OR'
        else:
            operator = 'AND'
        criteria = definition.add_criteria(operator=operator)

        for test in res.tests:
            criterion = Criterion(test.get_attr('id'))
            criteria.add_criterion(criterion)
        res.definition = definition
        return res
