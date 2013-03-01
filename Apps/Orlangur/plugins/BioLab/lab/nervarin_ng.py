#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Fabric based server admins tool
"""
from __future__ import print_function
from fabric.contrib.files import append

__author__ = "Alexey 'Averrin' Nabrodov <averrin@gmail.com>"
__version__ = '-1.8.2- NG 0.1'
__deps__ = ['fabric', 'mongate']

import os, sys
#from fabulous.color import *

#try:
from fabric.context_managers import hide
from fabric.api import *
from fabric.colors import *
from fabric.decorators import task
from fabric import state
from fabric.operations import open_shell
from mongate.connection import Connection
from optparse import OptionParser
import pystache
#except ImportError:
#     print('Install deps:')
#     print('pip install %s' % ', '.join(__deps__))
#     exit(1)


# Connection
ORLANGUR_SERVER = 'en.averr.in'
ORLANGUR_PORT = 27080
ORLANGUR_USER = 'averrin'
ORLANGUR_PASWD = 'aqwersdf'
url = 'http://%s:%s/orlangur/_authenticate' % (ORLANGUR_SERVER, ORLANGUR_PORT)
data = {'username': ORLANGUR_USER, 'password': ORLANGUR_PASWD}

def connect():
    try:
        import urllib2, urllib

        req = urllib2.Request(url, urllib.urlencode(data))
        urllib2.urlopen(req).read()
    except ImportError:
        from urllib.error import URLError
        import urllib.request as req
        import urllib.parse as parse

        r = req.Request(url, parse.urlencode(data).encode('utf8'))
        req.urlopen(r).read()

    connection = Connection(ORLANGUR_SERVER, ORLANGUR_PORT)
    globals()['db'] = connection.orlangur
    return connection.orlangur


if os.path.basename(sys.argv[0]) == 'fab':
    home_folder = os.path.split(os.path.abspath(env['fabfile']))[0] + '/'
elif os.path.basename(sys.argv[0]) == 'ipython':
    home_folder = os.path.abspath('.')
else:
    home_folder = os.path.split(os.path.abspath(sys.argv[0]))[0] + '/'


def dump_to_file(filename, text, mod=777):
    with open(os.path.join(home_folder, '.temp/', filename), 'w') as f:
        f.write(text)
        os.system('chmod %s %s' % (mod, os.path.join(home_folder, '.temp/', filename)))
    return os.path.join(home_folder, '.temp/', filename)


@task
def get_info():
    """
        Get server info
    """
    env.warn_only = True
    run('lsb_release -a', shell=False)
    run('uname -a', shell=False)
    run('uptime', shell=False)
    env.warn_only = False


def get_server(server_alias):
    return db.en_servers.find({'alias': server_alias})[0]


@task
def shell(native=False, tmux=True):
    """
        Open common ssh shell
    """
    print(config)
    if native or eval(str(native)):
        print('Opening native fabric shell')
        open_shell(config['ssh_startup'] if eval(str(tmux)) else '')
    else:
        print('Opening ssh shell')
        key = server['ssh_cert']
        password = server['ssh_password']
        if key:
            key = '-i ' + os.path.join(home_folder, '.temp/', key)
            # ssh = "sshpass -p '%s' ssh %s -p %s %s %s" % (password,
        ssh = "ssh %s -p %s %s %s" % (
            '%(ssh_user)s@%(ip)s' % server,
            server['ssh_port'],
            key,
            "-t '%s'" % config['ssh_startup'] if eval(str(tmux)) else '')
        #        if platform.system() == 'Linux':
        #            ssh = "sshpass -p '%s' %s" % (password, ssh)
        #        else:
        #            print(password)
        print(ssh)
        os.system(ssh)


def list():
    for s in connect().en_servers.find():
        line = blue(' >  ', bold=True) +\
               s['alias'] +\
               blue(u' — %(description)s [' % s, bold=True) +\
               green(s['ip'], bold=True) +\
               blue(']', bold=True)
        try:
            print(line.encode('utf8'))
        except UnicodeEncodeError:
            print(line.encode('cp1251'))


def exec_cmd(cmd, use_sudo=False):
    runner = run
    if use_sudo:
        runner = sudo
    #    state.output['running'] = False
    runner(cmd)


def infect():
    put(os.path.join(home_folder, 'symbiont.py'), '.')
    sudo('pip install redis')
    sudo('nohup python symbiont.py %s > /dev/null &' % server['alias'], pty=False)


def infect_all(*servers):
    for server_alias in servers:
        server = get_server(server_alias)
        env.host_string = '%(ssh_user)s@%(ip)s' % server
        env.passwords[env.host_string] = server['ssh_password']
        globals()['server'] = server
        infect()
        
        
def render_config(title, context):
    content = pystache.render(db.en_configs.find({'title': title})[0]['content'], context)
    return content.encode('utf8')


def init():
    """
        Install must-have tools like tmux, zsh and others
    """
    env.warn_only = True
    for p in config['packages']:
        sudo('apt-get install %s -y' % p)
    for p in config['pip_packages']:
        sudo('pip install %s' % p)
    run('curl -L https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh | sh')
    env.warn_only = False
    path = run('which zsh')
    append('~/.tmux.conf', render_config('~/.tmux.conf', {'shell': path}), escape=True)
    append('~/.zshrc', render_config('~/.zshrc', {'alias': server['alias']}), escape=True)

    run('git config --global user.email "averrin@gmail.com"')
    run('git config --global user.name "Alexey Nabrodov"')
    

def main(argv, args):
    task = None
    local_task = True

    if args.args:
        if '-a' in argv:
            argv.remove('-a')
        if '--args' in argv:
            argv.remove('--args')
        for a in args.args:
            argv.remove(a)

        #    print(argv, args)
        #    return

    if len(argv) == 2:
        task_name = argv[1]

        if task_name in globals():
            task = globals()[task_name]


    elif len(argv) == 3:
        task_name = argv[2]

        if task_name in globals():
            task = globals()[task_name]
            server_alias = argv[1]
            local_task = False

    else:
        print('Not en(mistyped) arguments')

    if task is not None:
        if not local_task:
            server = get_server(server_alias)
            env.host_string = '%(ssh_user)s@%(ip)s' % server
            env.passwords[env.host_string] = server['ssh_password']

            globals()['server'] = server

        config = db.en_clients.find({'title': 'Nervarin'})[0]
        globals()['config'] = config

        if args.args is not None:
            task(*args.args)
        else:
            task()

    else:
        print('Unknown task')


def cb(option, opt_str, value, parser):
    args = []
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)

parser = OptionParser()
parser.add_option("-a", "--args", help="task arguments", action="callback", callback=cb, dest="args")
if __name__ == '__main__':
    connect()
    main(sys.argv, parser.parse_args()[0])
    