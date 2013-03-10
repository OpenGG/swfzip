#!/usr/bin/python
import os
import subprocess

source = 'swfzip.py'
target = 'swfunzip.py'

if not os.path.exists(source):
    raise Exception(source+' not existed.')


if os.path.exists(target):
    raise Exception(target+' existed.')

if 'symlink' in dir(os):
    os.symlink(source, target)
else:
    p = subprocess.Popen(
            'mklink {target} {source}'.format(
                source = source,
                target = target
                ),
            shell=True,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
        )
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print stderr
        raise Exception('symlink error')

print 'symlinking done.'