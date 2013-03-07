#!/bin/env python

import sys
sys.path.append('legacy')

from magiclib import Cube, Shiver
from items import *
from winterstone.snowflake import htmlColor as color

ITEMS = {\
    'gems': {'baseprice': 3}\
}

GEMS = {\
    'emerald': {'prefix': 'em', 'color': 'green', 'addvalue': 0},\
    'ruby': {'prefix': 'ruby', 'color': 'red', 'addvalue': 0},\
    'sapphire': {'prefix': 'sap', 'color': 'blue', 'addvalue': 0},\
    'diamond': {'prefix': 'dia', 'color': 'diamond', 'addvalue': 0},\
    'mixed': {'prefix': 'mix', 'color': 'unknown', 'addvalue': 0},\
    }

RECIPES = {\
        ('emerald', 'ruby'): 'emerald',\
        ('emerald', 'diamond'): 'emerald',\
        ('emerald', 'sapphire'): 'sapphire',\
        ('ruby', 'sapphire'): 'sapphire',\
        ('sapphire', 'diamond'): 'diamond',\
        ('ruby', 'diamond'): 'diamond',\
        }

SLOTS = {'Head': 1, 'Body': 1, 'Legs': 1, 'Boots': 1, 'Gloves': 2, 'Neck': 1, 'Cloak': 1, 'Rings': 6, 'Hands': 2,
         'Braces': 2}
#SLOTS.extend(MSLOTS)


class Item(Shiver):
    def __init__(self, prefix, name, weight=0, price=0):
        self.prefix = prefix
        self.name = name
        self.weight = weight
        self.inInv = False
        self.price = price
        super(Item, self).__init__(prefix)

    def onAdd(self):
        #print '%s [%s] added' % (self.id,self)
        pass

    def onDestroy(self):
        #print '%s [%s] removed' % (self.id,self)
        pass


class Gem(Item):
    def __init__(self, type, level=0, value=0, name='', clearness=0, canMix=True, price=0):
        self.type = type
        self.prefix = GEMS[type]['prefix']
        self.color = GEMS[type]['color']
        self.name = name
        self.level = level
        self.weight = 1
        self.price = price + ITEMS['gems']['baseprice']
        if not value:
            self.value = 1000 + 500 * self.level - 100 * clearness
        self.clearness = clearness
        self.canMix = canMix
        super(Gem, self).__init__(self.prefix, self.name, self.weight, self.price)


class Stackable(Item):
    def __init__(self, prefix, name, weight=0, price=0):
        self.count = 0
        super(Stackable, self).__init__(prefix, name, weight, price)


class Coin(Stackable): #create stackable class
    def __init__(self):
        self.money = True
        super(Coin, self).__init__('coin', 'Coin')

#from termcolor import colored

class Wearable(Item):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, rarety=0, weight=0, price=0, require={}):
        self.slot_name = slot_name
        self.require = require
        self.slot_name = slot_name
        self.item_type = item_type
        self.material = material
        self.quality = quality
        self.title = title
        self.is_id = False
        self.name = self.genName()
        self.info = self.name

        super(Wearable, self).__init__(prefix, self.name, weight, price)

    def genName(self):
        it = self.item_type['type']
        itn = self.item_type['name']
        itn = color(itn, it)


        if self.is_id:
            name = '%s %s %s %s' % (
                color(self.quality['name'], self.quality['color']), self.title['name'], self.material['name'], itn)
        else:
            name = '%s %s' % (self.material['name'], itn)
        return name.replace('Common', '').replace('  ', ' ').strip()

    def ident(self):
        self.is_id = True
        self.name = self.genName()
        self.info = self.name

    def check(self, hero):
        i = 0
        for stat in self.require:
            if hero[stat] < self.require[stat]:
                break
            else:
                i += 1
        if i == len(self.require):
            return True
        else:
            return False

    def effect(self, hero):
        if self.is_id:
            hero[self.attr_name] += self.attr_value
        else:
            hero[self.attr_name] += self.attr_value / 2

    def unEffect(self, hero):
        if self.is_id:
            hero[self.attr_name] -= self.attr_value
        else:
            hero[self.attr_name] -= self.attr_value / 2


class Armor(Wearable):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, weight=0, require={}):
        super(Armor, self).__init__(prefix, slot_name, item_type, material, quality, title, weight, require)
        self.base_defense = item_type['defense']
        self.defense = self.base_defense
        if self.defense:
            self.info = '%s [%d]' % (self.name, self.defense)
        self.attr_name = 'Defense'
        self.attr_value = self.defense


class Handheld(Wearable):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, weight=0, require={}):
        super(Handheld, self).__init__(prefix, slot_name, item_type, material, quality, title, weight, require)

    #self.base_defense=item_type['defense']
    #self.defense=self.base_defense
    #if self.defense:
    #self.info='%s [%d]' % (self.name,self.defense)
    #def effect(self,hero):
    #hero.Defense+=self.defense
    #def unEffect(self,hero):
    #hero.Defense-=self.defense


class Weapons(Handheld):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, weight=0, require={}):
        super(Weapons, self).__init__(prefix, slot_name, item_type, material, quality, title, weight, require)
        self.base_dmg = self.item_type['dmg']
        self.dmg = self.base_dmg
        self.hands = self.item_type['hands']
        self.attr_name = 'Damage'
        self.attr_value = self.dmg


class Shields(Handheld):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, weight=0, require={}):
        super(Shields, self).__init__(prefix, slot_name, item_type, material, quality, title, weight, require)
        self.base_defense = item_type['defense']
        self.defense = self.base_defense
        if self.defense:
            self.info = '%s [%d]' % (self.name, self.defense)
        self.attr_name = 'Defense'
        self.attr_value = self.defense


class Rings(Wearable):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, weight=0, require={}):
        super(Rings, self).__init__(prefix, slot_name, item_type, material, quality, title, weight, require)


class Braces(Wearable):
    def __init__(self, prefix, slot_name, item_type, material, quality, title, weight=0, require={}):
        super(Braces, self).__init__(prefix, slot_name, item_type, material, quality, title, weight, require)

    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"""class Slot(Shiver):
	def __init__(self,name):
		self.name=name
		self.has_item=False
		super(Slot,self).__init__('slot')
	def add(self,element):
		self.item=element

	#def onAdd(self,item):
		#item.unwear=lambda: self.unwear(item)
		#item.effect(self.hero)
	#def onRemove(self,item):
		#item.unEffect(self.hero)
		#del item.unwear"""

class Slot(Shiver):
    def __init__(self, name, max_items):
        super(Slot, self).__init__('slot')
        #Slot.__init__(self,name)
        #Cube.__init__(self,Wearable)
        self.max_items = max_items
        self.elements = []
        self.name = name

    def add(self, element):
        #print '%s has %d elements' % (self.name,len(self.elements))
        if len(self.elements) < self.max_items:
            try:
                if self.elements[0].hands < self.max_items:
                    self.elements.append(element)
                    return self.elements
                else:
                    return False
            except:
                self.elements.append(element)
                return self.elements
        else:
            return False
        #class slot_Ring(MultiSlot):
        #def __init__(self):
        #super(slot_Ring,self).__init__('Rings',6)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class GemChest(Cube):
    def __init__(self):
        super(self.__class__, self).__init__(Gem)

    def combine(self, gem1, gem2):    #value, name
        if gem1 != gem2 and gem1.canMix and gem2.canMix:
            if gem1.level == gem2.level:
                newlevel = gem1.level + 1
            else:
                newlevel = max(gem1.level, gem2.level)
            self.remove(gem1)
            self.remove(gem2)
            if gem1.type == gem2.type:
                newtype = gem1.type
                newclear = max(gem1.clearness, gem2.clearness) - 1
            else:
                newclear = 4
                try:
                    newtype = RECIPES[(gem1.type, gem2.type)]
                except:
                    newtype = RECIPES[(gem2.type, gem1.type)]
            newgem = Gem(newtype, newlevel, clearness=newclear)
            self.add(newgem)
            return newgem
        else:
            #yeah, i want do this such way.
            self.remove(gem1)
            self.remove(gem2)
            self.error = 'Hey, cheater, how you did it?'
            newgem = Gem('mixed', 0, 0, 'Cheater Rock', 4, False)
            newgem.value = 0
            self.add(newgem)
            return newgem

    def onAdd(self, gem):
        gem.combineWith = lambda g2: self.combine(gem, g2)


class Chest(Cube):
    def __init__(self):
        super(self.__class__, self).__init__(Item)


class Inventory(Cube):
    def __init__(self):
        super(self.__class__, self).__init__(Item)

    def onAdd(self, item):
        item.drop = lambda: self.removeTrig(item, 'inInv')

    def drop(self, item):
        self.removeTrig(item, 'inInv')

    def onRemove(self, item):
        del item.drop

    def give(self, item):
        return self.addTrig(item, 'inInv')

    def regShop(self, shop):
        self.shop = shop
        shop.customer = self
        for item in self.elements:
            item.sell = lambda: self.addCoins(Coin, shop.buy(item))
        money = self.listBy('money', True)
        for m in money:
            if isinstance(m, shop.money_class):
                shop.coins = m

    def unregShop(self):
        del self.shop
        for item in self.elements:
            del item.sell
        del self.shop.customer

    def addCoins(self, money, count):
        for i in self.elements:
            if issubclass(i.__class__, money):
                i.count += count


class Shop(Cube):
    def __init__(self, goods, money_class):
        super(self.__class__, self).__init__(Item)
        self.money_class = money_class
        for item in goods:
            self.addTrig(item, 'inShop')

    def buy(self, item):
        try:
            item.drop()
            self.addTrig(item, 'inShop')
            pay = self.getPrice(item)
            #self.customer.addCoins(pay)
            return pay
        #print '<item> [%s] selled' % item
        except:
            self.error = '<item> [%s] can`t sell' % item
            return False

    def sell(self, item):
        #omfg, need money improvement
        try:
            if not item.inShop:
                raise
            if self.coins.count >= item.price:
                self.removeTrig(item, 'inShop')
                self.coins.count -= item.price
                return item
            else:
                self.error = 'you haven`t engouth money (%d). You have only %d' % (item.price, self.coins.count)
                return False
        except:
            self.error = '<item> [%s] can`t buy' % item
            return False

    def onAdd(self, item):
        item.buy = lambda: self.customer.give(self.sell(item))
        pass

    def onRemove(self, item):
        del item.buy

    def getPrice(self, item):
        return item.price


class Doll(Cube):
    def __init__(self):
        super(self.__class__, self).__init__(Wearable)
        self.slots = Cube(Slot)
        for n in SLOTS:
            sl = Slot(n, SLOTS[n])
            #print sl
            self.slots.add(sl)
        #for s in self.slots.elements:
        #print s.name
        #for n in MSLOTS:
        #self.slots.add(MultiSlot(n))
        #self.slots.add(slot_Ring())

    #TODO: Ring Slots
    def regInv(self, inv):
        self.inv = inv
        inv.onAdd = self._inv_onAdd
        inv.refresh()

    def wear(self, item):
        if item.check(self.hero):
            slot = self.slots.itemBy('name', item.slot_name)
            if slot.add(item):
                self.addTrig(item, 'onHero')
                return self.elements
            else:
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                #slot.has_item=False
                #self.removeTrig(slot.item,'onHero')
                #del slot.item
                #return item.wear()
                #print 'ooops'
                self.error = '<item> [%s] can`t wear. Slot is full.' % item
                return False
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        else:
            self.error = '<item> [%s] can`t wear. Check failed' % item
            return False

    def unwear(self, item):
        slot = self.slots.itemBy('name', item.slot_name)
        slot.has_item = False
        self.removeTrig(item, 'onHero')
        del slot.item
        return self.elements

    def onAdd(self, item):
        item.unwear = lambda: self.unwear(item)
        item.effect(self.hero)

    def onRemove(self, item):
        item.unEffect(self.hero)
        del item.unwear

    def _inv_onAdd(self, item):
        item.drop = lambda: self.inv.removeTrig(item, 'inInv')
        if issubclass(item.__class__, Wearable):
            item.wear = lambda: self.wear(item)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


class Char(object):
    def __init__(self):
        self.inventory = Inventory()
        self.inventory.add(Coin())
        self.doll = Doll()
        self.doll.regInv(self.inventory)
        self.doll.hero = self

        #!!!!!!!
        self.Sex = 'Male'
        self.Name = 'Hero'
        self.Title = 'The Great'
        self.Alive = True
        self.Level = 0

        self.Agility = 5
        self.Strength = 5
        self.Speed = 5
        self.Intelegence = 5
        self.Charisma = 5

        self.AligmentPoints = 500
        self.Aligment = 'Neutral'


        #!!!!!!!!!!!!!resists
        self.ResistElements = 0
        self.ResistForces = 0
        self.ResistMagic = 0
        self.ResistPhisical = 0

        self.HP_Str = 1
        self.HP_Lvl = 5
        self.Mana_Int = 1
        self.Mana_Lvl = 5
        self.Stamina_Spd = 1
        self.Stamina_Lvl = 5

        self.Def_Str = 1
        self.Def_Agl = 1
        self.Def_Spd = 1
        self.Dmg_Str = 1
        self.Dmg_Agl = 1
        self.Dmg_Spd = 1

        self.Base_Def = 0
        self.Base_Dmg = 5

        self._calculate()
        self._refresh()

        #!!!!!!!!!!!!!Other !Stats
        self.StatPoints = 5

    #!!!!!!!
    def levelUp(self):
        self.Level += 1
        self.StatPoints += 5
        self._calculate()
        self._refresh()

    def addStat(self, stat):
        if self.StatPoints:
            self.StatPoints -= 1
            self._addStat(stat, 1)

    def _addStat(self, stat, value):
        self[stat] += value
        self._calculate()

    def _setStat(self, stat, value):
        self[stat] = value
        self._calculate()

    def info(self):
        print """{title} {name} [{level}] (Def: {defense} Dmg: {dmg})
[Str: {str} Agl: {agl} Spd: {spd} Int: {int}] 
HP: {hp}/{maxhp} Mana: {mana}/{maxmana} Stamina: {st}/{maxst}

		""".format(title=self.Title, name=self.Name, level=self.Level, str=self.Strength, agl=self.Agility,
                   spd=self.Speed, int=self.Intelegence, maxhp=self.MaxHP, hp=self.HP, maxmana=self.MaxMana,
                   mana=self.Mana, defense=self.Defense, dmg=self.Damage, st=self.Stamina, maxst=self.MaxStamina)


    def _calculate(self):
        self.Defense = self.Base_Def + self.Def_Spd * self.Strength + self.Def_Agl * self.Agility + self.Def_Spd * self.Speed
        self.Damage = self.Base_Dmg + self.Dmg_Spd * self.Strength + self.Dmg_Agl * self.Agility + self.Dmg_Spd * self.Speed
        self.MaxHP = 100 + self.HP_Lvl * self.Level + self.HP_Str * self.Strength
        self.MaxMana = 50 + self.Mana_Lvl * self.Level + self.Mana_Int * self.Intelegence
        self.MaxStamina = 50 + self.Stamina_Lvl * self.Level + self.Stamina_Spd * self.Speed

    def _refresh(self):
        self.HP = self.MaxHP
        self.Mana = self.MaxMana
        self.Stamina = self.MaxStamina


    def _regChest(self, chest):
        self.chest = chest
        chest.customer = self

    def _unregChest(self, chest):
        del self.chest
        del chest.cusomer

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def test(func, *args):
    try:
        result = func(*args)
        if isinstance(result, bool) and not result:
            raise
        else:
            print result
    except:
        try:
            print func.__self__.error
        except:
            print 'Shit happened. If you test lambda function, use instead container method'


from types import DictType

def names(array, complex=False):
    names = []
    if complex:
        for n in array:
            for i in array[n]:
                names.append(i['name'])
    else:
        for i in array:
            names.append(i['name'])
    return names


def itemByType(array, type_item, complex=False):
    if complex:
        for n in array:
            for i in array[n]:
                if i['name'] == type_item:
                    return i
    else:
        for i in array:
            if i['name'] == type_item:
                return i


def genItem(hero, **kwargs):
    from avlib import choice, rand

    if 'slot' in kwargs and kwargs['slot'] in TYPES.keys():
        slot = kwargs['slot']
    else:
        slot = choice(TYPES.keys())
    if slot == 'Hands':
        if 'temp' in kwargs and kwargs['temp'] in TYPES[slot]:
            temp = kwargs['temp']
        else:
            temp = choice(TYPES[slot].keys())
        if 'item_type' in kwargs and kwargs['item_type'] in names(TYPES[slot][temp]):
            item_type = itemByType(TYPES[slot][temp], kwargs['item_type'])
        else:
            item_type = choice(TYPES[slot][temp])
    elif type(TYPES[slot]) is DictType:
        if 'item_type' in kwargs and kwargs['item_type'] in names(TYPES[slot], complex=True):
            item_type = itemByType(TYPES[slot], kwargs['item_type'], complex=True)
        else:
            item_type = rand({'value': TYPES[slot]['Rare'], 'p': 0.1}, {'value': TYPES[slot]['Unique'], 'p': 0.05},
                    {'value': TYPES[slot]['Common'], 'p': 0.8})
    else:
        item_type = choice(TYPES[slot])
    #material=choice(MATERIALS[item_type['type']])
    if 'material' in kwargs and kwargs['material'] in names(MATERIALS[item_type['type']], complex=True):
        material = itemByType(MATERIALS[item_type['type']], kwargs['material'], complex=True)
    else:
        material = rand({'value': MATERIALS[item_type['type']]['Rare'], 'p': 0.1},
                {'value': MATERIALS[item_type['type']]['Unique'], 'p': 0.05},
                {'value': MATERIALS[item_type['type']]['Common'], 'p': 0.8})
        if item_type['name'] in TM_EXCEPT.keys():
            while material['name'] in TM_EXCEPT[item_type['name']]:
                material = rand({'value': MATERIALS[item_type['type']]['Rare'], 'p': 0.1},
                        {'value': MATERIALS[item_type['type']]['Unique'], 'p': 0.05},
                        {'value': MATERIALS[item_type['type']]['Common'], 'p': 0.8})
    if 'quality' in kwargs and kwargs['quality'] in names(QTITLES, complex=True):
        quality = itemByType(QTITLES, kwargs['quality'], complex=True)
    else:
        quality = rand({'value': QTITLES['Rare'], 'p': 0.1}, {'value': QTITLES['Unique'], 'p': 0.05},
                {'value': QTITLES['Common'], 'p': 0.8})
    if 'title' in kwargs and kwargs['title'] in names(TITLES, complex=True):
        title = itemByType(TITLES, kwargs['title'], complex=True)
    else:
        title = rand({'value': TITLES['Rare'], 'p': 0.1}, {'value': TITLES['Unique'], 'p': 0.05},
                {'value': TITLES['Common'], 'p': 0.8})

    #title=rand({'value':TITLES,'p':0.2},{'value':[{'name':'Common'}],'p':0.8})
    if item_type['name'] in TT_EXCEPT[title['name']]:
        while item_type['name'] in TT_EXCEPT[title['name']]:
            title = rand({'value': TITLES['Rare'], 'p': 0.1}, {'value': TITLES['Unique'], 'p': 0.05},
                    {'value': TITLES['Common'], 'p': 0.8})
    item_color = choice(COLORS)
    if slot == 'Rings':
        item_class = Rings
    elif slot == 'Braces':
        item_class = Braces
    elif slot == 'Hands':
        if temp == 'Weapons':
            item_class = Weapons
        else:
            item_class = Shields
    else:
        item_class = Armor
    #print '%s %s %s %s' % (quality['name'],title['name'],material['name'],item_type['name'])
    item = item_class(item_type['name'].replace(' ', ''), slot, item_type, material, quality, title)
    item.ident()
    #print item.info
    return item


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def genName(obj):
    return obj.id

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class Effect(Shiver):
    def __init__(self):
        super(Effect, self).__init__('effect')
