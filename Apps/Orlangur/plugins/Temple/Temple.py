from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.baseQt import SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons
from winterstone.base import WinterPlugin

import paramiko as ssh
import json
import logging

import os

#from fabric.tasks import *

#print(execute(lambda: run('ls'), hosts=["averrin@192.168.0.101"]))

class Test(WinterPlugin):
    def activate(self):
        self.panel = QWidget()
        self.panel.setLayout(QVBoxLayout())
        self.log = QTextBrowser()
        self.list = QComboBox()

        self.panel.setAcceptDrops(True)
        self.panel.dragEnterEvent = self.dragEnterEvent
        self.panel.dropEvent = self.dropEvent
        
#        print(self.log.dropEvent)

        self.list.currentIndexChanged.connect(self.lch)
        
        self.panel.layout().addWidget(self.list)
        self.panel.layout().addWidget(self.log)
        
        self.api.createSBAction('cloud-minus', 'Temple', self.panel, toolbar=True)

        self.log.setText('Connecting...')
        self.api.async(lambda: self.api.getCollection('en_servers', os='linux'), self.fillList)

        self.active = True
        return True
    
    def dragEnterEvent(self, event):
        fpf = 'application/x-qt-windows-mime;value="FileNameW"'
        if fpf in event.mimeData().formats():
            b = bytes(event.mimeData().data(fpf).replace(b'\x00', b''))
            path = b.decode('utf8')
            print(path)
            event.acceptProposedAction()
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        fpf = 'application/x-qt-windows-mime;value="FileNameW"'
        if fpf in event.mimeData().formats():
            b = bytes(event.mimeData().data(fpf).replace(b'\x00', b''))
            path = b.decode('utf8')
            event.accept()
            self.sftp.put(path, '.')
            server = self.list.itemText(self.list.currentIndex())
            self.connectTo(server, self.setRetText, self.setErrText)


    def lch(self, item):
        server = self.list.itemText(item)
        self.connectTo(server, self.setRetText, self.setErrText)
    
    def fillList(self, servers):
        for s in servers:
#            print(s['alias'])
            self.list.addItem(s['alias'])
    
    def connectTo(self, alias, callback, error_connect):
        self.log.setText('Connecting...')
        print('Connect to %s' % alias)
        server = self.api.getCollection('en_servers', alias=alias)
#        print(server)
        if server:
            self.api.async(lambda: self.initSSH(server), callback, error_connect)
        else:
            self.log.setText('Unknown server')
        
    def setErrText(self, e):
        self.api.error(e)
        self.log.setText(str(e))

    def setRetText(self):

        _ret = self.ssh.exec_command('ls', encoding='utf8')[1]
        ret = []
        for line in _ret:
            ret.append(line.strip('\n'))
        
        self.log.setText('\n'.join(ret))

    def deactivate(self):
        self.api.info('trololo')
        self.active = False
        return True
    
    
    def initSSH(self, server):
#        print(server)
        server = server[0]
        print('Init ssh for %(alias)s' % server)
        port = server['ssh_port']
        username = server['ssh_user']
        hostname = server['ip']
        password = server['ssh_password']

        client = ssh.SSHClient()
        self.ssh = client
#        print(self.ssh)

        self.ssh.set_missing_host_key_policy(ssh.AutoAddPolicy())
        if not server['ssh_cert']:
            client.connect(hostname, username=username, password=password)
        else:
            key = self.api.getCollection('en_keys', title=server['ssh_cert'])[0]
            with open('key', 'w') as key_file:
                key_file.write(key['key'].replace('\\n', '\n'))
            client.connect(hostname, username=username, key_filename='./key')
            
            self.sftp = self.ssh.open_sftp()


        
