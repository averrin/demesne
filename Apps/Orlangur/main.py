#!/usr/bin/env python
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
from winterstone.baseQt import WinterQtApp, SBAction, WinterAction
from winterstone.terminal import WinterTerminal, WinterTermManager

from PyQt4.QtWebKit import QWebView, QWebPage, QWebSettings

import json
import re

import paramiko as ssh

from core import Editor

__author__ = 'averrin'

#TODO: fix syntax highlighter crashes

#TODO: move this classes to core        
            

class UI(WinterQtApp):
    """
        Main class
    """

    def __init__(self, app):
        """
            Create your own mymainwidget inherits QWidget and set it through self.setMainWidget. For future access use self.mainWidget property
        """
        self.app = app
        WinterQtApp.__init__(self, app)

    def getApp(self):
        return self.app

    def _afterMWInit(self):
        """
            Fired after MainWindow initialisation
        """

        pass

    def _afterAppInit(self):
        """
            Fired after WinterApp initialisation
        """
        widget = QWidget(self)
        self.setMainWidget(widget)

        self.list = QListWidget()
        self.editor = Editor(self, autosave=self.api.config.options.app.autosave)
        
        from PyQt4.Qsci import QsciScintilla
        self.editor.setWrapMode( QsciScintilla.WrapCharacter)

        self.editor.editor.textChanged.connect(self.editor.checkErrors)

        self.lp = QWidget()
        self.lp.setLayout(QVBoxLayout())
        
        self.rp = QTabWidget()
        self.rp.setTabPosition(QTabWidget.West)
        
        self.rp.tab_list = {}

        self.ltb = QToolBar(self)
        self.ltb.addAction(self.api.ex('createAction')('doc', 'Edit Meta', self.core.editMeta))
        self.ltb.addAction(self.api.ex('createAction')('cloud-plus', 'Add collection', self.core.addCollection))
        self.ltb.addAction(self.api.ex('createAction')('cloud-minus-210', 'Delete collection', self.core.delCollection))
        self.ltb.addAction(self.api.ex('createAction')('doc-attached', 'Backup collections', self.core.backUp))     # Move backups to Nervarin plugin


#        WinterAction.objects.get(title='Save').setShorcut('Ctrl+S')          #TODO: make it work
        self.editor.editor.setReadOnly(True)

        self.lp.layout().addWidget(self.ltb)
        self.lp.layout().addWidget(self.list)

        widget.setLayout(QHBoxLayout())
#        widget.layout().addWidget(self.lp)
        self.api.createSBAction('app', 'Collections', self.lp, toolbar=True) #.showWidget()
        self.terminal = WinterTermManager(self)
        self.termtab = self.addTab(self.terminal, 'Console')        #TODO: add aliases
        self.et = self.addTab(self.editor, 'Editor')

        self.viewer = QWebView()
        self.item_list = QListWidget()
        self.il = self.addTab(self.item_list, 'List')
        self.et = self.addTab(self.viewer, 'HTML')
        
        widget.layout().addWidget(self.rp)

        self.list.itemClicked.connect(self.core.onClick)

        self.addListItem = self.item_list.addItem
#        self.selectTab = self.rp.setCurrentIndex
#        self.addTab = self.rp.addTab

        self.core.fillList()
        self.api.pushToIP({'orlangur': self.core.db})

        self.pb = QProgressBar(self.statusBar)
        self.statusBar.addWidget(self.pb)
        self.pb.setMaximum(0)
        self.pb.setMinimum(0)
        
    def addTab(self, widget, title):
        self.rp.tab_list[title] = self.rp.count()
        self.rp.addTab(widget, title)
    
    def selectTab(self, title):
        self.rp.setCurrentIndex(self.rp.tab_list[title])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QMainWindow.close(self)
            

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
    api = ui.api

    endtime = datetime.now()
    delta = endtime - starttime
    ui.api.info('Initialization time: %s' % delta)
    print('Started')
    qtapp.exec_()


if __name__ == '__main__':
    main()
