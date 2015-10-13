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
from etherstone.base import EtherIntegration
import re

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
        wi = EtherIntegration(self, UI=False)
        mymainwidget = wi.getWebView(toolbar=True)

        def nfilter(name, root):
            if not os.path.isdir(os.path.join(root, name)):
                file = open(os.path.join(root, name))
                title = re.findall('<TITLE>([^<]*)</TITLE>', file.read())
                if title:
                    title = title[0].replace(
                        'Improved ADOM Guidebook - ', 'GB - ')
                    title = title.replace('ADOM Manual - ', 'Manual - ')
                else:
                    title = name
                file.close()
                return title
            else:
                return name

        def ffilter(path):
            if not os.path.isdir(path):
                if path.endswith('.html'):
                    return True

            return False

        global app
        app = mymainwidget

        def onEmptyFind(reverse=False):
            if not hasattr(self, 'cpos'):
                self.cpos = 0
                self.q = app.view.q
            else:
                self.cpos += 1
                self.nf = False

            if self.q != app.view.q:
                del self.cpos
                app.view.onEmptyFind()
            else:
                items = app.dirtree.WFind(app.view.q, True, True)
                if items and len(items) == self.cpos + 1:
                    del self.cpos
                else:
                    try:
                        url = items[self.cpos].url
                        app.view.show(url)
                        self.nf = True
                        self.api.showMessage('File num: %d' % (self.cpos + 1))
                        app.view.WFind(app.view.q)
                    except Exception as e:
                        try:
                            del self.cpos
                        except:
                            pass

        def retryFind():
            if hasattr(self, 'q') and self.nf:
                app.view.WFind(self.q)

        mymainwidget.view.onEmptyFind = onEmptyFind
        mymainwidget.api = API()

        mymainwidget.view.setHomePage('file://' + os.path.join(CWD, 'adomgb/adomgb-toc.html'))
        mymainwidget.view.loadHomePage()
        mymainwidget.dirtree = WinterDirTree(
            mymainwidget, os.path.join(CWD, 'adomgb/'), 'Guide book', mymainwidget.view, ffilter, nfilter)


        mymainwidget.view.loadFinished.connect(retryFind)

        self.sideBar = WinterSideBar(self)

        self.createSBAction('list', 'Content', mymainwidget.dirtree.getWidget(
            True, True), toolbar=True, keyseq='ALT+1')

        self.setMainWidget(mymainwidget)

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

    ui.show()
    api = API()

    endtime = datetime.now()
    delta = endtime - starttime
    ui.api.info('Initialization time: %s' % delta)
    # print 'Started'
    qtapp.exec_()


if __name__ == '__main__':
    main()
