__author__ = 'Averrin'

from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from winterstone.baseQt import SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons
from winterstone.base import WinterPlugin

from IPython.kernel.inprocess.ipkernel import InProcessKernel
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.inprocess_kernelmanager import QtInProcessKernelManager
from IPython.lib import guisupport
import IPython.utils.coloransi as coloransi

class WinterTerminal(QWidget):
    def __init__(self, app, imports=None, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.app = app
        qtapp = self.app.getApp()
        kernel = InProcessKernel(gui='qt5')
        self.kernel = kernel
        self.shell = kernel.shell

        # Populate the kernel's namespace.
        kernel.shell.push({'api': self.app.api, 'self': self.app, 'shell': kernel.shell})

        for plugin in self.app.pm.plugins:
            self.shell.push({plugin.name: plugin})

        self.push = kernel.shell.push
        self.ex = kernel.shell.ex


        # Create a kernel manager for the frontend and register it with the kernel.
        km = QtInProcessKernelManager(kernel=kernel)
        km.start_channels()
        kernel.frontends.append(km)

        # Create the Qt console frontend.
        control = RichIPythonWidget()
        control.exit_requested.connect(qtapp.quit)
        control.kernel_manager = km
        control.show()

        self.widget = control

        self.imports = [
            'from PyQt4.QtCore import *',
            'from PyQt4.QtGui import *',
            'import json',
            'import os, sys'
        ]
        if imports is not None and type(imports) is list:
            self.imports.extend(imports)
        for import_line in self.imports:
            kernel.shell.ex(import_line)



        self.setLayout(QVBoxLayout())
        self.layout().addWidget(control)
#        self.addTab(control, 'Main')

        control.clear()

        self.app.api.echo = self.echo
        self.app.api.echoServerOutput = self.echoServerOutput
        self.app.api.setIPInput = self.set_input
        self.app.api.pushToIP = self.shell.push
        self.app.api.setIPCursor = self.setCursorPos

    def setCursorPos(self, pos):
        self.widget._control.setFocus(Qt.MouseFocusReason)
        cursor = self.widget._get_prompt_cursor()
        if pos < 0:
            move = cursor.Left
            cursor.movePosition(cursor.EndOfLine)
        else:
            move = cursor.Right
            cursor.movePosition(cursor.StartOfLine)

        for i in range(0, abs(pos)):
            cursor.movePosition(move)

        self.widget._control.setTextCursor(cursor)

    def set_input(self, input):
        self.widget._set_input_buffer(input)

    def echo(self, msg, header=None):
        if not header is None:
            tb = coloransi.TermColors()
            msg = tb.Red + header + tb.Normal + '\n' + msg
        self.shell.push({'output': msg})
        self.set_input('print(output)')
        self.widget.execute()

    def echoServerOutput(self, server):
        self.set_input('%s.printOutput()' % server)
        self.widget.execute()


class WinterTermManager(QTabWidget):
    def __init__(self, app):
        QTabWidget.__init__(self)
        self.app = app
        self.terminals = {}

        self.setTabsClosable(True)
        self.setMovable(True)

        self.tabCloseRequested.connect(self.closeTab)

        self.addTerm('Main')

        self.app.createAction(QIcon(), 'Add terminal', self.addTerm, keyseq='Ctrl+T')

    def closeTab(self, index):
        if index:
            self.removeTab(index)

    def setTerminalName(self, title):
        self.setTabText(self.currentIndex(), title)



    def getCurrentTerminal(self):
        return self.currentWidget()

    def addTerm(self, title=None):
        if title is None:
            title = 'Terminal %s' % self.count()

        self.terminals[title] = WinterTerminal(self.app)
        self.addTab(self.terminals[title], title)

        self.setCurrentIndex(self.count() - 1)
