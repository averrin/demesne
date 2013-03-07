from base import *

class Armor(Wearable):
    def __init__(self, name, slot, defense, *args, **kwargs):
        Wearable.__init__(self, name, slot, *args, **kwargs)
        WinterObject.__refs__[Wearable].append(weakref.ref(self))
        self.defense = defense

    @property
    def info(self):
        info = "<img src=%s style='float:left;'><b>%s %sAC</b><br>Quality: %s<br><i>%s</i>" % (
        fAPI().icons[self.icon], self.name, self.defense, rules.qualities[self.quality], self.desc)
        if hasattr(self, 'from_set') and self.from_set is not None:
            info += "<br>From set: <b>%s</b><br>" % self.from_set.name
            info += '<br>'.join([effect.short_info for effect in self.from_set.enchant.effects])
        return info


class Weapon(Wearable):
    def __init__(self, name, damage, *args, **kwargs):
        Wearable.__init__(self, name, 'MainHand', *args, **kwargs)
        WinterObject.__refs__[Wearable].append(weakref.ref(self))
        self.damage = damage

    @property
    def info(self):
        info = "<img src=%s style='float:left;'><b>%s %s</b><br>Quality: %s<br><i>%s</i>" % (
        fAPI().icons[self.icon], self.name, self.damage, rules.qualities[self.quality], self.desc)
        if hasattr(self, 'from_set') and self.from_set is not None:
            info += "<br>From set: <b>%s</b><br>" % self.from_set.name
            info += '<br>'.join([effect.short_info for effect in self.from_set.enchant.effects])
        return info

    def onSlotFull(self, slot):
        if slot.name == 'MainHand':
            self.slot = 'OffHand'
            return True
        else:
            return False


class Book(Item):
    def use(self):
        self.inv.owner.Title = 'Smarty'
        self.inv.destroy(self)
        eventer.msg('You so smart!')
        eventer.onUse(self)