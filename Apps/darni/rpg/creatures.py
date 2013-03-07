from .base import *


class Creature(WinterObject):
    def __init__(self, name):
        WinterObject.__init__(self)
        self.Name = name
        self.Male = True

        self.title = ''
        self.Alive = True
        self.Level = 0

        self.HP = 9
        self.TotalHP = 10
        self.MP = 9
        self.TotalMP = 10

        self.Luck = 60

        self.Agility = rules.CommonAgility
        self.Strength = rules.CommonStrength
        self.Intelligence = rules.CommonIntelligence
        self.Charisma = rules.CommonCharisma

        self.inventory = Inventory(self)
        self.doll = Doll(self)

    def onEquip(self):
        self.onChange('', '')

    def addItem(self, item, predefined=False, zeroweight=False):
        if not isinstance(item, Item):
            if not predefined:
                item = ItemPrototypes[item]
            else:
                item = Items[item]
        if zeroweight:
            item.weight = 0
        self.inventory.add(item)

    def addItemFromSet(self, setname):
        item = Sets[setname].getItem(self)
        if item:
            self.addItem(item)

    @property
    def Defense(self):
        Defense = rules.baseDefense
        for item in Wearable.objects.filter(equipped=True):
            if hasattr(item, 'defense'):
                Defense += item.defense
        Defense += rules.DefModStr * self.Strength
        Defense += rules.DefModAgi * self.Agility
        Defense *= rules.DefModTotal
        Defense = abs(int(Defense))
        return Defense

    @property
    def Damage(self):
        Damage = rules.baseDamage
        for item in Wearable.objects.filter(equipped=True):
            if hasattr(item, 'damage'):
                Damage += item.damage
        Damage += rules.DmgModStr * self.Strength
        Damage += rules.DmgModAgi * self.Agility
        Damage *= rules.DmgModTotal
        Damage = abs(int(Damage))
        return Damage

    def __setattr__(self, key, value):
        WinterObject.__setattr__(self, key, value)
        self.onChange(key, value)

    def onChange(self, prop, value):
        pass


class Humanoid(Creature):
    @property
    def Title(self):
        return self.title

    @Title.setter
    def Title(self, title):
        self.title = title
        self.onChange('title', title)


class Hero(Humanoid):
    def __init__(self, name):
        self.Gold = 100
        Humanoid.__init__(self, name)

        # self.AligmentPoints = 500
        # self.Aligment = 'Neutral'


        #!!!!!!!!!!!!!resists
        # self.ResistElements = 0
        # self.ResistForces = 0
        # self.ResistMagic = 0
        # self.ResistPhisical = 0

        # self.HP_Str = 1
        # self.HP_Lvl = 5
        # self.Mana_Int = 1
        # self.Mana_Lvl = 5
        # self.Stamina_Spd = 1
        # self.Stamina_Lvl = 5

        # self.Def_Str = 1
        # self.Def_Agl = 1
        # self.Def_Spd = 1
        # self.Dmg_Str = 1
        # self.Dmg_Agl = 1
        # self.Dmg_Spd = 1
