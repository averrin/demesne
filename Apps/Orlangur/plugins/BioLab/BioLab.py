from PyQt4.QtGui import *
from PyQt4.QtCore import *
import json
from time import sleep
from winterstone.baseQt import SBAction
from winterstone.base import WinterPlugin

from everstone.baseQt import Stream

from datetime import datetime

from IPython.utils import io


from functools import partial
import IPython.utils.coloransi as coloransi
from collections import UserDict

class Server(UserDict):

    def printOutput(self):
        tb = coloransi.TermColors()
        header = '[Symbiont:%s]:\n' % self['alias']
        print(tb.Red + 'Out ' + tb.Normal + header + self.output)

class BioLab(WinterPlugin):
    def activate(self):
#        self.output = QListWidget()
        self.targets = QListWidget()

        self.targets.itemDoubleClicked.connect(self._sendCmd)
        self.targets.setContextMenuPolicy(Qt.CustomContextMenu)
        self.targets.customContextMenuRequested.connect(self.openMenu)

        panel = QWidget()
        panel.setLayout(QVBoxLayout())

        panel.layout().addWidget(self.targets)
#        panel.layout().addWidget(self.output)


        self.action = self.api.createSBAction('erlenmeyer', 'BioLab', panel, toolbar=True)
        self.action.setEmblem('gray')

        panel.onShow = self.action.reset
        
        self.stream = Stream(self.config.options.channels, raw_log=False)

        self.stream.subscribe(['answer:*'])
        
        self.stream.listen()

        self.api.async(lambda: self.api.getCollection('en_servers'), self.fillList)

        self.stream.addHandler('online', self.receiveOnline)
        self.stream.addHandler('answer:*', self.receiveDefault)

        self.active = True

        return True

    def openMenu(self, point):
        item = self.targets.itemAt(point)
        item.menu.exec_(self.targets.mapToGlobal(point))

    def fillList(self, list):
        self.servers = {}
        for server in sorted(list, key=lambda x: x['alias']):
            server = Server(server)
            self.servers[server['alias']] = server
            self.servers[server['alias']].state = 'offline'
            i = QListWidgetItem(server['alias'])
            i.target = server['alias']
            i.menu = QMenu()
#            s = QAction('Stealth', self.targets)
#            s.triggered.connect(lambda: self.stream.publish('commands:%s' % i.target, 'sym:stealth'))  # not triggred=(
            cmd = 'sym:stealth'.encode('utf8')
            ch = 'commands:%s' % i.target
#            print(ch, cmd)
            i.menu.addAction('Stealth', lambda: self.stream.publish(ch, cmd))
            self.targets.addItem(i)
            self.bg = i.background()

            self.api.pushToIP({i.target: server})
            server.cmd = partial(self.sendCmd, server)

        self.watcher = self.Watcher(self)
        self.watcher.connect(self.watcher, SIGNAL('setColor'), self.setState)
        self.watcher.start()

    def setState(self, item, state):
        item.state = state
        if state == 'online':
            item.setBackground(QColor('lightgreen'))
            item.setIcon(QIcon(self.api.icons['green']))

        elif state == 'busy':
            item.setBackground(QColor('#ffccaa'))
            item.setIcon(QIcon(self.api.icons['orange']))

        else:
            item.setBackground(self.bg)
            item.setIcon(QIcon(self.api.icons['gray']))

    
    def receiveDefault(self, channel, pattern, msg):
        m = msg['msg']
        if m[0]:
            m = m[0]
        else:
            m = m[1]
        self.api.selectTab('Console')
        alias = msg['hostname']
        self.servers[alias].output = m
        self.api.echoServerOutput(alias)
        self.action.setEmblem('green')

    def receiveOnline(self, channel, pattern, msg):
        if hasattr(self, 'servers'):
            self.servers[msg['hostname']].state = msg['msg']


    def _sendCmd(self, item):
        self.api.selectTab('Console')
        self.api.setIPInput('%s.cmd("")' % item.target)
        self.api.setIPCursor(-2)

    def sendCmd(self, server, cmd):
#        self.api.set_input(item.target)
#        cmd, status = QInputDialog.getText(QWidget(), 'Exec command', 'Command')
#        print(server, cmd)
        self.stream.publish('commands:%s' % server['alias'], json.dumps(cmd))


    class Watcher(QThread):

        def __init__(self, parent):
            QThread.__init__(self)
            self.parent = parent

        def run(self):
            while True:
                for i in range(self.parent.targets.count()):
                    item = self.parent.targets.item(i)
                    self.emit(SIGNAL('setColor'), item, self.parent.servers[item.target].state)
                    self.parent.servers[item.target].state = 'offline'

                sleep(2)






    def receiveLog(self, channel, pattern, msg):
        msg['who'] = channel.replace('log:', '')
        self.output.addItem(self.api.makeMessage('%(who)s: %(level)s :: %(msg)s' % msg))
        

    def deactivate(self):
        self.active = False
        return True

