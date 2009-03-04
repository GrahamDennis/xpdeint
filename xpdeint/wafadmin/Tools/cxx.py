#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2005 (ita)

"Base for c++ programs and libraries"

import TaskGen, Task, Utils
from Logs import debug
import ccroot # <- do not remove
from TaskGen import feature, before, extension, after

g_cxx_flag_vars = [
'CXXDEPS', 'FRAMEWORK', 'FRAMEWORKPATH',
'STATICLIB', 'LIB', 'LIBPATH', 'LINKFLAGS', 'RPATH',
'CXXFLAGS', 'CCFLAGS', 'CPPPATH', 'CPPFLAGS', 'CXXDEFINES']
"main cpp variables"

EXT_CXX = ['.cpp', '.cc', '.cxx', '.C', '.c++']

TaskGen.bind_feature('cxx', ['apply_core'])

g_cxx_type_vars=['CXXFLAGS', 'LINKFLAGS']
class cxx_taskgen(ccroot.ccroot_abstract):
	pass

@feature('cxx')
@before('apply_type_vars')
@after('default_cc')
def init_cxx(self):
	if not 'cc' in self.features:
		self.mappings['.c'] = TaskGen.task_gen.mappings['.cxx']

	self.p_flag_vars = set(self.p_flag_vars).union(g_cxx_flag_vars)
	self.p_type_vars = set(self.p_type_vars).union(g_cxx_type_vars)

	if not self.env['CXX_NAME']:
		raise Utils.WafError("At least one compiler (g++, ..) must be selected")

@feature('cxx')
def apply_obj_vars_cxx(self):
	env = self.env
	app = env.append_unique
	cxxpath_st = env['CPPPATH_ST']

	# local flags come first
	# set the user-defined includes paths
	for i in env['INC_PATHS']:
		app('_CXXINCFLAGS', cxxpath_st % i.bldpath(env))
		app('_CXXINCFLAGS', cxxpath_st % i.srcpath(env))

	# set the library include paths
	for i in env['CPPPATH']:
		app('_CXXINCFLAGS', cxxpath_st % i)

@feature('cxx')
def apply_defines_cxx(self):
	self.defines = getattr(self, 'defines', [])
	lst = self.to_list(self.defines) + self.to_list(self.env['CXXDEFINES'])
	milst = []

	# now process the local defines
	for defi in lst:
		if not defi in milst:
			milst.append(defi)

	# CXXDEFINES_USELIB
	libs = self.to_list(self.uselib)
	for l in libs:
		val = self.env['CXXDEFINES_'+l]
		if val: milst += self.to_list(val)

	self.env['DEFLINES'] = ["%s %s" % (x[0], Utils.trimquotes('='.join(x[1:]))) for x in [y.split('=') for y in milst]]
	y = self.env['CXXDEFINES_ST']
	self.env['_CXXDEFFLAGS'] = [y%x for x in milst]

@extension(EXT_CXX)
def cxx_hook(self, node):
	# create the compilation task: cpp or cc
	task = self.create_task('cxx')
	if getattr(self, 'obj_ext', None):
		obj_ext = self.obj_ext
	else:
		obj_ext = '_%d.o' % self.idx

	task.inputs = [node]
	task.outputs = [node.change_ext(obj_ext)]
	self.compiled_tasks.append(task)
	return task

cxx_str = '${CXX} ${CXXFLAGS} ${CPPFLAGS} ${_CXXINCFLAGS} ${_CXXDEFFLAGS} ${CXX_SRC_F}${SRC} ${CXX_TGT_F}${TGT}'
cls = Task.simple_task_type('cxx', cxx_str, color='GREEN', ext_out='.o', ext_in='.cxx', shell=False)
cls.scan = ccroot.scan
cls.vars.append('CXXDEPS')

link_str = '${LINK_CXX} ${CXXLNK_SRC_F}${SRC} ${CXXLNK_TGT_F}${TGT} ${LINKFLAGS}'
cls = Task.simple_task_type('cxx_link', link_str, color='YELLOW', ext_in='.o', shell=False)
cls.maxjobs = 1
cls2 = Task.task_type_from_func('vnum_cxx_link', ccroot.link_vnum, cls.vars, color='CYAN', ext_in='.o')
cls2.maxjobs = 1

TaskGen.declare_order('apply_incpaths', 'apply_defines_cxx', 'apply_core', 'apply_lib_vars', 'apply_obj_vars_cxx', 'apply_obj_vars')

