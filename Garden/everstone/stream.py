import json
import re
import redis


class EverStream(object):
    
    def __init__(
        self,
        channels=False,
        handler=None,
        raw_log=False,
        host='averr.in',
        password='aqwersdf'
    ):
        self.connection = redis.Redis(host, password=password)
        self.handler = handler
        self.raw_handlers = []
        self.stop = False
        self.p = self.connection.pubsub()
        self.subscribe(channels)
        self.channels = self.p.channels
        self.raw_log = raw_log
        
    def addHandler(self, channel, handler):
        if not channel in self.handlers:
            self.handlers[channel] = []            
        self.handlers[channel].append(handler)

    def publish(self, data, channels=False):
        if not channels:
            channels = self.channels
        for channel in channels:
            self.connection.publish(channel, json.dumps(data))

    def subscribe(self, channels=[]):
        for channel in channels:
            self.p.psubscribe(channel)

    def unsubscribe(self, channels):
        for channel in channels:
            try:
                self.channels.remove(channel)
                self.p.punsubscribe(channel)
            except ValueError:
                pass

    def listen(self):
        self.beforeStart()
        for data_raw in self.p.listen():
            if self.stop:
                self.stop = False
                break
                
            if self.raw_log:
                if data_raw['channel'] not in ['online']:
                    print(data_raw)
            
            for rh in self.raw_handlers:
                data_raw = rh(data_raw)
            
            if data_raw['type'] not in ["message", "pmessage"]:
                continue

            try:
                data = data_raw["data"] #FACKEN bytes
                if isinstance(data, bytes):
                    data = data.decode()

                data = json.loads(data)
                ch = data_raw["channel"]
                pattern = data_raw["pattern"]
                if self.handler is not None:
                    self.handler(ch, pattern, data)
            except Exception as e:
#                print('-----------')
#                print(e)
#                print(data_raw)
#                print(data)
                pass
                
        self.beforeStop()
                
    def beforeStart(self):
        pass
    
    def beforeStop(self):
        pass



Rainer = EverStream