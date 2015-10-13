import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from winterstone.baseQt import API, SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons
from etherstone.base import EtherIntegration
from winterstone.extraQt import WinterEditor, CustomStyle, CustomLexer, FocusProxy
from augment import *
from etherstone.base import EtherWebView
from winterstone.base import WinterObject
from winterstone.base import Borg
from winterstone.extraQt import WinterDirTree
from winterstone.extraQt import WinterSearch, WinterLine
from config import Config
from ravenClasses import *
#from PyQt4.Qsci import QsciLexerCSS


class Core(object):
    """
        Store all your app logic here
    """

    def _afterInit(self):
        """
            when application totally init
        """
        self.api = API()

    def main(self):
        """
            dummy for main core method.
        """
        #        self.view.loadPage('main.html')

        self.wi = EtherIntegration(UI=True)

        #        self.view=self.app.mainWidget.view
