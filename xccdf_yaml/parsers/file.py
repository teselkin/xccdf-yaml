from xccdf_yaml.parsers.common import ParsedObjects
from xccdf_yaml.parsers.common import GenericParser

from xccdf_yaml.oval import Definition
from xccdf_yaml.oval import OvalObject
from xccdf_yaml.oval import OvalTest
from xccdf_yaml.oval import OvalState
from xccdf_yaml.oval import Criterion
# from xccdf_yaml.oval import Metadata
from xccdf_yaml.cpe import get_affected_from_cpe


class FileParser(GenericParser):
    __ns__ = 'oval-def-unix'

    @staticmethod
    def __parse_mode__(mode):
        mode = '{:0>4}'.format(mode)
        bit_names = [
            'suid', 'sgid', 'sticky',
            'uread', 'uwrite', 'uexec',
            'gread', 'gwrite', 'gexec',
            'oread', 'owrite', 'oexec',
        ]
        bit_string = ''.join([
            '{0:03b}'.format(int(i)) for i in str(mode)])
        bit_values = [str(x == '1').lower()
                      for x in bit_string][:len(bit_names)]
        return dict(zip(bit_names, bit_values))

    def parse(self, id, metadata):
        res = ParsedObjects(self.xccdf)
        res.new_rule(id)

        if 'filename' not in metadata:
            raise KeyError('filename must be set')

        filenames = []
        if isinstance(metadata['filename'], str):
            filenames.append(metadata['filename'])
        elif isinstance(metadata['filename'], list):
            filenames = metadata['filename']
        else:
            raise ValueError('filename must be string or list')

        affected = metadata.get('affected', 'Ubuntu 1604')

        for idx, filename in enumerate(filenames):
            # Object
            obj = OvalObject('oval:{}_{}:obj:1'.format(id, idx),
                             'file_object', ns=self.__ns__)

            obj.sub_element('filepath')\
                .set_text(filename)\
                .set_attr('operation', 'pattern match')

            res.objects.append(obj)

            # states and tests
            if 'mode' in metadata:
                mode = str(metadata['mode'])
                if 4 < len(mode) < 1:
                    raise ValueError("mode must be 1 to 4 digits")
                if not str(mode).isdecimal():
                    raise ValueError("mode must be decimal")
                modes = self.__parse_mode__(mode)

                # State
                state = OvalState('oval:{}_mode_{}:ste:1'.format(id, idx),
                                  'file_state', ns=self.__ns__)
                state.__elements_order__ = (
                    'suid', 'sgid', 'sticky',
                    'uread', 'uwrite', 'uexec',
                    'gread', 'gwrite', 'gexec',
                    'oread', 'owrite', 'oexec',
                )
                for k, v in modes.items():
                    state.sub_element(k)\
                        .set_text(v)\
                        .set_attr('datatype', 'boolean')

                res.states.append(state)

                # Test
                test = OvalTest('oval:{}_mode_{}:tst:1'.format(id, idx),
                                'file_test', ns=self.__ns__)
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
                    raise ValueError('UID must be positive decimal')
                # tid = 'oval:{}_uid:tst:1'.format(uid)

                # State
                state = OvalState('oval:{}_uid_{}:ste:1'.format(id, idx),
                                  'file_state', ns=self.__ns__)

                state.sub_element('user_id')\
                    .set_text(uid)\
                    .set_attr('datatype', 'int')\
                    .set_attr('operation', 'equals')

                res.states.append(state)

                # Test
                test = OvalTest('oval:{}_uid_{}:tst:1'.format(id, idx),
                                'file_test', ns=self.__ns__)
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
                    raise ValueError('GID must be positive decimal')
                # State
                state = OvalState('oval:{}_gid_{}:ste:1'.format(id, idx),
                                  'file_state', ns=self.__ns__)

                state.sub_element('group_id')\
                    .set_text(gid)\
                    .set_attr('datatype', 'int')\
                    .set_attr('operation', 'equals')

                res.states.append(state)

                # Test
                test = OvalTest('oval:{}_gid_{}:tst:1'.format(id, idx),
                                'file_test', ns=self.__ns__)
                test.__elements_order__ = (
                    'object',
                    'state',
                )
                test.add_object(obj)
                test.add_state(state)
                res.tests.append(test)

        # definition
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
