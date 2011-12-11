#!/usr/bin/env python
# encoding: utf-8
"""
cheetah.py

Created by Graham Dennis on 2009-02-28.
"""

try:
    from Cheetah.Template import Template
except ImportError:
    Template = None

from waflib import Task, TaskGen

def configure(conf):
    conf.start_msg('Checking for the Cheetah python module')
    if Template:
        conf.end_msg('ok')
    else:
        conf.end_msg('Not found')

class cheetah(Task.Task):
    ext_in  = ['.tmpl']
    ext_out = ['.py']
    vars = ['CHEETAH_SETTINGS']
    
    def run(self):
        env = self.env
        bld = self.generator.bld

        input_node = self.inputs[0]
        output_node = self.outputs[0]

        compilerSettings = 'CHEETAH_SETTINGS' in env and env['CHEETAH_SETTINGS'] or {}

        basename = input_node.change_ext('').name

        pysrc = Template.compile(
            file = input_node.abspath(),
            compilerSettings = compilerSettings,
            moduleName = basename,
            className = basename,
            returnAClass = False,
        )

        output_node.write(pysrc)
        return 0
    

@TaskGen.extension('.tmpl')
def cheetah_callback(self, node):
    out = node.change_ext('.py').name
    self.create_task('cheetah', node, node.parent.find_or_declare(out))
