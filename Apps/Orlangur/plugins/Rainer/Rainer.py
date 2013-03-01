from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.baseQt import SBAction
from winterstone.base import WinterPlugin

from everstone.baseQt import Stream

from datetime import datetime

from pynma import PyNMA as nma

class Rainer(WinterPlugin):
    def activate(self):
        self.list = QListWidget()
        self.action = self.api.createSBAction('mail', 'Rainer', self.list, toolbar=True)
        self.action.setEmblem('gray')

        self.list.onShow = lambda: self.action.setEmblem('gray')
        
        self.stream = Stream(self.config.options.channels)
        
        self.stream.addHandler('orlangur', self.receiveSystem)
        self.stream.addHandler('default', self.receiveDefault)
        self.stream.addHandler('log:*', self.receiveLog)
        self.stream.addHandler('notify', self.receiveNotify)
        
        self.stream.listen()
        
        self.api.pushToIP({'stream': self.stream})
        
        self.api.async(lambda: self.api.getCollection('__singles__', key='NMA API'), self.initNotifier)

        self.active = True
        return True
        
        
    def initNotifier(self, nmaapi):
        self.notifier = nma(nmaapi[0]['value'])

        self.api.pushToIP({'nma_notify': self.notifier.push})

        
    
    def receiveNotify(self, channel, pattern, msg):
        self.list.addItem(self.api.makeMessage('Notification: %s' % msg, color='lightgreen'))
        if self.config.options.nma:
            self.notifier.push('Evernight', 'from Rainer', msg)
        self.action.setEmblem('green')
        
    
    def receiveDefault(self, channel, pattern, msg):
        self.list.addItem(self.api.makeMessage(msg))

    def receiveSystem(self, channel, pattern, msg):
        self.list.addItem(self.api.makeMessage(msg, color='yellow', timestamp=True))
        self.action.setEmblem('orange')


    def receiveLog(self, channel, pattern, msg):
        msg['who'] = channel.replace('log:', '')
        self.list.addItem(self.api.makeMessage('%(who)s: %(level)s :: %(msg)s' % msg))
        

    def deactivate(self):
        self.active = False
        return True

