#!/usr/bin/env python
# encoding: utf-8
"""
Configuration.py

Created by Graham Dennis on 2009-03-01.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""
import os, sys, imp, shutil

from pkg_resources import resource_filename
from xpdeint.Preferences import xpdeintUserDataPath

import cPickle

VERSION="1.5.3"

xpdeintSourcePlaceholder = 'XPDEINT_SOURCE_PLACEHOLDER.cc'
xpdeintTargetPlaceholder = 'XPDEINT_TARGET_PLACEHOLDER'
buildVariant = 'default'
availableUselib = None
availableVariants = None

wafArguments = {}

def run_waf(command):
    # Step one, setup sys.path as in waf-light
    wafadmin = resource_filename(__name__, 'wafadmin')
    wafdir = os.path.normpath(resource_filename(__name__, '.'))
    tools = os.path.join(wafadmin, 'Tools')
    sys.path = [wafadmin, tools] + sys.path
    
    # Step two, mess with sys.argv so waf thinks it's being asked to configure
    # FIXME: In the future, xpdeint should recognise waf arguments
    sys.argv = ['./waf', command]
    
    # Step three, if the wscript doesn't exist, copy it in
    if not os.path.isfile(os.path.join(xpdeintUserDataPath, 'wscript')):
        wscript_path = resource_filename(__name__, 'support/wscript')
        dest_wscript_path = os.path.join(xpdeintUserDataPath, 'wscript')
        shutil.copyfile(wscript_path, dest_wscript_path)
    
    # Step four, call Scripting as in waf-light
    oldcwd = os.getcwd()
    os.chdir(xpdeintUserDataPath)
    import Scripting
    Scripting.prepare(tools, '.', VERSION, wafdir)
    os.chdir(oldcwd)
    
    sys.path = sys.path[2:]
    
    return 0

config_arg_cache_filename = os.path.join(xpdeintUserDataPath, 'xpdeint_config_arg_cache')


def run_config(includePaths = None, libPaths = None):
    includePaths = includePaths or []
    libPaths = libPaths or []
    
    wafArguments['CPPPATH'] = includePaths
    wafArguments['LIBPATH'] = libPaths
    
    wafArguments.update([(key, value) for key, value in os.environ.iteritems() if key in ['CXX']])
    
    cPickle.dump(wafArguments, file(config_arg_cache_filename, 'w'))
    
    ret = run_waf('configure')
    
    print "Config log saved to ", os.path.join(xpdeintUserDataPath, 'waf_build', 'config.log')
    return ret

def run_reconfig(includePaths = None, libPaths = None):
    includePaths = includePaths or []
    libPaths = libPaths or []
    wafArguments.clear()
    
    if os.path.isfile(config_arg_cache_filename):
        wafArguments.update(cPickle.load(file(config_arg_cache_filename)))
    includePaths.extend(wafArguments.get('CPPPATH', []))
    libPaths.extend(wafArguments.get('LIBPATH', []))
    
    return run_config(includePaths = includePaths, libPaths = libPaths)

g_compile_command = None
g_link_command = None

def waf_compile_command_callback(cmd):
    global g_compile_command
    g_compile_command = cmd

def waf_link_command_callback(cmd):
    global g_link_command
    g_link_command = cmd

def run_build(source_name, target_name, variant = 'default', buildKWs = {}):
    global g_compile_command
    global g_link_command
    g_compile_command = g_link_command = None
    
    wafArguments.clear()
    wafArguments.update(buildKWs)
    
    global buildVariant
    buildVariant = variant
    
    # Silence waf!
    def dont_log(str):
        pass
    import logging
    old_info = logging.info
    logging.info = dont_log
    
    placeholderFilePath = os.path.join(xpdeintUserDataPath, xpdeintSourcePlaceholder)
    if not os.path.isfile(placeholderFilePath):
        f = file(os.path.join(xpdeintUserDataPath, xpdeintSourcePlaceholder), 'w')
        f.write("/* Placeholder file created by xpdeint to keep waf happy */")
        f.close()
    
    run_waf('build')
    logging.info = old_info
    
    if not variant in availableVariants:
        if variant == 'mpi':
            print "xpdeint could not find MPI. Do you have an MPI library (like OpenMPI) installed?"
            print "If you do, run 'xpdeint --reconfigure' to find it."
        else:
            print "xpdeint could not find build variant '%s'." % variant
        return
    
    missing_uselib = set(buildKWs['uselib']).difference(availableUselib)
    if missing_uselib:
        print "This script requires libraries or features that xpdeint could not find."
        print "Make sure these requirements are installed and then run 'xpdeint --reconfigure'."
        print "The missing feature(s) were: %s." % ', '.join(missing_uselib)
        return
    
    # return build command
    source_name = '"' + source_name + '"'
    target_name = '"' + target_name + '"'
    
    compile_command = g_compile_command.strip().replace(os.path.join('..', xpdeintSourcePlaceholder), source_name)
    link_command = g_link_command.strip().replace(os.path.join(variant, xpdeintTargetPlaceholder), target_name)
    
    return ' '.join([compile_command, link_command])

