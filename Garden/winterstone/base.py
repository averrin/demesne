# -*- coding: utf-8 -*-
"""
    Base of Winterstone lib.
"""

__version__ = '0.8.6'
__author__ = 'averrin'

from _collections import defaultdict
import os
import weakref
from winterstone.snowflake import CWD, VAULT
import re
import inspect

import imp

try:
    from config import Config
    CONFIG_ENABLED = True
except:
    CONFIG_ENABLED = False


class WinterManager(object):
    """
        Django ORM -like manager for WinterObject subclasses
    """

    def __init__(self, cls):
        self.cls = cls

    def all(self):
        """
            Use native object _get_all method
        """
        return self.cls._get_all()

    def count(self):
        """
            return number of items
        """
        return len(self.all())

    def filter(self, **kwargs):
        """
            Filter criteria pass like attr = value
        """
        result = []
        for obj in self.all():
            n = 0
            for crit in kwargs:
                try:
                    tmp = crit.split('__')
                    action = None
                    val = None
                    if len(tmp) > 1:
                        crit = tmp[0]
                        action = tmp[1]
                        val = kwargs['%s__%s' % (crit, action)]
                    if (action is None and obj[crit] == kwargs[crit]) or\
                    (action == 'like' and re.match(val, obj[crit])) or\
                    (action == 'gt' and obj[crit] > val) or\
                    (action == 'lt' and obj[crit] < val) or\
                    (action == 'gte' and obj[crit] >= val) or\
                    (action == 'lte' and obj[crit] <= val) or\
                    (action == 'ne' and obj[crit] != val) or\
                    (action == 'isnone' and val and obj[crit] is None) or\
                    (action == 'isnone' and not val and obj[crit] is not None) or\
                    (action == 'has' and val and hasattr(obj, crit)) or\
                    (action == 'has' and not val and not hasattr(obj, crit)):
                        n += 1
                except KeyError:
                    pass
            if n == len(kwargs):
                result.append(obj)
        return result

    def get(self, **kwargs):
        """
            Get only first item of filter. Without Django-like exeption about not-uniq item
        """
        items = self.filter(**kwargs)
        if items:
            return items[0]
        else:
        #            raise Exception('No items')
            return False

    def __getitem__(self, key):
        return self.cls._get_all()[key]


class WinterMeta(type):
    """
        Custom metaclass
    """
    def __call__(cls, **kwargs):
        obj = super(WinterMeta, cls).__call__()
        for name, value in kwargs.items():
            setattr(obj, name, value)
        return obj

    def __new__(cls, **kwargs):
        obj = super(WinterMeta, cls).__call__()
        for name, value in kwargs.items():
            setattr(obj, name, value)
        return obj


class WinterObject(object):
    """
        Enhanced primitive object
    """
    __refs__ = defaultdict(list)
    __manager__ = WinterManager
    # __metaclass__ = WinterMeta

    def __init__(self, **kwargs):
        """
            Some preparations for objectmanager
        """
        self.__refs__[self.__class__].append(weakref.ref(self))
        self.__class__.objects = self.__class__.__manager__(self.__class__)

        WinterObject.__refs__[WinterObject].append(weakref.ref(self))
        WinterObject.objects = WinterObject.__manager__(WinterObject)

        for name, value in kwargs.items():
            setattr(self, name, value)

    @classmethod
    def _get_all(cls):
        """
            Get all objects of this class
        """
        lst = []
        for inst_ref in cls.__refs__[cls]:
            inst = inst_ref()
            if inst is not None:
                lst.append(inst)
        return lst

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __call__(self, *args, **kwargs):
        pass

    def set(self, key, value):
        self.__setattr__(key, value)
        return self

if CONFIG_ENABLED:
    class WinterConfig(Config):
        def __init__(self, streamOrFile=None):
            Config.__init__(self, streamOrFile)
            self._subs = []

        def add(self, listener):
            self._subs.append(listener)

        def delete(self, listener):
            self._subs.remove(listener)

        def notify(self, key, value):
            for listener in self._subs:
                if hasattr(listener, 'onSubsChange'):
                    listener.onSubsChange(key, value)
                if hasattr(listener, 'on_%s' % key):
                    getattr(listener, 'on_%s' % key)(value)

        def onChange(self, key, value):
            self.notify(key, value)


class Borg(object):
    """
        Simple monostate class
    """
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class WinterAPI(Borg):
    """
        IO API for plugins
    """
    _shared_state = {'denied': ['ex']}

    def __init__(self):
        Borg.__init__(self)
        if not hasattr(self, 'CWD'):
            self.CWD = CWD
        if not hasattr(self, 'icons'):
            self.icons = self.IconDict()
            icondir = self.CWD + 'icons/'
            self.addIconsFolder(icondir)
            self.addIconsFolder(VAULT + 'icons/')

    def addIconsFolder(self, icondir, force=True):
        ext = ['.png', '.jpg', '.gif']
        try:
            dirList = os.listdir(icondir)
        except OSError:
            dirList = []
        for fname in dirList:
            if os.path.isdir(str(icondir + fname)) and not fname.startswith('_'):
                subdirList = os.listdir(str(icondir + fname))
                for fi in subdirList:
                    if fi[-4:] in ext:
                        self.icons[fname + '/' + fi[:-4]] = os.path.join(icondir, fname, fi)
            elif fname[-4:] in ext:
                self.icons[fname[:-4]] = os.path.join(icondir, fname)

    class IconDict(dict):
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except(KeyError):
                return dict.__getitem__(self, 'dummy')

    def info(self, msg): pass

    def debug(self, msg): pass

    def error(self, msg): pass

    def log(self, msg): pass

    def __getattr__(self, item):
        try:
            return self.__getattribute__(item)
        except AttributeError as e:
            if str(item) not in self.denied:
                ex = self.ex(item)
                if ex:
                    return ex
                else:
                    return self.ex(item, module='core')

            else:
                raise e

class WinterPM(object):
    """
        Plugin manager
    """

    def activate(self, plugin):  #TODO: make it async
        """
            Activate plugin
        """
        try:
            if plugin.activate():
                plugin.state = 'Activated'
                if not plugin in self.plugins:
                    self.plugins.append(plugin)
        except Exception as e:
            plugin.active = False
            plugin.state = e
            self.api.error(e)
            
########################

    def experemental_activate(self, plugin):       #oops, it wants thread-safe plugin activation=(
        plugin.active = False
        self.api.async(
            plugin.activate,
            callback=lambda x: self.onSuccessActivate(plugin, x),
            error_callback=lambda e: self.onErrorActivate(plugin, e)
        )
    
    def onSuccessActivate(self, plugin, state):
        if state:
            plugin.state = 'Activated'
            if not plugin in self.plugins:
                self.plugins.append(plugin)
        else:
            plugin.active = False
            plugin.state = 'Unknown reason'


    def onErrorActivate(self, plugin, e):
        plugin.active = False
        plugin.state = e
        self.api.error(e)

########################      
        
    def deactivate(self, plugin):
        """
            Deactivate plugin
        """
        if plugin.state == 'Activated':
            plugin.deactivate()
            self.plugins.remove(plugin)
            plugin.state = 'Deactivated'

    def findModules(self):
        """
            Search plugin files
            http://wiki.python.org/moin/ModulesAsPlugins
        """
        modules = set()
        for folder in os.listdir(self.api.CWD + 'plugins'):
            if os.path.isdir(self.api.CWD + 'plugins/' + folder):
                for filename in os.listdir(self.api.CWD + 'plugins/' + folder):
                    module = None
                    if filename not in ['__init__.py', '__init__.py']:
                        if filename.endswith(".py"):
                            module = filename[:-3]
                        elif filename.endswith(".pyc"):
                            module = filename[:-4]
                        if module is not None:
                            modules.add(module)
                        
        return list(modules)

    def loadModule(self, name, path="plugins/"):
        """
            Return a named module found in a given path.
            http://wiki.python.org/moin/ModulesAsPlugins
        """
        (file, pathname, description) = imp.find_module(name, [self.api.CWD + path + name])
        try:
            return imp.load_module(name, file, pathname, description)
        except Exception as e:
            print("Module %s cant be loaded" % name)
            print(e)
            return None

    def processPlugin(self, module):
        """
            Create plugin instance from module
        """
        if module is not None:
            for obj in list(module.__dict__.values()):
                try:
                    if inspect.isclass(obj) and issubclass(obj, WinterPlugin) and obj is not WinterPlugin:
                        plugin = obj()
                        plugin.name = module.__name__
                        try:
                            plugin.onLoad()
                            return plugin
                        except Exception as e:
                            raise e
                except Exception as e:
                    raise e

    def activateAll(self):
        for plugin in self.plugins:
            if plugin.name in self.config.plugins.active:
                try:
                    self.activate(plugin)
                except Exception as e:
                    self.api.error(e)
            else:
                plugin.state = 'Deactivated'
                plugin.active = False

    def __init__(self, config):
        self.config = config
        self.api = API()
        self.modules = [self.loadModule(name) for name in self.findModules()]
        self.plugins = []
        for module in self.modules:
            m = self.processPlugin(module)
            if m is not None:
                self.plugins.append(m)


class WinterPlugin(WinterObject):
    """
        Base plugin class
    """

    def __init__(self):
        self.api = API()
        WinterObject.__init__(self)
        WinterObject.__refs__[WinterPlugin].append(weakref.ref(self))

    def onLoad(self):
        """
            Some base actions after create instance
        """
        cfgfile = open(self.api.CWD + 'plugins/%s/plugin.cfg' % self.name)
        self.config = WinterConfig(cfgfile)
        self.api.addIconsFolder(self.api.CWD + 'plugins/%s/icons' % self.name)

    def activate(self):
        """
            Overload...able method for activate
        """
        self.active = True
        return True

    def deactivate(self):
        """
            Overload...able method for activate
        """
        self.active = False
        return True


class WinterApp(object):
    """
        Main non-gui application class
    """
    __apiclass__ = WinterAPI
    __pmclass__ = WinterPM

    def getMethod(self, key, module='main'):
        if not key.startswith('_'):
            try:
                if module == 'core':
                    return getattr(self.core, key)
                elif module == 'main':
                    return getattr(self, key)
                else:
                    return getattr(WinterPlugin.objects.get(name=module), key)
            except Exception as e:
                pass
        return False

    def __getitem__(self, key):
        return self.getMethod('main', key)

    def loadConfigs(self):
        """
            Load configuration from file
        """
        self.config = WinterConfig(open(self.api.CWD + 'config/main.cfg'))
        self.p_config = WinterConfig(open(self.api.CWD + 'config/plugins.cfg'))
        self.schema = WinterConfig(open(self.api.CWD + 'config/schema.cfg'))

    def onSubsChange(self, key, value):
        print('%s changed to %s' % (key, value))

    def __init__(self):
        self.api = self.__class__.__apiclass__()

        global API
        API = self.__class__.__apiclass__
        self.loadConfigs()
        self.api.config = self.config
        self.api.ex = self.getMethod

        self.beforeCore()
        from core import Core

        self.core = Core()
        self.core.app = self
        self.core._afterInit()
        if self.config.options.plugins:
            WinterPlugin()
            self.pm = self.__class__.__pmclass__(self.p_config)

    def beforeCore(self):
        pass


'''
class WinterGUI(QMainWindow):
    def __init__(self, uiPath):
    #        pass
        QMainWindow.__init__(self)
        uiFile = QtCore.Qopen(uiPath)
        uiFile.open(QtCore.QFile.ReadOnly)
        self.loader = QtUiTools.QUiLoader()
        self.win = self.loader.load(uiFile, self)
        uiFile.close()

class WinterMainApp(WinterGUI, WinterApp):
    def __init__(self):
        WinterApp.__init__(self)
        WinterGUI.__init__(self, 'main.ui')


class WinterSM(WinterGUI):
    def __init__(self):
        WinterGUI.__init__(self, 'main.ui')
'''
