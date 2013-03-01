from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.baseQt import SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons
from winterstone.base import WinterPlugin
import pip

from subprocess import *

import IPython.utils.coloransi as coloransi


class PipHelper(object):
    def install(self, *packeges):
        args = ['install']
        args.extend(packeges)
        pip.main(args)

class Nervarin(object):
    def __init__(self, main, python):
        self.main = main
        self.python = python

    def local(self, cmd, *args):
        cmd = [self.python, self.main, cmd]
        if args:
            cmd.append('-a')
            for a in args:
                cmd.append(a)

        self.ex(cmd, 'local')

    def ex(self, cmd, alias, noprint=False):
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        self.stdout, self.stderr = p.communicate()
        self.stdout = self.stdout.decode()
        self.stderr = self.stderr.decode()
        if not noprint:
            header = '[Nervarin:%s]:\n' % alias
            tb = coloransi.TermColors()
            print(tb.Red + 'Out ' + tb.Normal + header + self.stdout)
        else:
            return self.stdout, self.stderr

    def remote(self, alias, cmd, *args):
        if not type(alias) == str:
            alias = alias['alias']
        cmd = [self.python, self.main, alias, cmd]
        if args:
            cmd.append('-a')
            for a in args:
                cmd.append(a)
        self.ex(cmd, alias)

    def list(self):
        self.local('list')

    def info(self, alias):
        self.remote(alias, 'get_info')

class Test(WinterPlugin):
    def activate(self):
#        self.api.createSBAction('hand-down', 'Nervarin', QWidget(), toolbar=True)

        self.nervarin = Nervarin(self.config.options.nervarin, self.config.options.interpreter)
        self.nervarin.api = self.api

        self.api.pushToIP({'nervarin': self.nervarin})
        self.api.pushToIP({'pip': PipHelper()})

        self.active = True
        return True

    def deactivate(self):
        self.api.info('trololo')
        self.active = False
        return True
