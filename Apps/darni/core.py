from PyQt4.QtGui import *
from PyQt4.QtCore import *
from augment import *
from rpg.base import *
from ui import API
from rpg.items import *


class Core(QObject):
    """
        Store all your app logic here
    """

    def _afterInit(self):
        """
            when application totally init
        """
        self.api = API()
        self.api.ex = self.app.getMethod
        self.api.config = self.app.config
        self.main()
        # self.api.info('Core loaded.')

    def main(self):
        """
            dummy for main core method.
        """
        # self.hero.inventory.add(self.set1.getItem(self.hero))
        # self.hero.inventory.add(self.set1.getItem(self.hero))
        self.app.script.addObject('core', self)
        self.app.script.addObject('player', hero)
        self.app.script.addObject('inv', hero.inventory)

        self.hero = hero

        eventer.onSlotWear = self.updateSlot
        eventer.onSlotUnWear = self.clearSlot
        eventer.onEnchantActivate = self.onEffectActivate
        eventer.onEffectShot = self.onEffectShot
        eventer.onEnchantDeActivate = self.onEffectDeActivate
        eventer.onEffectDeActivate = self.onEffectDeActivate
        eventer.onSetActivate = self.onSetActivate
        eventer.onSetDeActivate = self.onSetDeActivate
        eventer.onUse = self.onUse
        eventer.onDrop = self.onDrop
        self.hero.onChange = self.heroChange
        eventer.msg = self.api.log
        eventer.onInventoryAdded = self.onInventoryAdded
        #        self.vault=Container('Vault',[ItemPrototypes.random(),ItemPrototypes.random(),ItemPrototypes.random(),Sets['SSwift'].getItem(self.hero),Sets['SSwift'].getItem(self.hero),Sets['SSwift'].getItem(self.hero)])
        self.vault = Container('Vault', [])
        # self.reroll()

    def reroll(self):
        self.app.vault.container = Container('Vault',
            [ItemPrototypes.random(enchant=2), ItemPrototypes.random(enchant=2), ItemPrototypes.random(enchant=0), ItemPrototypes.random(),
             ItemPrototypes.random(), ItemPrototypes.random()])
        self.app.vault.updateItems()

    def onInventoryAdded(self, item):
        try:
            self.app.inv.updateItems()
        except AttributeError:
            pass

    def start(self):
        self.app.stats.update()

    def updateSlot(self, slot, item):
        target = None
        for n in range(len(self.hero.doll.slots)):
            if self.app.doll.item(n, 0).slot == slot:
                target = self.app.doll.item(n, 0)
                break
        if target is not None:
            qitem = QTableWidgetItem(item.name)
            self.app.doll.setItem(n, 1, qitem)
            qitem.setIcon(QIcon(self.api.icons[item.icon]))
            qitem.setToolTip(item.info)
            self.api.inv(self.tr('%s weared' % item.name))

        target = None
        for n in range(len(self.hero.inventory.items)):
            if self.app.inv.item(n, 0).item == item:
                target = self.app.inv.item(n, 0)
                break
        if target is not None:
            for i in range(0, self.app.inv.columnCount()):
                if self.app.inv.item(n, i):
                    brush = QBrush(QColor(self.api.config.options.app.inv_equipped_color))
                    self.app.inv.item(n, i).setBackground(brush)

        self.app.status.update()

    def heroChange(self, *args):
        try:
            self.app.status.update()
            self.app.stats.update()
            self.app.inv.updateItems()
        except AttributeError as e:
            print(e)

    def clearSlot(self, slot, item):
        target = None

        for n in range(len(self.hero.doll.slots)):
            if self.app.doll.item(n, 0).slot == slot:
                target = self.app.doll.item(n, 0)
                break
        if target is not None:
            self.app.doll.setItem(n, 1, QTableWidgetItem(''))
            target.item = None
            self.api.inv(self.tr('%s unweared' % item.name))

        target = None
        for n in range(len(self.hero.inventory.items)):
            if self.app.inv.item(n, 0).item == item:
                target = self.app.inv.item(n, 0)
                break
        if target is not None:
            for i in range(0, self.app.inv.columnCount()):
                if self.app.inv.item(n, i):
                    self.app.inv.item(n, i).setBackground(QBrush(Qt.transparent))

        self.app.status.update()

    def onEffectActivate(self, effect):
        self.api.effect(self.tr('%s activated' % effect.name))

    def onEffectShot(self, effect):
        self.api.effect(self.tr('%s activated' % effect.name))

    def onEffectDeActivate(self, effect):
        self.api.effect(self.tr('%s deactivated' % effect.name))

    def onSetActivate(self, iset):
        self.api.iset(self.tr('%s weared' % iset.name))

    def onSetDeActivate(self, iset):
        self.api.iset(self.tr('%s unweared' % iset.name))

    def onUse(self, item):
        self.api.log(self.tr('%s used' % item.name))

    def onDrop(self, item):
        self.api.drop(self.tr('%s dropped' % item.name))
