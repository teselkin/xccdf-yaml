from xccdf_yaml.xccdf import BenchmarkRule
import os

class CmdExecParser(object):
    def __init__(self, parsed_args=None):
        self.parsed_args = parsed_args

    def parse(self, id, metadata):
        rule = BenchmarkRule(id)
        if 'title' in metadata:
            rule.set_title(metadata['title'])
        if 'description' in metadata:
            rule.set_description(metadata['description'])

        if 'cmd' in metadata:
            filename = '{}.sh'.format(id)
            target_filename = os.path.join(self.parsed_args.output_dir,
                                           filename)
            with open(target_filename, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write(metadata['cmd'])
                f.write('\n')
        elif 'filename' in metadata:
            filename = metadata['filename']
            target_filename = os.path.join(self.parsed_args.output_dir,
                                           filename)
        else:
            raise Exception('No script or cmdline found')

        rule.add_check(system_ns='sce')\
            .check_import({'import-name': 'stdout'})\
            .check_content_ref({'href': filename})

        return rule
