#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, time

starttime = datetime.now()

import sys, os


sys.path.append('Garden')
sys.path.append('../../Garden')
from winterstone.extraQt import WinterLine

from winterstone.snowflake import *
from winterstone.extraQt import WinterEditor, WinterDirTree
from etherstone.base import EtherIntegration

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.extraQt import WinterSideBar

from winterstone.baseQt import WinterQtApp, API, WinterAction, SBAction
from ravenClasses import *

__author__ = 'averrin'

class UI(WinterQtApp):
    '''
        Main class
    '''

    def __init__(self, app):
        '''
            Create your own mymainwidget inherits QWidget and set it through self.setMainWidget. For future access use self.mainWidget property
        '''

        WinterQtApp.__init__(self, app)


    def _afterMWInit(self):
        '''
            Fired after MainWindow initialisation
        '''

        pass

    def _afterAppInit(self):
        '''
            Fired after WinterApp initialisation
        '''

        wi = EtherIntegration(self, UI=False)

        widget = QWidget(self)
        widget.setLayout(QVBoxLayout())

        mmw = Panel(self)
        mmw.api = self.api
        mmw.tree = Tree(mmw, self.api.CWD)
        mmw.tree.setDragDropMode(QAbstractItemView.InternalMove)

        self.setMainWidget(widget)
        self.sideBar = WinterSideBar(self)

        newpanel = NewForm(mmw)

        css = CssPanel(self, mmw)

        mmw.toggle({True: 1, False: 0}[self.config.options.app.start_editor])

        self.createSBAction('squares', 'Content', mmw.tree.getWidget(), toolbar=True,
            keyseq=self.config.options.app.tree_shortcut)
        self.createSBAction('newPage', 'New', newpanel, toolbar=True, keyseq=self.config.options.app.new_shortcut)
        self.createSBAction('css', 'Style', css, toolbar=True, keyseq=self.config.options.app.css_shortcut)
        self.createSBAction('edit', 'Edit', EditForm(mmw), toolbar=False, keyseq='F5')

        doctree = DocTree(mmw)
        self.createSBAction('squares', 'gDocs', doctree, toolbar=False, keyseq='Ctrl+D')

        cmd = CommandLine(mmw)

        self.cmd = cmd

        self.createAction('', 'Focus cmd', self.cmd.setFocus, keyseq='F3')
        self.createAction('list', 'Focus tree', mmw.tree.setFocus, keyseq='F2')
        self.createAction('cross', 'Del current', mmw.tree.delPage, keyseq='F8')

        self.createAction('', 'Action Editor', lambda: mmw.setCurrentIndex(2), keyseq='F7')
        self.createAction('', 'New page short', lambda: self.cmd.shortcut(':new '), keyseq='CTRL+N')
        self.createAction('', 'View page short', lambda: self.cmd.shortcut(':view '), keyseq='CTRL+E')

        widget.layout().addWidget(cmd)
        widget.layout().addWidget(mmw)

        self.mmw = mmw

        ae = QWidget()
        gird = QGridLayout()
        x = 0
        y = 0
        sbactions = SBAction.objects.all()
        actions = WinterAction.objects.all()
        for a in actions:
            sbactions.append(a)
        for action in sbactions:
            label = QLabel('%s\n%s' % (action.text(), action.shortcut().toString()))
            icon = QLabel('')

            pixmap = action.icon().pixmap(QSize(48, 48))
            if pixmap.isNull():
                pixmap = QPixmap(self.api.icons['newPage']).scaled(QSize(48, 48))
            icon.setPixmap(pixmap)
            widget = QWidget()
            widget.setLayout(QHBoxLayout())
            widget.layout().addWidget(icon)
            widget.layout().addWidget(label)
            widget.layout().setAlignment(Qt.AlignLeft)
            gird.addWidget(widget, y, x)
            x += 1
            if x > 3:
                x = 0
                y += 1
        gird.setAlignment(Qt.AlignTop)
        ae.setLayout(gird)
        self.mmw.insertWidget(2, ae)

        mmw.setFocus()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QMainWindow.close(self)


def main():
    qtapp = QApplication(sys.argv)
    api = API()
    ui = UI(qtapp)

    ui.show()

    endtime = datetime.now()
    delta = endtime - starttime
    api.info('Initialization time: %s' % delta)
    qtapp.exec_()


if __name__ == '__main__':
    main()
