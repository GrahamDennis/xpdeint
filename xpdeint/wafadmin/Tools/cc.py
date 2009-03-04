#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2006 (ita)

"Base for c programs/libraries"

import os
import TaskGen, Build, Utils, Task
from Logs import debug
import ccroot
from TaskGen import feature, before, extension, after

g_cc_flag_vars = [
'CCDEPS', 'FRAMEWORK', 'FRAMEWORKPATH',
'STATICLIB', 'LIB', 'LIBPATH', 'LINKFLAGS', 'RPATH',
'CCFLAGS', 'CPPPATH', 'CPPFLAGS', 'CCDEFINES']

EXT_CC = ['.c']

TaskGen.bind_feature('cc', ['apply_core'])

g_cc_type_vars = ['CCFLAGS', 'LINKFLAGS']

class cc_taskgen(ccroot.ccroot_abstract):
	pass

@feature('cc')
@before('apply_type_vars')
@after('default_cc')
def init_cc(self):
	self.p_flag_vars = set(self.p_flag_vars).union(g_cc_flag_vars)
	self.p_type_vars = set(self.p_type_vars).union(g_cc_type_vars)

	if not self.env['CC_NAME']:
		raise Utils.WafError("At least one compiler (gcc, ..) must be selected")

@feature('cc')
def apply_obj_vars_cc(self):
	env = self.env
	app = env.append_unique
	cpppath_st = env['CPPPATH_ST']

	# local flags come first
	# set the user-defined includes paths
	for i in env['INC_PATHS']:
		app('_CCINCFLAGS', cpppath_st % i.bldpath(env))
		app('_CCINCFLAGS', cpppath_st % i.srcpath(env))

	# set the library include paths
	for i in env['CPPPATH']:
		app('_CCINCFLAGS', cpppath_st % i)

@feature('cc')
def apply_defines_cc(self):
	self.defines = getattr(self, 'defines', [])
	lst = self.to_list(self.defines) + self.to_list(self.env['CCDEFINES'])
	milst = []

	# now process the local defines
	for defi in lst:
		if not defi in milst:
			milst.append(defi)

	# CCDEFINES_
	libs = self.to_list(self.uselib)
	for l in libs:
		val = self.env['CCDEFINES_'+l]
		if val: milst += val
	self.env['DEFLINES'] = ["%s %s" % (x[0], Utils.trimquotes('='.join(x[1:]))) for x in [y.split('=') for y in milst]]
	y = self.env['CCDEFINES_ST']
	self.env['_CCDEFFLAGS'] = [y%x for x in milst]

@extension(EXT_CC)
def c_hook(self, node):
	# create the compilation task: cpp or cc
	task = self.create_task('cc')
	if getattr(self, 'obj_ext', None):
		obj_ext = self.obj_ext
	else:
		obj_ext = '_%d.o' % self.idx

	task.inputs = [node]
	task.outputs = [node.change_ext(obj_ext)]
	self.compiled_tasks.append(task)
	return task

cc_str = '${CC} ${CCFLAGS} ${CPPFLAGS} ${_CCINCFLAGS} ${_CCDEFFLAGS} ${CC_SRC_F}${SRC} ${CC_TGT_F}${TGT}'
cls = Task.simple_task_type('cc', cc_str, 'GREEN', ext_out='.o', ext_in='.c', shell=False)
cls.scan = ccroot.scan
cls.vars.append('CCDEPS')

link_str = '${LINK_CC} ${CCLNK_SRC_F}${SRC} ${CCLNK_TGT_F}${TGT} ${LINKFLAGS}'
cls = Task.simple_task_type('cc_link', link_str, color='YELLOW', ext_in='.o', shell=False)
cls.maxjobs = 1
cls2 = Task.task_type_from_func('vnum_cc_link', ccroot.link_vnum, cls.vars, color='CYAN', ext_in='.o')
cls2.maxjobs = 1

TaskGen.declare_order('apply_incpaths', 'apply_defines_cc', 'apply_core', 'apply_lib_vars', 'apply_obj_vars_cc', 'apply_obj_vars')

