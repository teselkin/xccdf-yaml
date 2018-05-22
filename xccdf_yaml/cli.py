import logging

from cliff.command import Command
from cliff.lister import Lister
from xccdf_yaml.parsers import PARSERS

from xccdf_yaml.xccdf import Benchmark

from xccdf_yaml.oval import OvalDefinitions

from xccdf_yaml.actions import ConvertYamlAction


class CliConvertYaml(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('filename')
        parser.add_argument('--output-dir', default='output')
        return parser

    def take_action(self, parsed_args):
        action = ConvertYamlAction()
        return action.take_action(parsed_args)


class CliTestXccdf(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        benchmark = Benchmark('test_benchmark')\
            .set_title('Title')\
            .set_description('<b>Description</b>')
        benchmark.add_platform('cpe:/o:canonical:ubuntu_linux:16.04')

        profile = benchmark.add_profile('mos')\
            .set_title('Mirantis uberprofile')

        group = benchmark.add_group('common')
        rule = group.add_rule('etc_os_release_does_not_match_Xerus')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-etc_os_release_does_not_match_Xerus:def:1")
        profile.append_rule(rule, selected=True)

        rule = group.add_rule('bin_dash_has_mode_0755')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-bin_dash_has_mode_0755:def:1")
        profile.append_rule(rule, selected=True)

        rule = group.add_rule('aide_is_installed')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-aide_is_installed:def:1")
        profile.append_rule(rule, selected=True)

        rule = group.add_rule('sysctl_vm_laptop_mode_1')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-sysctl_vm_laptop_mode_1:def:1")
        profile.append_rule(rule, selected=True)

        return str(benchmark)


class CliTestOval(Command):
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        oval_definitions = OvalDefinitions()

        """
        <ns0:definition class="compliance" id="oval:mos-etc_os_release_does_not_match_Xerus:def:1" version="1">
            <ns0:metadata>
                <ns0:title>etc_os_release_does_not_match_Xerus definition</ns0:title>
                <ns0:affected family="unix">
                <ns0:platform>Ubuntu 1604</ns0:platform>
                </ns0:affected>
                <ns0:description>etc_os_release_does_not_match_Xerus definition</ns0:description>
            </ns0:metadata>
            <ns0:criteria operator="OR">
                <ns0:criterion test_ref="oval:mos-etc_os_release_does_not_match_Xerus:tst:1"/>
            </ns0:criteria>
        </ns0:definition>
        """
        definition = oval_definitions\
            .add_definition('oval:mos-etc_os_release_does_not_match_Xerus:def:1')

        definition.add_metadata()\
            .set_title('etc_os_release_does_not_match_Xerus definition')\
            .set_description('etc_os_release_does_not_match_Xerus definition')\
            .set_affected('unix', 'Ubuntu 16.04')

        criteria = definition.add_criteria()
        criteria.add_criterion(test_ref='oval:mos-etc_os_release_does_not_match_Xerus:tst:1')

        """
        <ns0:definition class="compliance" id="oval:mos-bin_dash_has_mode_0755:def:1" version="1">
            <ns0:metadata>
                <ns0:title>bin_dash_has_mode_0755 definition</ns0:title>
                <ns0:affected family="unix">
                <ns0:platform>Ubuntu 1604</ns0:platform>
                </ns0:affected>
                <ns0:description>bin_dash_has_mode_0755 definition</ns0:description>
            </ns0:metadata>
            <ns0:criteria operator="OR">
                <ns0:criterion test_ref="oval:mos-bin_dash_has_mode_0755:tst:1"/>
            </ns0:criteria>
        </ns0:definition>
        """
        definition = oval_definitions\
            .add_definition('oval:mos-bin_dash_has_mode_0755:def:1')

        definition.add_metadata()\
            .set_title('bin_dash_has_mode_0755 definition')\
            .set_description('bin_dash_has_mode_0755 definition')\
            .set_affected('unix', 'Ubuntu 16.04')

        criteria = definition.add_criteria()
        criteria.add_criterion(test_ref='oval:mos-bin_dash_has_mode_0755:tst:1')

        """
        <ns0:definition class="compliance" id="oval:mos-aide_is_installed:def:1" version="1">
            <ns0:metadata>
                <ns0:title>aide_is_installed definition</ns0:title>
                <ns0:affected family="unix">
                    <ns0:platform>Ubuntu 1604</ns0:platform>
                </ns0:affected>
                <ns0:description>aide_is_installed definition</ns0:description>
            </ns0:metadata>
            <ns0:criteria operator="OR">
                <ns0:criterion test_ref="oval:mos-aide_is_installed:tst:1"/>
            </ns0:criteria>
        </ns0:definition>
        """
        definition = oval_definitions\
            .add_definition('oval:mos-aide_is_installed:def:1')

        definition.add_metadata()\
            .set_title('aide_is_installed definition')\
            .set_description('aide_is_installed definition')\
            .set_affected('unix', 'Ubuntu 16.04')

        criteria = definition.add_criteria()
        criteria.add_criterion(test_ref='oval:mos-aide_is_installed:tst:1')

        """
        <ns0:definition class="compliance" id="oval:mos-sysctl_vm_laptop_mode_1:def:1" version="1">
            <ns0:metadata>
                <ns0:title>sysctl_vm_laptop_mode_1 definition</ns0:title>
                <ns0:affected family="unix">
                    <ns0:platform>Ubuntu 1604</ns0:platform>
                </ns0:affected>
                <ns0:description>sysctl_vm_laptop_mode_1 definition</ns0:description>
            </ns0:metadata>
            <ns0:criteria operator="OR">
                <ns0:criterion test_ref="oval:mos-sysctl_vm_laptop_mode_1:tst:1"/>
            </ns0:criteria>
        </ns0:definition>
        """
        definition = oval_definitions\
            .add_definition('oval:mos-sysctl_vm_laptop_mode_1:def:1')

        definition.add_metadata()\
            .set_title('sysctl_vm_laptop_mode_1 definition')\
            .set_description('sysctl_vm_laptop_mode_1 definition')\
            .set_affected('unix', 'Ubuntu 16.04')

        criteria = definition.add_criteria()
        criteria.add_criterion(test_ref='oval:mos-sysctl_vm_laptop_mode_1:tst:1')

        """
        <ns0:tests>
            <ns5:file_test check="all" check_existence="all_exist" comment="bin_dash_has_mode_0755 test"
             id="oval:mos-bin_dash_has_mode_0755:tst:1" version="1">
                <ns5:object object_ref="oval:mos-bin_dash_has_mode_0755:obj:1"/>
                <ns5:state state_ref="oval:mos-bin_dash_has_mode_0755_mode_755:ste:1"/>
                <ns5:state state_ref="oval:mos-bin_dash_has_mode_0755_gid_0:ste:1"/>
                <ns5:state state_ref="oval:mos-bin_dash_has_mode_0755_uid_0:ste:1"/>
            </ns5:file_test>
        </ns0:tests>

        <ns0:objects>
            <ns5:file_object id="oval:mos-bin_dash_has_mode_0755:obj:1" version="1">
                <ns5:filepath>/bin/dash</ns5:filepath>
            </ns5:file_object>
        </ns0:objects>

        <ns5:file_state id="oval:mos-bin_dash_has_mode_0755_mode_755:ste:1" version="1">
            <ns5:uread datatype="boolean">true</ns5:uread>
            <ns5:uwrite datatype="boolean">true</ns5:uwrite>
            <ns5:uexec datatype="boolean">true</ns5:uexec>
            <ns5:gread datatype="boolean">true</ns5:gread>
            <ns5:gwrite datatype="boolean">false</ns5:gwrite>
            <ns5:gexec datatype="boolean">true</ns5:gexec>
            <ns5:oread datatype="boolean">true</ns5:oread>
            <ns5:owrite datatype="boolean">false</ns5:owrite>
            <ns5:oexec datatype="boolean">true</ns5:oexec>
        </ns5:file_state>

        <ns5:file_state id="oval:mos-bin_dash_has_mode_0755_gid_0:ste:1" version="1">
            <ns5:group_id datatype="int" operation="equals">0</ns5:group_id>
        </ns5:file_state>

        <ns5:file_state id="oval:mos-bin_dash_has_mode_0755_uid_0:ste:1" version="1">
            <ns5:user_id datatype="int" operation="equals">0</ns5:user_id>
        </ns5:file_state>
        """
        test = oval_definitions\
            .add_test('file_test', ns='oval-def-unix')\
            .set_attrs({
                'check': "all",
                'check_existence': "all_exist",
                'comment': "bin_dash_has_mode_0755 test",
                'id': "oval:mos-bin_dash_has_mode_0755:tst:1",
                'version': "1",
            })

        obj = oval_definitions\
            .add_object('file_object', ns='oval-def-unix')\
            .set_attrs({
                'id': "oval:mos-bin_dash_has_mode_0755:obj:1",
                'version': "1"
            })
        obj.sub_element('filepath').set_text('/bin/dash')
        test.add_object(obj)

        state = oval_definitions\
            .add_state('file_state', ns='oval-def-unix')\
            .set_attrs({
                'id': "oval:mos-bin_dash_has_mode_0755_mode_755:ste:1",
                'version': "1",
            })
        state.sub_element('uread')\
            .set_attr('datatype', 'boolean').set_text('True')
        state.sub_element('uwrite')\
            .set_attr('datatype', 'boolean').set_text('True')
        state.sub_element('uexec')\
            .set_attr('datatype', 'boolean').set_text('True')
        state.sub_element('gread')\
            .set_attr('datatype', 'boolean').set_text('True')
        state.sub_element('gwrite')\
            .set_attr('datatype', 'boolean').set_text('False')
        state.sub_element('gexec')\
            .set_attr('datatype', 'boolean').set_text('True')
        state.sub_element('oread')\
            .set_attr('datatype', 'boolean').set_text('True')
        state.sub_element('owrite')\
            .set_attr('datatype', 'boolean').set_text('False')
        state.sub_element('oexec')\
            .set_attr('datatype', 'boolean').set_text('True')
        test.add_state(state)

        state = oval_definitions\
            .add_state('file_state', ns='oval-def-unix')\
            .set_attrs({
                'id': "oval:mos-bin_dash_has_mode_0755_gid_0:ste:1",
                'version': "1",
            })
        state.sub_element('group_id')\
            .set_attr('datatype', 'int')\
            .set_attr('operation', 'equals')\
            .set_text('0')
        test.add_state(state)

        state = oval_definitions\
            .add_state('file_state', ns='oval-def-unix')\
            .set_attr('id', "oval:mos-bin_dash_has_mode_0755_uid_0:ste:1")\
            .set_attr('version', '1')
        state.sub_element('user_id')\
            .set_attr('datatype', 'int')\
            .set_attr('operation', 'equals')\
            .set_text('0')
        test.add_state(state)

        """
        <ns0:tests>
            <ns4:dpkginfo_test check="all" check_existence="all_exist" comment="aide_is_installed test"
             id="oval:mos-aide_is_installed:tst:1" version="1">
                <ns4:object object_ref="oval:mos-aide_is_installed:obj:1"/>
            </ns4:dpkginfo_test>
        </ns0:tests>

        <ns0:objects>
            <ns4:dpkginfo_object id="oval:mos-aide_is_installed:obj:1" version="1">
                <ns4:name>aide</ns4:name>
            </ns4:dpkginfo_object>
        </ns0:objects>
        """
        test = oval_definitions\
            .add_test('dpkginfo_test', ns='oval-def-linux')\
            .set_attrs({
                'check': "all",
                'check_existence': "all_exist",
                'comment': "aide_is_installed test",
                'id': "oval:mos-aide_is_installed:tst:1",
                'version': "1",
            })

        obj = oval_definitions\
            .add_object('dpkginfo_object', ns='oval-def-linux')\
            .set_attrs({
                'id': "oval:mos-aide_is_installed:obj:1",
                'version': "1",
            })
        obj.sub_element('name').set_text('aide')
        test.add_object(obj)

        """
        <ns0:tests>
            <ns5:sysctl_test check="all" check_existence="all_exist" comment="sysctl_vm_laptop_mode_1 test"
             id="oval:mos-sysctl_vm_laptop_mode_1:tst:1" version="1">
                <ns5:object object_ref="oval:mos-sysctl_vm_laptop_mode_1:obj:1"/>
                <ns5:state state_ref="oval:mos-sysctl_vm_laptop_mode_1:ste:1"/>
            </ns5:sysctl_test>
        </ns0:tests>

        <ns0:objects>
            <ns5:sysctl_object id="oval:mos-sysctl_vm_laptop_mode_1:obj:1" version="1">
                <ns5:name>vm.laptop_mode</ns5:name>
            </ns5:sysctl_object>
        </ns0:objects>

        <ns5:sysctl_state id="oval:mos-sysctl_vm_laptop_mode_1:ste:1" version="1">
            <ns5:value datatype="int" operation="equals">1</ns5:value>
        </ns5:sysctl_state>
        """
        test = oval_definitions\
            .add_test('sysctl_test', ns='oval-def-unix')\
            .set_attrs({
                'check': "all",
                'check_existence': "all_exist",
                'comment': "sysctl_vm_laptop_mode_1 test",
                'id': "oval:mos-sysctl_vm_laptop_mode_1:tst:1",
                'version': "1",
            })

        obj = oval_definitions\
            .add_object('sysctl_object', ns='oval-def-unix')\
            .set_attrs({
                'id': "oval:mos-sysctl_vm_laptop_mode_1:obj:1",
                'version': "1",
            })
        obj.sub_element('name').set_text('vm.laptop.mode')
        test.add_object(obj)

        """
        <ns0:tests>
            <ns3:textfilecontent54_test check="all" check_existence="none_exist"
             comment="etc_os_release_does_not_match_Xerus test"
             id="oval:mos-etc_os_release_does_not_match_Xerus:tst:1" version="1">
                <ns3:object object_ref="oval:mos-etc_os_release_does_not_match_Xerus:obj:1"/>
            </ns3:textfilecontent54_test>
        </ns0:tests>

        <ns0:objects>
            <ns3:textfilecontent54_object id="oval:mos-etc_os_release_does_not_match_Xerus:obj:1" version="1">
                <ns3:filepath>/etc/os-release</ns3:filepath>
                <ns3:pattern operation="pattern match">Xerus$</ns3:pattern>
                <ns3:instance datatype="int" operation="greater than or equal">1</ns3:instance>
            </ns3:textfilecontent54_object>
        </ns0:objects>
        """
        test = oval_definitions\
            .add_test('textfilecontent54_test', ns='oval-def-indep')\
            .set_attrs({
                'id': 'oval:mos-etc_os_release_does_not_match_Xerus:tst:1',
                'check': 'all',
                'check_existence': 'none_exist',
                'comment': 'etc_os_release_does_not_match_Xerus test',
                'version': '1',
            })

        obj = oval_definitions\
            .add_object('textfilecontent54_object', ns='oval-def-indep')\
            .set_attrs({
                'id': "oval:mos-etc_os_release_does_not_match_Xerus:obj:1",
                'version': "1",
            })

        obj.sub_element('filepath').set_text('/etc/os-release')

        obj.sub_element('pattern')\
            .set_attr('operation', 'pattern match')\
            .set_text('Xerus$')

        obj.sub_element('instance')\
            .set_attrs({
                'datatype': "int",
                'operation': "greater than or equal",
            }).set_text('1')

        test.add_object(obj)

        return str(oval_definitions)


class CliAboutParser(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('name')
        return parser

    def take_action(self, parsed_args):
        cls = PARSERS.get(parsed_args.name)
        print(cls.about())


class CliListParsers(Lister):
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        cols = ('Name', 'About')
        rows = []
        for cls in PARSERS.values():
            rows.append((cls.name(), cls.about()))
        return cols, rows
