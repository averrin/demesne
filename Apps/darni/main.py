#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

starttime = datetime.now()

import sys


sys.path.append('Garden')
sys.path.append('../Garden')
sys.path.append('../../Garden')

from winterstone.snowflake import *

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.extraQt import WinterSideBar

from winterstone.baseQt import WinterQtApp, API

from rpg.base import *
from ui import *

__author__ = 'averrin'


class UI(WinterQtApp):
    """
        Main class
    """

    def __init__(self, app):
        """
            Create your own mymainwidget inherits QWidget and set it through self.setMainWidget. For future access use self.mainWidget property
        """
        WinterQtApp.__init__(self, app)

    def _afterMWInit(self):
        """
            Fired after MainWindow initialisation
        """

        pass

    def _afterAppInit(self):
        """
            Fired after WinterApp initialisation
        """
        widget = QWidget()
        self.setMainWidget(widget)
        widget.setLayout(QFormLayout())
        self.name = QLineEdit()
        widget.layout().addRow(self.tr('Name'), self.name)
        widget.layout().addRow('', QPushButton('Create'))
        widget.layout().setAlignment(Qt.AlignTop)
#        widget.layout()
        self.startGame()

    def startGame(self):
#        print(self.api.icons[self.api.config.options.app.inv_icon])
        widget = QTabWidget(self)
        widget.setLayout(QVBoxLayout())
        self.inv = InventoryPanel(self, self.core.hero)
        self.doll = DollPanel(self, self.core.hero)

        tables = QWidget()

        tables.setLayout(QGridLayout())
        widget.layout().addWidget(tables)
        hi = QWidget()
        hi.setLayout(QHBoxLayout())

        tables.layout().addWidget(hi)
        tables.layout().addWidget(self.inv, 0, 1)

        self.stats = StatsPanel(self, self.core.hero)
        hi.layout().addWidget(self.stats)
        hi.layout().addWidget(self.doll)

        self.log = GameLog(self)

        self.status = EffectsBar(self)
        #        widget.layout().addWidget(self.status)
        self.log.setTitleBarWidget(self.status)

        # panel = QStackedWidget()
        # tables.layout().addWidget(panel,1,1)

        self.setMainWidget(widget)
        self.sideBar = WinterSideBar(self)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.log)

        icon = QIcon(self.api.icons[self.api.config.options.app.inv_icon])
        widget.addTab(tables, icon, 'Inventory')
        icon = QIcon(self.api.icons[self.api.config.options.app.vault_icon])
        vt = QWidget()
        vt.setLayout(QVBoxLayout())
        self.vault = ContainerPanel(self, self.core.vault)
        vt.layout().addWidget(self.vault)

        reroll = QPushButton('ReRoll')
        reroll.clicked.connect(self.core.reroll)
        vt.layout().addWidget(reroll)

#        widget.addTab(vt, icon, 'Vault')
        self.core.start()

        self.createSBAction('Icons/inv_misc_bag_10', 'Vault', vt, toolbar=True, keyseq='F5')
#        self.api.setBadge('Vault','white','new','black')
        # self.api.setProgress('Vault', 60, '#6666ff')

#        self.api.setEmblem('Vault','red')
#        self.api.delBadge('Vault')
#        SBAction.objects.get(title='Vault').setAlpha(100)
#        self.api.flashAction('Vault',3)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QMainWindow.close(self)

    def getLog(self):
        return self.log


def resolve(map1, map2, key):
    return 'overwrite'


def main():
    qtapp = QApplication(sys.argv)
    qtTranslator = QTranslator()
    if qtTranslator.load(CWD + "lang/%s.qm" % QLocale.system().name()):
        qtapp.installTranslator(qtTranslator)
        print(QLocale.system().name(), qtapp.tr('Translate loaded'))
    ui = UI(qtapp)

    if ui.config.options.ui.maximized:
        ui.showMaximized()
    else:
        ui.show()
    # api = ui.api

    # if api.config.options.app.showRavenor:
    #     showRavenor(ui)

    endtime = datetime.now()
    delta = endtime - starttime
    ui.api.info('Initialization time: %s' % delta)

    print('Started')
    qtapp.exec_()


def showRavenor(ui):
    sys.path.append('../Ravenor')
    import raven
    from winterstone.base import WinterConfig
    from config import ConfigMerger

    raven.API().CWD += '../Ravenor/'
    ravenconfig = WinterConfig(file(raven.API().CWD + 'config/main.cfg'))
    darniconfig = WinterConfig(file(CWD + 'config/main.cfg'))
    merger = ConfigMerger(resolve)
    merger.merge(darniconfig.options.app, ravenconfig.options.app)
    API().config = darniconfig
    from etherstone.base import EtherIntegration

    wi = EtherIntegration(ui, UI=False)
    ravenor = raven.Panel(ui)
    ravenor.tree = raven.Tree(ravenor, ravenor.api.CWD)
    newpanel = raven.NewForm(ravenor)
    ui.sideBar = WinterSideBar(ui)
    ui.createSBAction('squares', 'Content', ravenor.tree.getWidget(), toolbar=True,
        keyseq=darniconfig.options.app.tree_shortcut)
    ui.createSBAction('newPage', 'New', newpanel, toolbar=True, keyseq=darniconfig.options.app.new_shortcut)
    ui.createSBAction('newPage', 'Edit', newpanel, toolbar=False, keyseq=darniconfig.options.app.new_shortcut)

    cmd = raven.CommandLine(ravenor)
    lay = QWidget()
    lay.setLayout(QVBoxLayout())
    lay.layout().addWidget(cmd)
    lay.layout().addWidget(ravenor)

    ui.mainWidget.addTab(lay, QIcon(raven.API().CWD + 'icons/app.png'), 'Ravenor')


if __name__ == '__main__':
    main()
