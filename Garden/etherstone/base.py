import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebView, QWebPage
#from jinja2.loaders import FileSystemLoader
from winterstone.snowflake import getFileContent, CWD, VAULT
from winterstone.base import WinterObject
import re
from winterstone.base import Borg
from urllib.request import urlopen
from winterstone.baseQt import API, WinterQtApp
from winterstone.extraQt import WinterSearch

try:
    from bottle import *

    TEMPLATE_PATH.append(CWD + 'templates/')
    BOTTLE_SUPPORT = True
except:
    BOTTLE_SUPPORT = False

    def route(*args):
        pass

try:
    from jinja2 import Environment, PackageLoader

    JINJA2_SUPPORT = True
except ImportError:
    JINJA2_SUPPORT = False
#    print('WARNING: JINJA2_SUPPORT disabled')

class EtherServer(QThread):
    def __init__(self, port=8080):
        QThread.__init__(self)
        self.port = port
        self.quiet = False
        debug(True)

    def run(self):
        run(host='localhost', port=self.port, quiet=self.quiet)


class EtherIntegration(Borg):
    def __init__(self, parent='', UI=False):
        Borg.__init__(self)
        self.ui = UI
        if not hasattr(self, 'parent') and parent:
            self.parent = parent
            if self.ui:
                self.server = EtherServer(port=4801)
                self.server.start()

    def showGreeting(self):
        self.parent.statusBar.showMessage(urlopen('http://api.averr.in/greeting').read())

    def getWebView(self, url='', toolbar=False, debug=False):
        if not self.ui:
            view = EtherWebView()
        else:
            view = EtherWebUI()
        if url:
            view.load(EtherUrl(url))

        frame = QWidget()
        frame.view = view
        lay = QVBoxLayout()
        if toolbar:
            frame.tb = QToolBar(frame)
            lay.addWidget(frame.tb)
            frame.tb.addWidget(QWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
            frame.tb.addWidget(QLabel('Search:  '))
            frame.tb.addWidget(WinterSearch(view))
        lay.addWidget(view)
        frame.setLayout(lay)

        if debug:
            view.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)

        return frame

#    @route('/static/:dir/:subdir/:sub_subdir/:file_name')
#    @route('/static/:dir/:subdir/:file_name')
#    @route('/static/:dir/:file_name')
#    def server_static(dir,subdir='',sub_subdir='',file_name=''):
#        root='%sstatic/%s/' % (CWD,dir)
#        if subdir:
#            root+='%s/' % subdir
#        if sub_subdir:
#            root+='%s/' % sub_subdir
#        return static_file(file_name, root=root)
#
#    @route('/vault/:dir/:subdir/:sub_subdir/:file_name')
#    @route('/vault/:dir/:subdir/:file_name')
#    @route('/vault/:dir/:file_name')
#    def server_vault(dir,subdir='',sub_subdir='',file_name=''):
#        root='%s/%s/' % (VAULT,dir)
#        if subdir:
#            root+='%s/' % subdir
#        if sub_subdir:
#            root+='%s/' % sub_subdir
#        return static_file(file_name, root=root)
#
#    @route('/images/:dir/:subdir/:sub_subdir/:file_name')
#    @route('/images/:dir/:subdir/:file_name')
#    @route('/images/:dir/:file_name')
#    def server_static_images(dir,subdir='',sub_subdir='',file_name=''):
#        root='%sstatic/images/%s/' % (CWD,dir)
#        if subdir:
#            root+='%s/' % subdir
#        if sub_subdir:
#            root+='%s/' % sub_subdir
#        return static_file(file_name, root=root)



class EtherWebView(QWebView):
    def __init__(self, inspect=False):
        QWebView.__init__(self)
        self.wi = EtherIntegration()
        self.hp = EtherUrl()
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.linkClicked.connect(self.lc)
        self.titleChanged.connect(self.tc)
        self.api = API()
        self.setRenderHint(QPainter.HighQualityAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.Antialiasing)
        settings = self.page().settings()
        settings.setFontFamily(QWebSettings.StandardFont, self.wi.parent.config.options.webview.main_font)
        settings.setFontSize(QWebSettings.DefaultFontSize, 24)
        if inspect:
            self.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        palette = QPalette()
        palette.setBrush(QPalette.Base, QBrush(QColor(self.wi.parent.config.options.webview.bg_color)))
        self.page().setPalette(palette)


    def tc(self, text):
        if text:
            self.lc(QUrl(text))

    def lc(self, link):
        if link.scheme() == 'winter':
            args = str(link.path())[1:].split('/')
            method = str(link.authority())
            try:
                module, method = method.split('.')
            except ValueError:
                module = 'main'
            try:
                if args[0]:
                    self.emit('exec',method, module,*args)
                else:
                    self.emit('exec',method, module)
                self.wi.parent.debug('Execute: %s(%s) [%s]' % (method, args, module))
            except Exception as e:
                self.api.error(e)
#        elif link.authority() not in ['#', '','localhost:4801']:
        elif link.authority() not in ['#', '']:
            self.wi.parent.debug('GoTo: [%s] %s%s' % (link.scheme(), link.authority(), link.path()))
            self.load(link)
        else:
            pass


    def loadHomePage(self):
        self.load(self.hp)


    def setHomePage(self, link):
        self.hp = EtherUrl(link)

    def show(self, item):
        self.load(EtherUrl(item.url))
        self.wi.parent.setTitle(item.name)

    def cd(self, path):
        pass

    def WFind(self, text):
    #        self.findText('', QWebPage.HighlightAllOccurrences)
        self.q = text
        return self.findText(text)

    def WFindNext(self):
        res = self.findText(self.q)
        if res:
            return res
        else:
            self.onEmptyFind()
            return res

    def WFindPrev(self):
        res = self.findText(self.q, QWebPage.FindBackward)
        if res:
            return res
        else:
            self.onEmptyFind(reverse=True)
            return res

    def js(self, line):
        self.page().currentFrame().evaluateJavaScript(line)

    def onEmptyFind(self, reverse=False):
        self.api.showMessage('No string found')


class EtherUrl(QUrl):
    def __init__(self, link=''):
        if link and link[0] == '~':
            link = os.path.expanduser(link)
        QUrl.__init__(self, link)


class EtherWebUI(EtherWebView):
    def __init__(self, *args, **kwargs):
        EtherWebView.__init__(self, *args, **kwargs)


    #    def load(self,url):
    #        todo: implement template dirs
    #        self.loadPage(os.path.basename(str(url.path())))

    def loadPage(self, url, **kwargs):
    #        html = template(template_name, STATIC=CWD+'static/', **kwargs)
    #        self.setContent(html, "text/html", QUrl('file://%s' % CWD))
        self.load(QUrl('http://localhost:4801' + url))
