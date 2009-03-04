#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy 2008

"""MacOSX related tools

To compile an executable into a Mac application bundle (a .app), set its 'mac_app' attribute
  obj.mac_app = True

To make a bundled shared library (a .bundle), set the 'mac_bundle' attribute:
  obj.mac_bundle = True
"""

import os, shutil, sys, platform
import TaskGen, Task, Build, Options
from TaskGen import taskgen, feature, after, before
from Logs import error, debug


# see WAF issue 285
# and also http://trac.macports.org/ticket/17059
@feature('cc', 'cxx')
@before('apply_lib_vars')
def set_macosx_deployment_target(self):
	if self.env['MACOSX_DEPLOYMENT_TARGET']:
		os.environ['MACOSX_DEPLOYMENT_TARGET'] = self.env['MACOSX_DEPLOYMENT_TARGET']
	elif 'MACOSX_DEPLOYMENT_TARGET' not in os.environ:
		if sys.platform == 'darwin':
			os.environ['MACOSX_DEPLOYMENT_TARGET'] = '.'.join(platform.mac_ver()[0].split('.')[:2])



@feature('cc', 'cxx')
@after('apply_lib_vars')
def apply_framework(self):
	for x in self.to_list(self.env['FRAMEWORKPATH']):
		frameworkpath_st = '-F%s'
		self.env.append_unique('CXXFLAGS', frameworkpath_st % x)
		self.env.append_unique('CCFLAGS', frameworkpath_st % x)
		self.env.append_unique('LINKFLAGS', frameworkpath_st % x)

	for x in self.to_list(self.env['FRAMEWORK']):
		self.env.append_value('LINKFLAGS', ['-framework', x])

@taskgen
def create_task_macapp(self):
	if 'cprogram' in self.features and self.link_task:
		apptask = self.create_task('macapp', self.env)
		apptask.set_inputs(self.link_task.outputs)
		apptask.set_outputs(self.link_task.outputs[0].change_ext('.app'))
		self.apptask = apptask

@after('apply_link')
@feature('cc', 'cxx')
def apply_link_osx(self):
	"""Use env['MACAPP'] to force *all* executables to be transformed into Mac applications
	or use obj.mac_app = True to build specific targets as Mac apps"""
	if self.env['MACAPP'] or getattr(self, 'mac_app', False):
		self.create_task_macapp()
		name = self.link_task.outputs[0].name
		if getattr(self, 'vnum', None):
			name = name.replace('.dylib', '.%s.dylib' % self.vnum)

		path = os.path.join(self.env['PREFIX'], 'lib', name)
		self.env.append_value('LINKFLAGS', '-install_name')
		self.env.append_value('LINKFLAGS', path)

@before('apply_link', 'apply_lib_vars')
@feature('cc', 'cxx')
def apply_bundle(self):
	"""use env['MACBUNDLE'] to force all shlibs into mac bundles
	or use obj.mac_bundle = True for specific targets only"""
	if not ('cshlib' in self.features or 'shlib' in self.features): return
	if self.env['MACBUNDLE'] or getattr(self, 'mac_bundle', False):
		self.env['shlib_PATTERN'] = self.env['macbundle_PATTERN']
		uselib = self.uselib = self.to_list(self.uselib)
		if not 'MACBUNDLE' in uselib: uselib.append('MACBUNDLE')

@after('apply_link')
@feature('cshlib')
def apply_bundle_remove_dynamiclib(self):
	if self.env['MACBUNDLE'] or getattr(self, 'mac_bundle', False):
		if not getattr(self, 'vnum', None):
			self.env['LINKFLAGS'].remove('-dynamiclib')

app_dirs = ['Contents', os.path.join('Contents','MacOS'), os.path.join('Contents','Resources')]

app_info = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist SYSTEM "file://localhost/System/Library/DTDs/PropertyList.dtd">
<plist version="0.9">
<dict>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleGetInfoString</key>
	<string>Created by Waf</string>
	<key>CFBundleSignature</key>
	<string>????</string>
	<key>NOTE</key>
	<string>THIS IS A GENERATED FILE, DO NOT MODIFY</string>
	<key>CFBundleExecutable</key>
	<string>%s</string>
</dict>
</plist>
'''

def app_build(task):
	global app_dirs
	env = task.env

	i = 0
	for p in task.outputs:
		srcfile = p.srcpath(env)

		debug('osx: creating directories')
		try:
			os.mkdir(srcfile)
			[os.makedirs(os.path.join(srcfile, d)) for d in app_dirs]
		except (OSError, IOError):
			pass

		# copy the program to the contents dir
		srcprg = task.inputs[i].srcpath(env)
		dst = os.path.join(srcfile, 'Contents', 'MacOS')
		debug('osx: copy %s to %s' % (srcprg, dst))
		shutil.copy(srcprg, dst)

		# create info.plist
		debug('osx: generate Info.plist')
		# TODO:  Support custom info.plist contents.

		f = file(os.path.join(srcfile, "Contents", "Info.plist"), "w")
		f.write(app_info % os.path.basename(srcprg))
		f.close()

		i += 1

	return 0

def install_shlib(task):
	"""see http://code.google.com/p/waf/issues/detail?id=173"""
	nums = task.vnum.split('.')

	path = self.install_path

	libname = task.outputs[0].name

	name3 = libname.replace('.dylib', '.%s.dylib' % task.vnum)
	name2 = libname.replace('.dylib', '.%s.dylib' % nums[0])
	name1 = libname

	filename = task.outputs[0].abspath(task.env)
	bld = task.outputs[0].__class__.bld
	bld.install_as(path + name3, filename, env=task.env)
	bld.symlink_as(path + name2, name3)
	bld.symlink_as(path + name1, name3)

@feature('osx')
@after('install_target_cshlib')
def install_target_osx_cshlib(self):
	if not Options.is_install: return
	if getattr(self, 'vnum', '') and sys.platform != 'win32':
		self.link_task.install = install_shlib

Task.task_type_from_func('macapp', vars=[], func=app_build, after="cxx_link cc_link ar_link_static")

