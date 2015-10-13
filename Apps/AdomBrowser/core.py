from PyQt5.QtGui import *
from PyQt5.QtCore import *
from winterstone.baseQt import API
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons

class Core(QObject):
    """
        Store all your app logic here
    """

    def _afterInit(self):
        """
            when application totally init
        """
        self.api = API()
        self.main()
        # self.api.info('Core loaded.')


    def main(self):
        """
            dummy for main core method.
        """
        pass
