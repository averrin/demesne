from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from winterstone.baseQt import WinterAPI, IconPainter
from datetime import datetime, time
from rpg.base import *

class API(WinterAPI):
    def inv(self, msg):
        self.ex('getLog')().inv(msg)

    def effect(self, msg):
        self.ex('getLog')().effect(msg)

    def iset(self, msg):
        self.ex('getLog')().iset(msg)

    def log(self, msg):
        self.ex('getLog')().log(msg)

    def drop(self, msg):
        self.ex('getLog')().drop(msg)
#from winterstone.baseQt import API


class GameLog(QDockWidget):
    def __init__(self, parent):
        QDockWidget.__init__(self)
        self.setObjectName('gameLog')
        self.list = QListWidget(self)
        self.setWidget(self.list)
        self.parent = parent
        self.list.setAutoScroll(True) #??? why dont work?
        self.api = API()


    def makeMessage(self, msg, color='', icon='', bold=True, fgcolor='', timestamp=False):
        """""
            Return listitem with nize attrs
        """""
        if timestamp:
            timestamp = datetime.now().strftime('%H:%M:%S')
            item = QListWidgetItem('[%s] %s' % (timestamp, msg))
        else:
            item = QListWidgetItem(msg)
        if color:
            item.setBackground(QColor(color))
        font = QFont('Sans')
        font.setBold(bold)
        font.setPointSize(9)
        item.setFont(font)
        item.setForeground(QBrush(QColor(fgcolor)))
        if icon:
            item.setIcon(QIcon(self.parent.api.icons[icon]))
        return item

    def log(self, msg):
        self.list.addItem(
            self.makeMessage(msg, timestamp=True, icon='ok', color=self.api.config.options.app.log_message_color))

    def inv(self, msg):
        self.list.addItem(self.makeMessage(msg, timestamp=True, icon=self.api.config.options.app.log_inv_message_icon,
            color=self.api.config.options.app.log_inv_message_color))

    def drop(self, msg):
        self.list.addItem(self.makeMessage(msg, timestamp=True, icon=self.api.config.options.app.log_inv_message_icon,
            color=self.api.config.options.app.log_drop_message_color))

    def effect(self, msg):
        self.list.addItem(
            self.makeMessage(msg, timestamp=True, icon=self.api.config.options.app.log_effect_message_icon,
                color=self.api.config.options.app.log_effect_message_color))

    def iset(self, msg):
        self.list.addItem(self.makeMessage(msg, timestamp=True, icon=self.api.config.options.app.log_iset_message_icon,
            color=self.api.config.options.app.log_iset_message_color))


class ContainerPanel(QTableWidget):
    def __init__(self, parent, container):
        self.container = container
        self.api = parent.api
        self.parent = parent
        QTableWidget.__init__(self, 0, 5)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.headers = [self.tr('Item'), self.tr('Enchant'), self.tr('Def/Dmg'), self.tr('Weight'),
                        self.tr('Value')]

        self.setIconSize(QSize(self.api.config.options.app.inv_icon_size, self.api.config.options.app.inv_icon_size))
        self.setHorizontalHeaderLabels(self.headers)
        self.updateItems()
        self.itemClicked.connect(self.giveItem)

    def giveItem(self, item):
        print(item.item)
        self.parent.core.hero.inventory.add(item.item)
        self.container.remove(item.item)
        self.updateItems()


    def updateItems(self):
        self.clear()
        self.setHorizontalHeaderLabels(self.headers)
        n = 0
        for n, item in enumerate(self.container.items):
            self.setRowCount(n + 1)
            qitem = QTableWidgetItem(item.name)
            qitem.setIcon(QIcon(self.api.icons[item.icon]))
            qitem.item = item
            qitem.setToolTip(item.info)
            self.setItem(n, 0, qitem)
            iitem = QTableWidgetItem(item.enchant.name if hasattr(item, 'enchant') and item.enchant is not None else '')
            if hasattr(item, 'enchant') and item.enchant:
                iitem.setIcon(QIcon(self.api.icons[item.enchant.icon]))
                iitem.setToolTip(item.enchant.info)
            self.setItem(n, 1, iitem)
            self.setItem(n, 3, QTableWidgetItem(str(item.weight)))
            if hasattr(item, 'defense'):
                it = QTableWidgetItem('%sAC' % item.defense)
                self.setItem(n, 2, it)
                it.setIcon(QIcon(self.api.icons[self.api.config.options.app.defense_icon]))
            elif hasattr(item, 'damage'):
                it = QTableWidgetItem('%s' % item.damage)
                self.setItem(n, 2, it)
                it.setIcon(QIcon(self.api.icons[self.api.config.options.app.damage_icon]))
            else:
                self.setItem(n, 2, QTableWidgetItem(''))

        n += 1
        self.setRowCount(n + 1)
        # self.setItem(n,0,QTableWidgetItem(self.tr(u'Total weight:')))
        # self.setItem(n,1,QTableWidgetItem('%s / %s'%(self.owner.inventory.calcWeight(),self.owner.inventory.capacity)))
        # iconitem=QTableWidgetItem('')
        # iconitem.setIcon(QIcon(self.api.icons[self.api.config.options.app.weight_icon]))
        # self.setVerticalHeaderItem(n,iconitem)
        # n+=1
        self.setItem(n, 0, QTableWidgetItem(self.tr('Total coins:')))
        self.setItem(n, 1, QTableWidgetItem('%s' % self.container.coins))
        iconitem = QTableWidgetItem('')
        iconitem.setIcon(QIcon(self.api.icons[self.api.config.options.app.coins_icon]))
        self.setVerticalHeaderItem(n, iconitem)


class InventoryPanel(QTableWidget):
    def __init__(self, parent, owner):
        self.owner = owner
        self.api = parent.api
        self.parent = parent
        QTableWidget.__init__(self, 0, 5)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.headers = [self.tr('Item'), self.tr('Enchant'), self.tr('Def/Dmg'), self.tr('Weight'),
                        self.tr('Value')]
        # for header in headers:
        # hs.append(QString(header))


        self.setIconSize(QSize(self.api.config.options.app.inv_icon_size, self.api.config.options.app.inv_icon_size))
        self.itemActivated.connect(self.itemEquip)
        self.itemClicked.connect(self.itemEquip)
        self.updateItems()

    #        self.horizontalHeaderItem(0)

    def updateItems(self):
        self.setSortingEnabled(False)
        self.clear()
        self.setHorizontalHeaderLabels(self.headers)
        paint=IconPainter()
        n = 0
        for n, item in enumerate(self.owner.inventory.items):
#            print(self.api.icons[item.icon])
            self.setRowCount(n + 1)
            qitem = QTableWidgetItem(item.name)
            qitem.setIcon(QIcon(self.api.icons[item.icon]))
            qitem.item = item
            qitem.setToolTip(item.info)
            self.setItem(n, 0, qitem)
            iitem = QTableWidgetItem(item.enchant.name if hasattr(item, 'enchant') and item.enchant is not None else '')
#            if hasattr(item, 'enchant') and item.enchant:
#                icon=qitem.icon().pixmap(QSize(64,64))
#                qitem.setIcon(QIcon(paint.drawEmblem(icon,'pvprank'+str(item.quality-7).zfill(2))))
#                iitem.setIcon(QIcon(self.api.icons[item.enchant.icon]))
#                iitem.setToolTip(item.enchant.info)

            self.setItem(n, 1, iitem)
            self.setItem(n, 3, QTableWidgetItem(str(item.weight)))
            if hasattr(item, 'defense'):
                it = QTableWidgetItem('%sAC' % item.defense)
                self.setItem(n, 2, it)
                it.setIcon(QIcon(self.api.icons[self.api.config.options.app.defense_icon]))
            elif hasattr(item, 'damage'):
                it = QTableWidgetItem('%s' % item.damage)
                self.setItem(n, 2, it)
                it.setIcon(QIcon(self.api.icons[self.api.config.options.app.damage_icon]))
            else:
                self.setItem(n, 2, QTableWidgetItem(''))

            if hasattr(item, 'equipped') and item.equipped:
                for i in range(5):
                    try:
                        self.item(n, i).setBackgroundColor(QColor(self.api.config.options.app.inv_equipped_color))
                    except:
                        pass
                        # iconitem=QTableWidgetItem('')
                        # iconitem.setIcon(QIcon(parent.api.icons[item.icon]))
                        # self.setVerticalHeaderItem(n,iconitem)
        n += 1
        self.setRowCount(n + 1)
        self.setItem(n, 0, QTableWidgetItem(self.tr('Total weight:')))
        self.setItem(n, 1,
            QTableWidgetItem('%s / %s' % (self.owner.inventory.calcWeight(), self.owner.inventory.capacity)))
        iconitem = QTableWidgetItem('')
        iconitem.setIcon(QIcon(self.api.icons[self.api.config.options.app.weight_icon]))
        self.setVerticalHeaderItem(n, iconitem)
        n += 1
        self.setRowCount(n + 1)
        self.setItem(n, 0, QTableWidgetItem(self.tr('Total coins:')))
        self.setItem(n, 1, QTableWidgetItem('%s' % self.owner.Gold))
        iconitem = QTableWidgetItem('')
        iconitem.setIcon(QIcon(self.api.icons[self.api.config.options.app.coins_icon]))
        self.setVerticalHeaderItem(n, iconitem)

    #        self.setSortingEnabled(True)

    #        self.customContextMenuRequested.connect(self.cmenu)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            QTableWidget.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
    #        if event.button()==Qt.LeftButton:
    #            QTableWidget.mousePressEvent(self,event)
    #        elif event.button()==Qt.RightButton:
    #        print event.globalPos()
        item = self.itemAt(event.pos())
        menu = QMenu()
        menu.addAction(QAction(QIcon(self.api.icons[item.item.icon]), item.text(), self))
        menu.addSeparator()
        if issubclass(item.item.__class__, Wearable):
            self.eq = QAction(self.tr('Unequip') if item.item.equipped else self.tr('Equip'), self)
            self.eq.triggered.connect(self.equip)
            self.eq.item = item
            menu.addAction(self.eq)
        if hasattr(item.item, 'use'):
            self.use = QAction(self.tr('Use'), self)
            self.use.triggered.connect(self.itemUse)
            self.use.item = item
            menu.addAction(self.use)
        self.de = QAction(self.tr('Drop'), self)
        self.de.triggered.connect(self.itemDrop)
        self.de.item = item
        menu.addAction(self.de)
        menu.exec_(event.globalPos())

    def itemUse(self):
        item = self.use.item.item
        item.use()
        self.updateItems()


    def equip(self, *args):
        self.itemEquip(self.eq.item)

    def itemDrop(self, item):
        item = self.de.item.item
        self.owner.inventory.remove(item)
        self.updateItems()

    def itemEquip(self, item):
        if hasattr(item, 'item') and issubclass(item.item.__class__, Wearable):
            if item.item.equipped:
                item.item.unequip()
            else:
                item.item.equip()


    def lock(self):
        for i in range(self.rowCount() - 1):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item:
                    item.setFlags(Qt.ItemIsSelectable)
                    item.setFlags(Qt.ItemIsEnabled)


class DollPanel(QTableWidget):
    def __init__(self, parent, owner):
        self.owner = owner
        QTableWidget.__init__(self, len(self.owner.doll.slots), 2)
        self.setHorizontalHeaderLabels([self.tr('Slot'), self.tr('Item')])
        self.setIconSize(
            QSize(parent.api.config.options.app.doll_icon_size, parent.api.config.options.app.doll_icon_size))
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for n, slot in enumerate(self.owner.doll.slots):
            item = QTableWidgetItem(slot.name)
            item.setIcon(QIcon(parent.api.icons[slot.icon]))
            item.slot = slot
            self.setItem(n, 0, item)
            self.takeVerticalHeaderItem(n)

        for i in range(self.rowCount() - 1):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item:
                    item.setFlags(Qt.ItemIsSelectable)
                    item.setFlags(Qt.ItemIsEnabled)


class StatsPanel(QTableWidget):
    def __init__(self, parent, owner):
        self.owner = owner
        self.api = parent.api
        QTableWidget.__init__(self, len(self.api.config.options.app.stats), 2)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setIconSize(
            QSize(parent.api.config.options.app.stats_icon_size, parent.api.config.options.app.stats_icon_size))
        self.stats = self.api.config.options.app.stats

    def update(self):
        self.clear()
        #        self.owner.update()
        for n, sts in enumerate(self.stats):
            st = QTableWidgetItem(sts[0])
            self.setItem(n, 0, st)
            st.setToolTip(sts[2])
            st.setIcon(QIcon(self.api.icons[sts[1]]))
            self.setItem(n, 1, QTableWidgetItem(str(self.owner.__getattribute__(sts[0]))))

        for i in range(self.rowCount() - 1):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item:
                    item.setFlags(Qt.ItemIsSelectable)
                    item.setFlags(Qt.ItemIsEnabled)


class EffectsBar(QWidget):
    def __init__(self, parent=''):
        self.parent = parent
        self.api = parent.api
        QWidget.__init__(self)
        self.setLayout(QHBoxLayout())
        self.icons = []
        self.spacerItem = QWidget()
        self.spacerItem.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        Effect('')
        self.icon_size = self.api.config.options.app.eff_icon_size
        self.emblem = QLabel('')
        self.emblem.setPixmap(QPixmap(self.api.icons[self.api.config.options.app.emblem_icon]).scaled(
            QSize(self.icon_size, self.icon_size)))

        self.hstatus = QLabel('')
        self.layout().insertWidget(0, self.hstatus)
        self.layout().insertWidget(0, self.emblem)
        self.update()


    def update(self):
        for icon in self.icons:
            icon.hide()
            icon.destroy()
        self.icons = []

        for effect in Effect.objects.filter(target=self.parent.core.hero):
            icon = QLabel()
            icon.setPixmap(QPixmap(self.api.icons[effect.icon]).scaled(QSize(self.icon_size, self.icon_size)))
            self.layout().insertWidget(2, icon)
            icon.setToolTip(effect.info)
            self.icons.append(icon)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.layout().addWidget(self.spacerItem)
        hero = self.parent.core.hero
        self.hstatus.setText('<b>%s%s(%s)</b> HP: %s/%s MP: %s/%s' % (
        hero.Name, ' %s ' % hero.Title if hero.Title else '', hero.Level, hero.HP, hero.TotalHP, hero.MP, hero.TotalMP))
