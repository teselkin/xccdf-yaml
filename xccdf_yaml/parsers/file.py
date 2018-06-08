from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
from xccdf_yaml.oval import Metadata
from xccdf_yaml.oval import NSMAP

from collections import OrderedDict

class FileParser(GenericParser):
    __id__ = 'file'
    __ns__ = 'oval-def-unix'

    @staticmethod
    def __parse_mode__(mode):
        bit_names = [
        'uread', 'uwrite', 'uexec',
        'gread', 'gwrite', 'gexec',
        'oread', 'owrite', 'oexec',
        ]
        bit_string = ''.join([
            '{0:03b}'.format(int(i)) for i in str(mode)])
        bit_values = [str(x == '1').lower() for x in bit_string][:9]
        return OrderedDict(zip(bit_names, bit_values))

    def parse(self, id, metadata):
        res = ParsedObjects()
        rule = res.new_rule(id)

        did = 'oval:{}:def:1'.format(id)
        oid = 'oval:{}:obj:1'.format(id)

        # Object
        if 'filename' in metadata:
            obj = OvalObject(oid, 'file_object', ns=self.__ns__)
            fpath = obj.sub_element('filepath').set_text(metadata['filename'])
            fpath.set_attr('operation', 'pattern match')
            res.objects.append(obj)
        else:
            raise Exception('filename must be set')

        # states and tests
        if 'mode' in metadata:
            mode = str(metadata['mode'])
            if len(mode) != 3:
                raise Exception('mode must be 3 digits')
            modes = self.__parse_mode__(mode)
            tid = 'oval:{}_mode:tst:1'.format(id)
            sid = 'oval:{}_mode:ste:1'.format(id)
            # State
            state = OvalState(sid, 'file_state', ns=self.__ns__)
            state.__elements_order__ = (
                'uread', 'uwrite', 'uexec',
                'gread', 'gwrite', 'gexec',
                'oread', 'owrite', 'oexec',
            )
            for k, v in modes.items():
                attrs = {'datatype': 'boolean'}
                entity = state.sub_element(k).set_text(v)
                entity.set_attrs(attrs)
            res.states.append(state)
            # Test
            test = OvalTest(tid, 'file_test', ns=self.__ns__)
            test.__elements_order__ = (
                'object',
                'state',
            )
            test.add_object(obj)
            test.add_state(state)
            res.tests.append(test)
        if 'uid' in metadata:
            uid = str(metadata['uid'])
            if int(uid) < 0 or not uid.isdecimal():
                raise Exception('UID must be positive decimal')
            tid = 'oval:{}_uid:tst:1'.format(uid)
            sid = 'oval:{}_uid:ste:1'.format(uid)
            # State
            state = OvalState(sid, 'file_state', ns=self.__ns__)
            attrs = {'datatype': 'int', 'operation': 'equals'}
            _uid = state.sub_element('user_id').set_text(uid)
            _uid.set_attrs(attrs)
            res.states.append(state)
            # Test
            test = OvalTest(tid, 'file_test', ns=self.__ns__)
            test.__elements_order__ = (
                'object',
                'state',
            )
            test.add_object(obj)
            test.add_state(state)
            res.tests.append(test)
        if 'gid' in metadata:
            gid = str(metadata['gid'])
            if int(gid) < 0 or not gid.isdecimal():
                raise Exception('GID must be positive decimal')
            tid = 'oval:{}_uid:tst:1'.format(uid)
            sid = 'oval:{}_gid:ste:1'.format(sid)
            # State
            state = OvalState(sid, 'file_state', ns=self.__ns__)
            attrs = {'datatype': 'int', 'operation': 'equals'}
            _gid = state.sub_element('group_id').set_text(gid)
            _gid.set_attrs(attrs)
            res.states.append(state)
            # Test
            test = OvalTest(tid, 'file_test', ns=self.__ns__)
            test.__elements_order__ = (
                'object',
                'state',
            )
            test.add_object(obj)
            test.add_state(state)
            res.tests.append(test)

        # definition
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
