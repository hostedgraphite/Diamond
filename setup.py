#!/usr/bin/env python3
# coding=utf-8

import sys
import os
from glob import glob
import distro
import platform


def running_under_virtualenv():
    if hasattr(sys, 'real_prefix'):
        return True
    elif sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return True
    if os.getenv('VIRTUAL_ENV', False):
        return True
    return False


def running_under_conda_env():
    if os.getenv('CONDA_PREFIX', False):
        return True
    return False


from setuptools import setup
setup_kwargs = dict(zip_safe=0)

if os.name == 'nt':
    pgm_files = os.environ["ProgramFiles"]
    base_files = os.path.join(pgm_files, 'diamond')
    data_files = [
        (base_files, ['LICENSE', 'version.txt']),
        (os.path.join(base_files, 'user_scripts'), []),
        (os.path.join(base_files, 'conf'), glob('conf/*.conf.*')),
        (os.path.join(base_files, 'collectors'), glob('conf/collectors/*')),
        (os.path.join(base_files, 'handlers'), glob('conf/handlers/*')),
    ]
    install_requires = ['configobj', 'psutil', ],

else:
    data_files = [
        ('share/diamond', ['LICENSE', 'version.txt']),
        ('share/diamond/user_scripts', []),
    ]

    distro_id = distro.os_release_attr('id')
    distro_major_version = int(distro.os_release_attr('version_id').split('.')[0])
    if not distro_id:
        if 'amzn' in platform.uname()[2]:
            distro_id = 'centos'

    if running_under_virtualenv() or running_under_conda_env():
        data_files.append(('etc/diamond',
                           glob('conf/*.conf.*')))
        data_files.append(('etc/diamond/collectors',
                           glob('conf/collectors/*')))
        data_files.append(('etc/diamond/handlers',
                           glob('conf/handlers/*')))
    else:
        data_files.append(('/etc/diamond',
                           glob('conf/*.conf.*')))
        data_files.append(('/etc/diamond/collectors',
                           glob('conf/collectors/*')))
        data_files.append(('/etc/diamond/handlers',
                           glob('conf/handlers/*')))
        data_files.append(('/var/log/diamond',
                           ['.keep']))

        if distro_id == 'ubuntu':
            if distro_major_version >= 16:
                data_files.append(('/usr/lib/systemd/system', ['rpm/systemd/diamond.service']))
            else:
                data_files.append(('/etc/init', ['debian/diamond.upstart']))
        if distro_id in ['centos', 'redhat', 'debian', 'fedora', 'oracle']:
            data_files.append(('/etc/init.d', ['bin/init.d/diamond']))
            if distro_major_version >= 7 and not distro_id == 'debian':
                data_files.append(('/usr/lib/systemd/system', ['rpm/systemd/diamond.service']))
            elif distro_major_version >= 6 and not distro_id == 'debian':
                data_files.append(('/etc/init', ['rpm/upstart/diamond.conf']))

    # Support packages being called differently on different distros

    # Are we in a virtenv?
    if running_under_virtualenv() or running_under_conda_env():
        install_requires = ['configobj', 'psutil', ]
    else:
        if distro_id in ['debian', 'ubuntu']:
            install_requires = ['configobj', 'psutil', ]
        # Default back to pip style requires
        else:
            install_requires = ['configobj', 'psutil', ]


def get_version():
    """
        Read the version.txt file to get the new version string
        Generate it if version.txt is not available. Generation
        is required for pip installs
    """
    try:
        f = open('version.txt')
    except IOError:
        os.system("./version.sh > version.txt")
        f = open('version.txt')
    version = ''.join(f.readlines()).rstrip()
    f.close()
    return version


def pkgPath(root, path, rpath="/"):
    """
        Package up a path recursively
    """
    global data_files
    if not os.path.exists(path):
        return
    files = []
    for spath in os.listdir(path):
        # Ignore test directories
        if spath == 'test':
            continue
        subpath = os.path.join(path, spath)
        spath = os.path.join(rpath, spath)
        if os.path.isfile(subpath):
            files.append(subpath)
        if os.path.isdir(subpath):
            pkgPath(root, subpath, spath)
    data_files.append((root + rpath, files))


if os.name == 'nt':
    pkgPath(os.path.join(base_files, 'collectors'), 'src/collectors', '\\')
else:
    pkgPath('share/diamond/collectors', 'src/collectors')

version = get_version()

setup(
    name='diamond',
    version=version,
    url='https://github.com/python-diamond/Diamond',
    author='The Diamond Team',
    author_email='diamond@librelist.com',
    license='MIT License',
    description='Smart data producer for graphite graphing package',
    package_dir={'': 'src'},
    packages=['diamond', 'diamond.handler', 'diamond.utils'],
    scripts=['bin/diamond', 'bin/diamond-setup'],
    data_files=data_files,
    python_requires='~=3.8',
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    ** setup_kwargs
)
