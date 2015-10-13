#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, time

starttime = datetime.now()

import sys
import os


sys.path.append('Garden')
sys.path.append('../Garden')
sys.path.append('../../Garden')
from winterstone.extraQt import WinterLine

from winterstone.snowflake import *
from winterstone.extraQt import WinterEditor, WinterDirTree

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from winterstone.extraQt import WinterSideBar

from winterstone.baseQt import WinterQtApp, API, WinterAction, SBAction, WinterAPI

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
        widget = QWidget(self)
        widget.setLayout(QFormLayout())
#        widget.setFont(QFont('Comfortaa'))
        s = QCheckBox('')
        s.setChecked(True)
        widget.layout().addRow('C&hecked', s)
        le = QLineEdit('Bood00m')
        le.setMaximumWidth(180)
        widget.layout().addRow('LineEdit', le)
        widget.layout().addRow('Not checked', QCheckBox('test'))
 #        widget.layout().addRow('Checkbox',QCheckBox('boom'))
        b = QPushButton('Click me!')
        b.clicked.connect(self.t)
#        b.setWidth(70)
        widget.layout().addRow('Button', b)
        widget.layout().addRow('Spinner', QSpinBox())
        pb = QProgressBar()
        pb.setValue(50)
        pb.setMaximumWidth(180)
        widget.layout().addRow('Progress', pb)
#        widget.layout().addRow('Slider',QSlider(Qt.Horizontal))

#        path=CWD+'themes/%s/'%API().config.options.theme
#        pos=QWidget()
#        pos.setLayout(QHBoxLayout())
#        l=QLabel()
#        l.setPixmap(QPixmap(path+'cross.png').scaled(QSize(18,18)))
#        pos.layout().addWidget(l)
#        pos.layout().addWidget(QLabel('Positive'))
#        pos.layout().setAlignment(Qt.AlignLeft | Qt.AlignTop)
#        widget.layout().addRow('Info',pos)
        tab = QTabWidget()
        tab.addTab(widget, 'Test')
        tab.addTab(QTableWidget(3, 4), 'Test2')

        self.setMainWidget(tab)

    def t(self):
        print('pressed')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QMainWindow.close(self)


def resolve(map1, map2, key):
    return 'overwrite'


def main():
    qtapp = QApplication(sys.argv)
    qtTranslator = QTranslator()
    if qtTranslator.load(CWD + "lang/%s.qm" % QLocale.system().name()):
        qtapp.installTranslator(qtTranslator)
        # print QLocale.system().name(), qtapp.tr('Translate loaded')
    ui = UI(qtapp)

    if ui.config.options.ui.maximized:
        ui.showMaximized()
    else:
        ui.show()
    api = ui.api

    endtime = datetime.now()
    delta = endtime - starttime
    ui.api.info('Initialization time: %s' % delta)
    # print 'Started'
    qtapp.exec_()


if __name__ == '__main__':
    main()
