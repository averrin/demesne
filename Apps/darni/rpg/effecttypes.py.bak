from base import *

class Modifier(Effect):
    def __init__(self, name, prop, value, *args, **kwargs):
        self.prop = prop
        self.value = value
        self.info_postfix = ''
        Effect.__init__(self, name, self._activate, self._deactivate, *args, **kwargs)
        WinterObject.__refs__[Effect].append(weakref.ref(self))
        self.short_info = self.info

    @property
    def info(self):
        return '%s +%s %s' % (self.prop, self.value, self.info_postfix)

    def _activate(self):
        self.target[self.prop] += self.value

    def _deactivate(self):
        self.target[self.prop] -= self.value