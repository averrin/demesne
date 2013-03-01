import re
from .stream import EverStream

from PyQt4.QtCore import *

class Stream(object):
    def __init__(self, channels=[], *args, **kwargs):
        self.stream = EverStream(channels, self.handler, *args, **kwargs)
        self.channels = self.stream.channels
        self.subscribe = self.stream.subscribe
        self.publish = self.stream.connection.publish
        self.unsubscribe = self.stream.unsubscribe
#        self.addHandler = self.stream.addHandler

        self.handlers = {}
        
        self.stream.beforeStart = self._bstart
        self.stream.beforeStop = self._bstop
        
        self.worker = None
        
    def _bstart(self):
        self.worker.emit(SIGNAL('start'))

    def _bstop(self):
        self.worker.emit(SIGNAL('stop'))
        
    def handler(self, channel, pattern, data):
        self.worker.emit(SIGNAL('message'), channel, pattern, data)
        
    def _inbox(self, ch, pattern, data):
        if pattern in self.handlers:
            for handler in self.handlers[pattern]:
                handler(ch, pattern, data)


    def addHandler(self, channel, handler):
        if not channel in self.handlers:
            self.handlers[channel] = []
        self.handlers[channel].append(handler)
        
        
    def errorHandler(self, e):
        raise e
        
        
    def listen(self):
        self.worker = self.Worker(self.stream)
        self.worker.connect(self.worker, SIGNAL('message'), self._inbox)
        self.worker.connect(self.worker, SIGNAL('start'), self.beforeStart)
        self.worker.connect(self.worker, SIGNAL('stop'), self.beforeStop)
        self.worker.connect(self.worker, SIGNAL('error'), self.errorHandler)
        self.worker.start()
        return self.worker

    def beforeStart(self):
        pass

    def beforeStop(self):
        print('stopped')
    
    class Worker(QThread):
        def __init__(self, stream):
            self.stream = stream
            QThread.__init__(self)
            
        def run(self):
            try:
                self.stream.listen()
            except Exception as e:
                self.emit(SIGNAL('error'), e)
    