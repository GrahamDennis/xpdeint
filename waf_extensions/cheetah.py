#!/usr/bin/env python
# encoding: utf-8
"""
cheetah.py

Created by Graham Dennis on 2009-02-22.
"""

import Task
from TaskGen import extension

EXT_CHEETAH = ['.tmpl']

cheetah_str = "${CHEETAH} compile --settings='${CHEETAH_SETTINGS}' ${SRC} >/dev/null"

@extension(EXT_CHEETAH)
def cheetah_hook(self, node):
    tsk = self.create_task('cheetah')
    tsk.set_inputs(node)
    # Cheating
    tsk.__class__.quiet = True
    # tsk.set_outputs(node.change_ext('.py'))

Task.simple_task_type('cheetah', cheetah_str, color='YELLOW')

def detect(conf):
    conf.find_program('cheetah', var='CHEETAH', mandatory = True)

