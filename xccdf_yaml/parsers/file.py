from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import OvalTest

from collections import OrderedDict

class FileParser(GenericParser):
    __id__ = 'file'

    @staticmethod
    def __parse_mode__(mode):
        modes = OrderedDict()
        u, g, o = list(map(lambda x: list(map(lambda y: str(bool(int(y))).lower(),'{:03b}'.format(int(x)))),mode))
        for i in ['u', 'g', 'o']:
            r, w, x = eval(i)
            modes['{}read'.format(i)] = r
            modes['{}write'.format(i)] = w
            modes['{}exec'.format(i)] = x
        return modes

    def parse(self, id, metadata):
        res = {}
        res['definition'] = None
        res['tests'] = []
        res['object'] = []
        res['states'] = []

        did = 'oval:{}:def:1'.format(id)
        oid = 'oval:{}:obj:1'.format(id)

        # Object
        if 'filename' in metadata:
            obj = OvalObject(oid)
            fpath = obj.sub_element('filepath').set_text(metadata['filename'])
            fpath.set_attr('operation', 'pattern match')
            res['object'].append(obj)
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
            state = OvalState(sid)
            for k, v in modes.items():
                attrs = {'type': 'boolean'}
                entity = state.sub_element(k).set_text(v)
                entity.set_attrs(attrs)
            t = OvalTest(tid)
            # Can't use test.add_(object|state) due to incorrect id!
            o = test.sub_element('object')
            o.set_attr('object_ref', oid)
            s = test.sub_element('state')
            s.set_attr('state_ref', sid)
            res['tests'].append(test)
            res['states'].append(state)
        if 'uid' in metadata:
            uid = str(metadata['uid'])
            if int(uid) < 0 or not uid.isdecimal():
                raise Exception('UID must be positive decimal')
            tid = 'oval:{}_uid:tst:1'.format(uid)
            sid = 'oval:{}_uid:ste:1'.format(uid)
            state = OvalState(sid)
            attrs = {'datatype': 'int', 'operation': 'equals'}
            _uid = state.sub_element('user_id').set_text(uid)
            _uid.set_attrs(attrs)
            test = OvalTest(tid)
            o = test.sub_element('object')
            o.set_attr('object_ref', oid)
            s = test.sub_element('state')
            s.set_attr('state_ref', sid)
            res['states'].append(state)
            res['tests'].append(test)
        if 'gid' in metadata:
            gid = str(metadata['gid'])
            if int(gid) < 0 or not gid.isdecimal():
                raise Exception('GID must be positive decimal')
            tid = 'oval:{}_uid:tst:1'.format(uid)
            sid = 'oval:{}_gid:ste:1'.format(sid)
            state = OvalState(sid)
            attrs = {'datatype': 'int', 'operation': 'equals'}
            _gid = state.sub_element('group_id').set_text(gid)
            _gid.set_attrs(attrs)
            test = OvalTest(tid)
            o = test.sub_element('object')
            o.set_attr('object_ref', oid)
            s = test.sub_element('state')
            s.set_attr('state_ref', sid)
            res['states'].append(state)
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
