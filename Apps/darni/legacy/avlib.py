#!/usr/bin/python
# -*- coding: utf-8 -*-
import base64

__author__ = 'averrin'

##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#    Attribute            Meaning
#    func_doc            The function’s documentation string, or None if unavailable    Writable
#    __doc__                Another way of spelling func_doc    Writable
#    func_name            The function’s name    Writable
#    __name__            Another way of spelling func_name    Writable
#    __module__            The name of the module the function was defined in, or None if unavailable.    Writable
#    func_defaults        A tuple containing default argument values for those arguments that have defaults, or None if no arguments have a default value    Writable
#    func_code            The code object representing the compiled function body.    Writable
#    func_globals        A reference to the dictionary that holds the function’s global variables — the global namespace of the module in which the function was defined.    Read-only
#    func_dict            The namespace supporting arbitrary function attributes.    Writable
#    func_closure        None or a tuple of cells that contain bindings for the function’s free variables.    Read-only
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from UserDict import UserDict
import sys, os, re, shutil, subprocess
from UserDict import UserDict
from urllib2 import urlopen
import hashlib
import datetime, time


#import twiggy
#from twiggy import log
#from termcolor import colored
import weakref
from _collections import defaultdict
from __builtin__ import issubclass
from unohelper import inspect
import inspect as insp

#from yapsy.PluginManager import PluginManager as YPM, IPlugin

#twiggy.quickSetup()
#logger=log
#logger.name('avlib')

cwd=sys.path[0]+'/'

def parsePage(link,pattern):
    page=urlopen(link).read()
    result=re.findall(pattern,page)
    return result

class di(object):
    def __getitem__(self,key):
        return self.__dict__[key]
    def __setitem__(self,key,value):
        self.__dict__[key]=value

def info(object, spacing=30, collapse=1):
    """Print methods and doc strings.
    Takes module, class, list, dictionary, or string."""
    methodList = [e for e in dir(object) if callable(getattr(object, e))]
    processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
    print "\n".join(["%s %s" % (method.ljust(spacing), processFunc(str(getattr(object, method).__doc__))) for method in methodList])
    print object.__dict__

def loadDir(dir,ext):
    return loadIcons(dir,ext)

def loadIcons(icondir,ext='.png'):
    icons={}
    dirList = os.listdir(icondir)
    for fname in dirList:
        if fname.endswith(ext):
            icons[fname[:-4]]=str(icondir+fname)
    return icons

class configs(UserDict):
    def __init__(self, iniFile):
        self.data = self._load_(iniFile)
    def _load_(self, iniFile, raw=False, vars=None):
        """Convert an INI file to a dictionary"""
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.read(iniFile)
        result = {}
        for section in config.sections():
            if section not in result:
                result[section] = {}
            for option in config.options(section):
                value = config.get(section, option, raw, vars)
                if len(re.findall('\[.*\]',value)):
                    result[section][option]=eval(value)
                else:
                    result[section][option] = value
        return result
    def dump(self, iniFile):
        """Convert an dictionary to a INI file"""
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config_dict = self.data
        for section, values in config_dict.items():
            config.add_section(section)
            for var_name, var_value in values.items():
                config.set(section, var_name, var_value)
        config.write(open(cwd+iniFile, 'w'))

class ProgressBar:
    def __init__(self, duration):
        self.duration = duration
        self.prog_bar = '[]'
        self.fill_char = '#'
        self.width = 40
        self.__update_amount(0)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) / 2) - len(str(percent_done))
        pct_string = '%i%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def update_time(self, elapsed_secs):
        self.__update_amount((elapsed_secs / float(self.duration)) * 100.0)
        self.prog_bar += '  %ds/%ss' % (elapsed_secs, self.duration)

    def __str__(self):
        return str(self.prog_bar)

def shell(*cmd):
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = pipe.communicate()
    return pipe.returncode, stdout, stderr





class Guard(di):
    def __init__(self,path):
        #self.name=name
        self.path=path
        self.settingsFile='%ssnap.guard' % self.path
        self.settings=configs(self.settingsFile)
        self.newMap=self.makeMap()
        if not 'Map' in self.settings:
            print 'No Map in file'
            self.map=self.newMap()
            self.settings['Map']=self.map
        else:
            self.map=self.settings['Map']
    def makeMap(self):
        outputList = {}
        for dir_name in self.settings['settings']['dirs']:
            for root, dirs, files in os.walk(dir_name):
                if self.checkPath(root):
                    for f1 in files:
                        if '/'.join([root,f1])!=self.settingsFile:
                            m = hashlib.md5()
                            path='/'.join([root, f1])
                            m.update(open(path).read())
                            hash=m.hexdigest()
                            outputList[path]=hash
        return outputList

    def checkPath(self,root):
        trigger=True
        for path in self.settings['settings']['ex']:
            if path in root:
                trigger=False
        return trigger

    def checkMap(self):
        diff=[]
        newMap=self.newMap
        for file in newMap:
            if file in self.map:
                if newMap[file]!=self.map[file]:
                    diff.append(self.fileInfo(file))
            else:
                diff.append(self.fileInfo(file,new=True))
        if diff:
            return diff

    def listChanges(self):
        self.diff=self.checkMap()
        for line in self.diff:
            mark=''
            if 'oldhash' not in line:
                mark='[new]'
            print 'File: %s %s\nLast Mod: %s' % (line['path'],mark,line['mod'])


    def fileInfo(self,file,new=False):
        fstat=os.stat(file)
        st_mtime = fstat.st_mtime
        a,b,c,d,e,f,g,h,i = time.localtime(st_mtime)
        mtime='%s.%s.%d %s:%s:%s' % (str(c).zfill(2),str(b).zfill(2),a,str(d).zfill(2),str(e).zfill(2),str(f).zfill(2))
        #mtime=c,b,a,d,e,f,g,h,i
        result={'path':file,'hash':self.newMap[file],'mod':str(mtime)}
        if not new:
            result['oldhash']=self.map[file]
        return result


    def saveSettings(self):
        self.settings['Map']=self.newMap
        self.settings.dump(self.settingsFile)
        #print self.settings
    def makeSnap(self):
        self.saveSettings()

    def createFile(self):
        pass
    def createUpadate(self):
        pass

from random import random, choice
def rand(*args):
    """rand({'value':'Common','p':0.8},{'value':['White','Black'],'p':0.2})"""
    r=random()
    pp=[]
    for case in args:
        pp.append(case['p'])
    pp=sorted(pp)
    for p in pp[:-1]:
        if r<p:
            target=p
            break
        else:
            target=pp[-1]
    for case in args:
        if case['p']==target:
            target=case
            break
    return choice(target['value'])


class MyLogger:
    def __init__(self):
        import logging
        logging.basicConfig(level=logging.DEBUG, format="%(created)-15s %(message)s")
        self.log= logging.getLogger(__name__)
    def debug(self,msg):
        self.log.debug(colored(msg, 'yellow',attrs=['bold']))
    def info(self,msg):
        self.log.info(colored(msg, 'white',attrs=['bold']))
    def success(self,template,cont=''):
        if cont:
            msg=template % colored(cont, 'green',attrs=['bold'])
        else:
            msg=colored(template, 'green',attrs=['bold'])
        self.log.debug(msg)
    def error(self,template,cont=''):
        if cont:
            msg=template % colored(cont, 'red',attrs=['bold'])
        else:
            msg=colored(template, 'red',attrs=['bold'])
        self.log.debug(msg)
    def request(self,template,cont=''):
        if cont:
            msg=template % colored(cont, 'cyan',attrs=['bold'])
        else:
            msg=colored(template, 'cyan',attrs=['bold'])
        self.log.debug(msg)

def color(msg,color_str):
    if color_str[-1]=='B':
        return colored(msg,color_str.rstrip('B'),attrs=['bold'])
    elif color_str=='None':
        return ''
    else:
        return colored(msg,color_str)
def htmlColor(msg,color_str):
    if color_str[-1]=='B':
        return '<span style="color: %s;"><b>%s</b></span>' % (color_str.rstrip('B'),msg)
    elif color_str=='None':
        return ''
    else:
        return '<span style="color: %s;">%s</span>' % (color_str.rstrip('B'),msg)



class Hooked(object):
    __refs__ = defaultdict(list)

    def __init__(self):
        self.__refs__[self.__class__].append(weakref.ref(self))

    @classmethod
    def get_all(cls):
        for inst_ref in cls.__refs__[cls]:
            inst = inst_ref()
            if inst is not None:
                yield inst


class BaseHook(object):

    def __init__(self, hcls, name='Hook', echo=False, baseclass=Hooked, *args):
        self.logger = log.name(name)
        self.echo=echo
        self.log('Created')
        self.args=args
        if issubclass(hcls,baseclass):
            self.log(str(hcls))
            self.hcls=self.filter(hcls.get_all())


    def __call__(self, f):
        def wrapped_f(*args):
            for obj in self.hcls:
                method='obj.before_%s()' % f.__name__
                if 'before_%s' % f.__name__ in dir(obj):
                    eval(method)
            f(*args)
            for obj in self.hcls:
                method='obj.on_%s()' % f.__name__
                if 'on_%s' % f.__name__ in dir(obj):
                    eval(method)
        return wrapped_f

    def log(self,msg):
        if self.echo:
            self.logger.info(msg)

    def filter(self,hcls):
        ret=[]
        for obj in hcls:
            ret.append(obj)
        return ret

"""

def giveId(element):
    id=element.__hash__()
    return "%s%d" % (element.prefix,id)

class Shiver(di):
    def __init__(self,prefix):
        self.prefix=prefix
        self.id=giveId(self)
        self.line=self.__dict__
    def __getitem__(self,key):
        return self.__dict__[key]
    def __setitem__(self,key,value):
        self.__dict__[key]=value
    #def __str__(self):
        #return self.line
    def onAdd(self):
        pass
    def onDestroy(self):
        pass

class Cube(object):
    def __init__(self,elementClass=Shiver):
        self.elementClass=elementClass
        self.elements=[]
        self.lists={}

    def addList(self,list,name):
        self.lists[name]=list
        return self.lists
    def addListAttr(self,attr):
        return self.addList(self.listAttr(attr),attr)
    def addListBy(self,attr,value):
        return self.addList(self.listBy(attr,value),'%s[%s]' % (attr,value))

    def add(self,element):
        l=False
        if type(element).__name__=='list':
            l=True
            for e in element:
                self.add(e)
        if (isinstance(element,self.elementClass) or issubclass(element.__class__,self.elementClass)) and element not in self.elements:
            self.elements.append(element)
            element.destroy=lambda: self.remove(element)
            element.onAdd()
            self.onAdd(element)
            return self.elements
        elif l:
            return self.elements
        else:
            self.error='wrong type of <element> [%s]' % element
            return False

    def addTrig(self,element,attr):
        if type(element).__name__=='list':
            for item in element:
                item[attr]=True
        else:
            element[attr]=True
        self.add(element)
        return self.listBy(attr,True)

    def remove(self,element): #id or index
        if type(element).__name__=='str':
            tp='id'
        elif type(element).__name__=='int' and element<len(self.elements):
            tp='index'
        elif isinstance(element,self.elementClass) and element in self.elements:
            tp='element'
        else:
            self.error='wrong type of <element> [%s] or no such <element> in %s' % (element,self)
            return False
        if tp=='index':
            e=self.elements[element]
        elif tp=='id':
            for e in self.elements:
                if e.id==element:
                    break
        elif tp=='element':
            e=element
        try:
            self.elements.remove(e)
            e.onDestroy()
            self.onRemove(e)
            return self.elements
        except:
            self.error='can`t remove <element> [%s]' % element
            return False
    def removeTrig(self,element,attr):
        element[attr]=False
        self.remove(element)
        return self.listBy(attr,True)
    def count(self):
        return len(self.elements)

    def listAttr(self,attr,unique=False):
        l=[e[attr] for e in self.elements if hasattr(e,attr)]
        if unique:
            set = {}
            map(set.__setitem__, l, [])
            l=set.keys()
        return l
    def dictAttr(self,attr):
        l={}
        for e in self.elements:
            if hasattr(e,attr):
                l[e[attr]]=e
        return l

    def listBy(self,attr,value):
        l=[e for e in self.elements if hasattr(e,attr) and e[attr]==value]
        return l
    def itemBy(self,attr,value):
        return self.listBy(attr,value)[0]
    def list(self,name):
        return self.lists[name]

    def onAdd(self,element):
        pass
    def onRemove(self,element):
        pass

    def refresh(self):
        backup=self.elements[:]
        self.elements=[]
        for e in backup:
            self.add(e)


def getFileContent(file):
    file=open(file,'r')
    content=file.read()
    file.close()
    return content

class try_this(object):
    def __init__(self, *args):
        self.logger=logger

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            try:
                return f(*args,**kwargs)
            except Exception,e:
                logger.trace('error').warning('%s' % f)
        return wrapped_f


##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#            Plugin System
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#''' *.yapsy-plugin example
#    [Core]
#    Name = Firsty
#    Module = first
#
#    [Documentation]
#    Author = Averrin
#    Version = 0.1
#    Website = http://averrin.com
#    Description = example plugin
#'''

    #TODO: import keyring

class API(object):

    def info(self,msg): pass
    def debug(self,msg): pass
    def error(self,msg): pass

class PM(YPM):
    def __init__(self, dirs=[cwd+'plugins'],logapi=logger,api=logger,autoactivate=False,toActivate=[]):
        super(PM,self).__init__()
        self.setPluginPlaces(dirs)
        self.collectPlugins()
        self.logapi=logapi
        self.api=api
        self.methods=[]
        self.logapi.info('%s plugins found' % self.locatePlugins())
        self.toActivate=toActivate
        self.active=[]
        if autoactivate:
            self.activateAll()


    def activateAll(self):
        self.n=0
        for pluginInfo in self.getAllPlugins():
            pluginInfo.state='Deactivated'
            if pluginInfo.name in self.toActivate:
                self.activate(pluginInfo)

        self.logapi.info('%d plugins activated' % self.n)

    def activate(self,pluginInfo,permanent=False):
        plugin=pluginInfo.plugin_object
        plugin.api=self.api
        plugin.info=pluginInfo
        try:
            self.activatePluginByName(pluginInfo.name)
            plugin.is_activated=True
            plugin._getMethods()
            self.methods.extend(plugin.methods)
            self.active.append(plugin.info.name)
            pluginInfo.state='Activated'
            self.n+=1
            if permanent and pluginInfo.name not in self.toActivate:
                self.toActivate.append(pluginInfo.name)
        except Exception,e:
            logger.trace('error').warning('%s: cant activate!' % pluginInfo.name)
            self.logapi.error('%s: cant activate!: %s' % (pluginInfo.name,e))
            pluginInfo.state='ERROR: cant activate!% '

    def deactivate(self,plugin,permanent=False):
        pl=self.getPluginByName(plugin).plugin_object
        pl.is_activated=False
        pl.info.state='Deactivated'
        self.active.remove(plugin)
        for m in self.methods:
            if m['plugin']==plugin:
                self.methods.remove(m)
        self.deactivatePluginByName(plugin)
        if permanent:
            self.toActivate.remove(plugin)

    @try_this()
    def getPlugin(self,name):
        pl=self.getPluginByName(name).plugin_object
        if pl.is_activated:
            return pl
        else:
            self.logapi.error('%s not activated' % name)
            raise Exception('Plugin cant activated')

    def getActive(self,only_names=True):
        if only_names:
            return self.active

    def __getitem__(self,key):
        return self.getPlugin(key)

class Plugin(IPlugin,di):

    def _getMethods(self):
        self.methods=[]
        for m in dir(self):
            if m.startswith('p_'):
                self.methods.append({'method':eval('self.%s' % m),'plugin':self.info.name,'sign':m.replace('p_','')})
        return self.methods

    def afterActivate(self):
        pass


class Project(object):
    def __init__(self,file='config.ini'):
        self.config=configs(cwd+file)
        self.data=configs(cwd+'app.project')
        logger.info('Config file %s loaded' % file)
        try:
            from core import Core
            self.core=Core(self)
        except:
            self.core=''

class App(object):
    def __init__(self,project,api=logger,logapi=logger):
        self.project=project
        self.settings=project.data['Settings']
        self.options=project.config['Options']
        self.name=self.settings['name']
        self.api=api
        self.api.ex=self.__getitem__
        self.api.exMethod=self.exMethod
        self.api.getMethod=self.getMethod
        self.api.config=project.config
        self.api.saveConfig=self.saveConfig
        self.api.getOption=self.getOption
        self.api.getPass=self.getPass
        self.logapi=logapi
        self.logapi.ex=self.__getitem__
        self.has_plugins=eval(self.settings['has_plugins'])
        self.methods=[]
        self.core=project.core
        self.core.app=self
        self.core.api=api
        for m in dir(self):
            if m.startswith('m_'):
                self.methods.append({'method':eval('self.%s' % m),'plugin':'main','sign':m.replace('m_','')})

        if self.core:
            for m in dir(self.core):
                if m.startswith('m_'):
                    self.methods.append({'method':eval('self.core.%s' % m),'plugin':'main','sign':m.replace('m_','')})
            self.core.onAppInit()

        if self.has_plugins:
            self.methods.extend(self.createPM().methods)
            for pl in self.pm.active:
                #TODO: fix this strange!
                self.pm.getPluginByName(pl).plugin_object.afterActivate()
        else:
            self.createPM(autoactivate=False)
        self.api.methods=self.methods


    def getAuth(self,login_name='',login_desc='',pass_name='',pass_desc=''):
        if not self.login_window:
            window=self.api.exMethod('main','createLoginWindow',cwd+'login.ui')
            window.show()
        else:
            print self.login_window
            passw=self.login_window.passwordLine.text()
            login=self.login_window.loginLine.text()
            self.project.config['Plugins'][login_name]=login
            self.project.config['Plugins'][login_name+'_desc']=login_desc
            self.project.config['Plugins'][pass_name]=base64.b64encode(passw)
            self.project.config['Plugins'][pass_name+'_desc']=pass_desc
            self.saveConfig()

    def getPass(self,login_name='',login_desc='',pass_name='',pass_desc=''):
        passw = self.getOption(pass_name,desc=pass_desc)
        print passw
        if not passw:
            self.getAuth(login_name,login_desc,pass_name,pass_desc)
        login= self.getOption(login_name,desc=login_desc)
        return str(base64.b64decode(str(passw)).replace('\x00','')),login

    def getOption(self,name,default='',desc=''):
        if not name in self.api.config['Plugins']:
            self.project.config['Plugins'][name]=default
            self.project.config['Plugins'][name+'_desc']=desc
            self.logapi.debug('%s saved with value: %s and desc; %s' % (name,default,desc))
            self.saveConfig()
            return default
        else:
            return self.project.config['Plugins'][name]

    def createPM(self,autoactivate=True):
        if self.has_plugins:
            self.pm = PM(logapi=self.logapi,api=self.api,autoactivate=autoactivate, toActivate=self.project.config['Plugins']['activated'])
        else:
            self.pm = PM(logapi=self.logapi,api=self.api,autoactivate=autoactivate, toActivate=[])
        return self.pm


    def getMethod(self,plugin,sign):
        for m in self.methods:
            if m['plugin']==plugin and m['sign']==sign:
                return m['method']
        return False

    @try_this()
    def exMethod(self, plugin, sign, *args, **kwargs):
        m=self.getMethod(plugin,sign)
        if m:
            result = m(*args,**kwargs)
            curframe = insp.currentframe()
            calframe = insp.getouterframes(curframe, 2)
#            self.logapi.debug('caller info: %s' % str(calframe))
            self.logapi.debug('Method %s called from %s' % (sign,calframe[2][3]))
            return result
        else:
            self.logapi.error('Method %s not exist' % sign)
            return False

    def __getitem__(self,key):
        return self.getMethod('main',key)


    @try_this()
    def deactivate(self,name,permanent=False):
        self.pm.deactivate(name, permanent)
        self.refreshMethods()
        if permanent:
            self.saveConfig()

    @try_this()
    def activate(self,name,permanent=False):
        plugin=self.pm.getPluginByName(name)
        self.pm.activate(plugin, permanent)
        if permanent:
            self.saveConfig()

    def refreshMethods(self):
        for m in self.methods:
            if m['plugin'] not in self.pm.active and m['plugin']!='main':
                self.methods.remove(m)


    def saveConfig(self):
#        print self.pm.toActivate
#        print self.project.config
        self.project.config.dump('config.ini')

    def m_echo(self,msg):
        self.logapi.info(msg)

##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#            OLD Plugin System
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


coms=[]

class Debugger(object):
    def methodInfo(self,method):
        self.api.echo(inspect.getargspec(method))

    def sInspect(self,obj):
        self.api.echo(inspect.getmembers(obj))

class Logger(object):
    def echo(self,msg,pri):
        pass

class old_Plugin(object):
    Name = 'undefined'
    Version='0.0'
    Author='Averrin'
    ShortDesc=''
    LongDesc=''

    Available=True
    Visible=True
    NeedUnLoad=False

    def __init__(self,api):
        #self.Commands=[{'sign':'info','method':self.printInfo}]
        self.api=api
        self.Commands=[]

    def getInfo(self):
        self.Info={'Name':self.Name,'Version':self.Version,'Author':self.Author, \
                'ShortDesc':self.ShortDesc, "LongDesc":self.LongDesc}
        return self.Info
    def getVars(self):
        return self.__dict__
    def getMethods(self):
        self.Methods=[]
        for m in dir(self):
            if not m.startswith('__'):
                if re.findall('[a-z]',m[0]):
                    self.Methods.append(m)
        return self.Methods

    def printInfo(self):
        self.api.echo(self.getInfo())

    def makeRoot(self):
        self.api.echo(self, "make root!")
        for m in self.getMethods():
            #self.api.echo(getattr(self,m)
            self.Commands.append({'sign':m,'method':getattr(self,m),'root':True})

    def listCommands(self):
        self.api.echo(self.Commands)

    def register(self):
        pass

    def onLoad(self):
        pass

    def onCommand(self, cmd, args):
        pass

    def onUnLoad(self):
        self.api.echo(self.Name, 'unloaded.')

    def onError(self):
        self.NeedUnLoad=True

    def unLoadMe(self):
        self.api.unLoad(self.Name)

class old_PluginManager(object):
    def __init__(self,api):
        self.Plugins=[]
        self.api=api
        self.PluginsCanUnLoad=True
        self.coms=[{'plugin':self,'commands':[\
                {'sign':'lplug','method':self.listPlugins},\
                {'sign':'lcoms','method':self.listCommands},\
                {'sign':'lpcoms','method':self.listCommands},\
                {'sign':'sudo','method':self.makeRoot},\
                {'sign':'info','method':self.printInfo},\
                {'sign':'unload','method':self.unLoad},\
                {'sign':'load','method':self.loadPlugin},\
                {'sign':'check','method':self.checkPlugins},\
                ]}]
        self.api.echo('Plugin system Loaded')

    def LoadPlugins(self):
        self.Classes=[]
        ss = os.listdir('plugins')
        flist=[]
        for s in ss:
            if s.endswith('.py'):
                flist.append(s)
        sys.path.insert(0, 'plugins')
        self.api.echo('Plugins found: '+str(len(flist)))
        self.flist=flist

        for s in flist:
            __import__(os.path.splitext(s)[0])

        for plugin in Plugin.__subclasses__():
            self.Classes.append({'name':plugin.__name__,'class':plugin})
            #self.api.echo(plugin
            p = plugin(self.api)
            #self.api.echo(p.Name, p.Available
            if p.Available:
                self.Plugins.append(p)
                p.onLoad()
                self.coms.append({'plugin':p,'commands':p.Commands})
        self.api.echo(('Plugins loaded: '+str(len(self.Plugins))))
        self.onLoad()

    def loadPlugin(self,plugin):
        plugin += 'Plugin'
        for dict in self.Classes:
            if dict['name']==plugin:
                pclass=dict['class']
        p=pclass(self.api)
        self.Plugins.append(p)
        p.onLoad()
        self.coms.append({'plugin':p,'commands':p.Commands})


    def listPlugins(self):
        self.api.echo(self.Plugins)
    def listCommands(self):
        self.api.echo(self.coms)
    def listPluginCommands(self,plugin):
        if self.getPlugin(plugin):
            self.getPlugin(plugin).getCommands()

    def getPlugin(self,plugin):
        for p in self.Plugins:
            if p.Name==plugin:
                return p

    def makeRoot(self,plugin):
        if self.getPlugin(plugin):
            self.getPlugin(plugin).makeRoot()
    def unLoad(self,plugin):
        p=self.getPlugin(plugin)
        if p:
            p.onUnLoad()
            for dict in self.coms:
                if dict['plugin']==p:
                    self.coms.remove(dict)
            del sys.modules[plugin.lower()]
            self.Plugins.remove(p)

    def checkPlugins(self):
        for p in self.Plugins:
            if p.NeedUnLoad:
                self.unLoad(p.Name)


    def getInfo(self,plugin):
        if self.getPlugin(plugin):
            return self.getPlugin(plugin).getInfo()
    def printInfo(self,plugin):
        self.api.echo(self.getInfo(plugin))



    def onLoad(self):
        self.api.echo('-'*40)
дщк

class old_API(object):
    def __init__(self,app):
        self.app=app

    def unLoad(self,plugin):
        if self.app.PluginManager.PluginsCanUnLoad:
            self.app.PluginManager.unLoad(plugin)
        else:
            self.api.echo('Self-unload forbidden!')

    def echo(self,msg):
        print '%s' % msg

"""