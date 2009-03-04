#!/usr/bin/env python
# encoding: utf-8
"""
cheetah.py

Created by Graham Dennis on 2009-02-28.
"""

import Task
from TaskGen import taskgen, extension
import os

EXT_CHEETAH = ['.tmpl']

@extension(EXT_CHEETAH)
def cheetah_hook(self, node):
    tsk = self.create_task('cheetah', self.env)
    tsk.set_inputs(node)
    # Cheating
    tsk.__class__.quiet = True
    # tsk.set_outputs(node.change_ext('.py'))

def detect(conf):
    conf.check_message_1("Checking for Cheetah module")
    try:
        from xpdeint.Utilities import leopardWebKitHack
        leopardWebKitHack()
        from Cheetah.Template import Template
    except ImportError:
        conf.fatal('The Cheetah module for Python was not found.')
    conf.check_message_2("ok")

def cheetah_build(task):
    from Cheetah.Template import Template
    
    env = task.env
    bld = task.generator.bld
    
    node = task.inputs[0]
    
    compiled_path = os.path.splitext(node.abspath(env))[0] + '.py'
    
    compilerSettings = 'CHEETAH_SETTINGS' in env and env['CHEETAH_SETTINGS'] or {}
    
    basename = node.file_base()
    
    pysrc = Template.compile(
        file = node.abspath(env),
        compilerSettings = compilerSettings,
        moduleName = basename,
        className = basename,
        returnAClass = False,
    )
    out_f = file(compiled_path, 'w')
    out_f.write(pysrc)
    out_f.close()
    return 0

Task.task_type_from_func('cheetah', cheetah_build)

