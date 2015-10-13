#coding=utf-8

import os
import shutil
import urllib.request as urllib2
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from winterstone.baseQt import API, SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons
from etherstone.base import EtherIntegration
from winterstone.extraQt import WinterEditor, CustomStyle, CustomLexer, FocusProxy
from augment import *
from etherstone.base import EtherWebView
from io import StringIO
from string import Template
from winterstone.base import WinterObject, WinterConfig
from winterstone.base import Borg
from winterstone.extraQt import WinterDirTree
from winterstone.extraQt import WinterSearch, WinterLine
from config import Config
import quopri
# from BeautifulSoup import BeautifulSoup
# from Crypto.Cipher import DES
import re
import mako.template
import haml

class Page(WinterObject):
    def __init__(self, path):
        WinterObject.__init__(self)
        self.path = os.path.expanduser(path)
        self.text = ''
        try:
            self.config = WinterConfig(open(self.path + '/__page.cfg'))
            print(self.config)
            # print(self.prefs, self.prefs.cfg)
            # self.config = self.prefs.cfg

            if not self.config:
                raise IOError()
        except IOError:
            f = open(self.path + '/__page.cfg', 'w')
            f.write('cfg: !mapping\n    empty: ""')
            f.close()
            self.config = WinterConfig(open(self.path + '/__page.cfg'))
            # self.config = self.prefs.cfg

            self.config.title = os.path.split(path)[1]
            self.config.template = API().config.options.app.default_template

        #        finally:
        self.title = self.config.title
        self.template = self.config.template


    def getText(self):
        if not self.text:
            with open(self.path + '/__page.text') as f:
                self.text = quopri.decodestring(f.read())
        return self.text


class DocTree(QTreeWidget):
    def __init__(self, parent):
        QTreeWidget.__init__(self, parent)
        return
        import gdata
        import gdata.docs.client

        client = gdata.docs.client.DocsClient()
        client.ClientLogin('averrin@gmail.com', 'oWertryN8..//vim', API().config.info.title)
        self.feed = client.GetDocList()
        self.fill()

    def fill(self):
    #        root=QTreeWidgetItem(['Docs'])
        self.setHeaderLabel('Docs')
        #        self.insertTopLevelItem(0, root)
        for doc in self.feed.entry:
            it = QTreeWidgetItem([doc.title.text])
            self.addTopLevelItem(it)


class Tree(QTreeWidget):
    def __init__(self, parent, path):
        QTreeWidget.__init__(self, parent)
        self.path = os.path.expanduser(path)
        self.parent = parent
        self.parent.tree = self
        self.searchable_exts = ['.txt', '.html', '.text']
        self.currentPage = ''

        self.editor = parent.editor

        self.setHeaderLabel('Content')

        self.api = parent.api

        #            self.itemExpanded.connect(self.expanded)
        self.itemActivated.connect(self.ic)
        self.itemClicked.connect(self.ic)
        #            self.itemDoubleClicked.connect(self.dic)

        self.fill()

    def ic(self, item, column=0):
        page = self.pages[os.path.split(item.url)[0]]
        self.editor.open(item.url)
        #            self.editor.editor.setText(page.getText())
        #            self.editor.filename=item.url
        self.currentPage = page
        self.parent.toggle(1)
        self.parent.parent.setWindowTitle('%s [%s]' % (self.parent.parent.config.info.title, page.title))

    def fill(self):
        self.clear()
        n = 0
        items = {}
        for (path, dirs, files) in os.walk(self.path + 'organizer'):
            if '__page.text' in files:
                page = Page(path)
                if not n:
                    item = self.headerItem()
                    item.path = self.path

                    self.insertTopLevelItem(0, item)
                    item.setExpanded(True)

                name = page.title
                it = QTreeWidgetItem([name])
                it.name = name
                if os.path.isfile(path + '/__icon.png'):
                    it.setIcon(0, QIcon(path + '/__icon.png'))
                else:
                    if dirs:
                        it.setIcon(0, QIcon(self.api.icons['dot']))
                    else:
                        it.setIcon(0, QIcon(self.api.icons['blank']))

                if not n:
                    self.insertTopLevelItem(0, it)
                    it.setExpanded(True)
                    self.currentPage = page
                    self.root = path
                else:
                    rootitem = items[os.path.split(path)[0]].item
                    rootitem.addChild(it)
                n += 1
                it.url = path + '/__page.text'
                page.item = it
                it.page = page
                items[path] = page
        self.pages = items
        self.items = items.values()


    def dropEvent(self, event):
        shutil.move(self.currentItem().page.path, self.itemAt(event.pos()).page.path)
        event.accept()
        self.fill()


    def WFind(self, text, full=False, getlist=False):
        its = []
        if self.full_text.checkState() == Qt.Checked or full:
            for i in self.items:
                i = i.item
                basename, extension = os.path.splitext(i.url)
                if extension in self.searchable_exts:
                    f = open(i.url)
                    for line in f:
                        if str(text).lower() in line.lower():
                            its.append(i)
                            break
                    f.close()
        else:
            its = self.findItems(text, Qt.MatchContains)

        for i in self.items:
            i = i.item
            if i not in its:
                i.setHidden(True)
            else:
                i.setHidden(False)
        if not getlist:
            return len(its)
        else:
            return its

    def getWidget(self, search=False, full=False):
        frame = FocusProxy(self)
        lay = QVBoxLayout()
        if search:
            frame.tb = QToolBar(frame)
            lay.addWidget(frame.tb)
            frame.tb.addWidget(QLabel('Search:  '))
            frame.tb.addWidget(WinterSearch(self))
            #            frame.tb.addWidget(QWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
            if full:
                self.full_text = QCheckBox('Full text')
                frame.tb.addWidget(self.full_text)
        lay.addWidget(self)
        frame.setLayout(lay)

        return frame

    def get_text(self, link):
        content = urllib2.urlopen('http://www.instapaper.com/text?u=' + link).read()
        soup = BeautifulSoup(content)
        title = soup.find('title').getText().decode('utf8')
        title = re.sub('\W*', '', title)
        content = str(soup.find('div', {'id': 'story'}))
        content += '<script>document.getElementById("sm").innerHTML="%s";' % str(
            soup.find('div', {'class': 'sm'}).getText())
        content += 'document.getElementById("orig").href="%s";' % str(
            soup.find('div', {'class': 'bar top'}).fetch()[0].attrs[0][1])
        content += '</script>'
        content = re.sub('(?<![>\s])\n+(?![<\s])', ' ', content)
        return content, title

    def newPage(self, title, root, template='', iconpath=''):
        if type(title).__name__ == 'tuple':
            title = title[0]

        content = ''
        if re.match('(http|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?', title):
            content, title = self.get_text(title)
            iconpath = API().icons['cloud']
        path = '%s/%s' % (root, title)
        try:
            os.mkdir(path)
            success = True
        except OSError as e:
            API().error(e)
            API().dialog('warning', 'Dublicate page name', 'Can\'t create new page. Plz change page title.')
            success = False
        if success:
            for fn in ['__page.text', '__page.cfg']:
                f = open(path + '/' + fn, 'w')
                if fn == '__page.text':
                    tf = content
                else:
                    tf = ''
                f.write(tf)
                f.close()
            cfg = WinterConfig(open(path + '/' + '__page.cfg'))
            if not template:
                template = API().config.options.app.default_template
            cfg.cfg = {'title': title, 'template': template}
            cfg.save(open(path + '/' + '__page.cfg', 'w'))

            if iconpath:
                shutil.copyfile(iconpath, path + '/__icon.png')

            self.parent.tree.fill()
            SBAction.objects.get(title='Content').forceShowWidget()
            page = Page.objects.get(path=path)
            self.parent.tree.ic(page.item, 0)
            self.parent.toggle(0)

    def delPage(self, page=''):
        if not page:
            page = self.currentPage
        shutil.rmtree(page.path)
        self.parent.tree.fill()
        default = Page.objects.get(path=self.root)
        self.parent.tree.ic(default.item, 0)

    def crypt(self, passw):
    #            if not page:
    #                page=self.currentPage
        if len(passw) < 8:
            raise Exception('Password length must be >= 8 chars')
        text = str(self.parent.editor.text())
        while len(text) % 8 != 0 or len(text) < 8:
            text += ' '
        key = DES.new(passw[:8], DES.MODE_ECB)
        crypted = key.encrypt(text)
        self.parent.editor.editor.setText(crypted)
        self.crypted = crypted
        self.key = key

    def decrypt(self, passw):
        if len(passw) < 8:
            raise Exception('Password length must be >= 8 chars')
        text = str(self.parent.editor.text().toAscii())

        key = DES.new(passw[:8], DES.MODE_ECB)
        decrypted = key.decrypt(text)
        self.parent.editor.editor.setText(decrypted.decode('utf-8'))

    def viewPage(self, *args):
        page = Page.objects.get(title=' '.join(args))
        if page:
            self.ic(page.item)


class NewForm(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.api = API()
        l = QGridLayout()
        self.setLayout(QVBoxLayout())
        self.layout().addLayout(l)
        #        newpanel.layout().addWidget(QWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        l.addWidget(QLabel('Title:'), 0, 0)
        self.title = QLineEdit()
        l.addWidget(self.title, 0, 1)
        l.addWidget(QLabel('Template:'), 1, 0)
        self.cb = QComboBox()
        self.cb.addItems(os.listdir(self.api.CWD + 'templates/html'))
        l.addWidget(self.cb, 1, 1)

        self.iconpath = API().icons['newPage']
        icon = QPixmap(self.iconpath)
        iv = QLabel()
        iv.setPixmap(icon)
        l.addWidget(iv, 2, 0)
        self.icon = iv

        chi = QPushButton('Change')
        l.addWidget(chi, 2, 1)
        l.setAlignment(Qt.AlignTop)
        chi.clicked.connect(self.chi)

        create = QPushButton('Create')
        l.addWidget(create, 3, 1)
        l.setAlignment(Qt.AlignTop)
        create.clicked.connect(self.new)

        tpl = os.listdir(self.api.CWD + 'templates/html')
        tpl = tpl.index(API().config.options.app.default_template)
        self.cb.setCurrentIndex(tpl)

        self.title.returnPressed.connect(self.new)


    def chi(self):
        icon = QFileDialog.getOpenFileName(self, 'Open file', os.path.expanduser('~'))
        self.icon.setPixmap(QPixmap(icon))
        self.iconpath = icon

    def new(self):
        title = str(self.title.text())
        template = str(self.cb.currentText())
        root = self.parent.tree.root
        self.parent.tree.newPage(title, root, template, self.iconpath)


class EditForm(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        l = QGridLayout()
        self.setLayout(QVBoxLayout())
        self.layout().addLayout(l)
        self.api = API()
        #        newpanel.layout().addWidget(QWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        l.addWidget(QLabel('Title:'), 0, 0)
        self.title = QLineEdit()
        l.addWidget(self.title, 0, 1)
        l.addWidget(QLabel('Template:'), 1, 0)
        self.cb = QComboBox()
        self.cb.addItems(os.listdir(self.api.CWD + 'templates/html'))
        l.addWidget(self.cb, 1, 1)

        self.iconpath = API().icons['newPage']
        icon = QPixmap(self.iconpath)
        iv = QLabel()
        iv.setPixmap(icon)
        l.addWidget(iv, 2, 0)
        self.icon = iv

        chi = QPushButton('Change')
        l.addWidget(chi, 2, 1)
        l.setAlignment(Qt.AlignTop)
        chi.clicked.connect(self.chi)

        apply = QPushButton('Apply')
        l.addWidget(apply, 3, 1)
        l.setAlignment(Qt.AlignTop)
        apply.clicked.connect(self.apply)

        self.title.returnPressed.connect(self.apply)

    def onShow(self):
        page = self.parent.tree.currentPage
        self.title.setText(page.title)
        tpl = os.listdir(self.api.CWD + 'templates/html')
        tpl = tpl.index(page.template)
        self.cb.setCurrentIndex(tpl)
        self.icon.setPixmap(QPixmap(page.path + '/__icon.png'))
        self.iconpath = page.path + '/__icon.png'

    def apply(self):
        page = self.parent.tree.currentPage
        page.config.title = str(self.title.text())
        page.config.template = str(self.cb.currentText())
        page.prefs.save(open(page.path + '/__page.cfg', 'w'))

        if self.iconpath != page.path + '/__icon.png':
            shutil.copyfile(self.iconpath, page.path + '/__icon.png')
        self.parent.tree.fill()

        API().showMessage('%s saved' % page.title)
        SBAction.objects.get(title='Content').forceShowWidget()
        page = Page.objects.get(path=page.path)
        self.parent.tree.ic(page.item, 0)
        self.parent.toggle(1)

    def chi(self):
        icon = QFileDialog.getOpenFileName(self, 'Open file', os.path.expanduser('~'))
        self.icon.setPixmap(QPixmap(icon))
        self.iconpath = icon


class Editor(WinterEditor):
    def onSave(self):
        title = '%s [%s]' % (self.panel.parent.config.info.title, self.panel.tree.currentPage.title)
        self.panel.parent.setWindowTitle(title)
        self.parent.statusBar.showMessage('%s saved' % self.panel.tree.currentPage.title)


class View(EtherWebView):
    def __init__(self, parent=None):
        EtherWebView.__init__(self, inspect=True)
        self.parent = parent


    def refresh(self):
        # out = StringIO()
        # compiler.Compiler(StringIO(str(self.parent.editor.text())), out).compile()
        out = mako.template.Template(self.parent.editor.text(),
            preprocessor=haml.preprocessor
        )
        static = 'file://' + self.api.CWD + 'templates/static'
        path = 'file://' + self.parent.tree.currentPage.path
        content = out.render(static=static, path=path)

        if hasattr(self.parent.tree.currentPage, 'config') and hasattr(self.parent.tree.currentPage.config, 'template'):
            tpl = self.parent.tree.currentPage.config.template
        else:
            tpl = API().config.options.app.default_template
        with open(self.api.CWD + 'templates/html/%s' % tpl) as f:
            page = Template(f.read()).substitute(static=static, content=content, path=path)

        # enc = BeautifulSoup(page).originalEncoding
        # if enc is None:
        #     enc = 'utf8'
        #
        # content = page.decode(enc)
        #
        # if enc == 'ISO-8859-2':
        #     content = page.decode('cp1251')
        #
        self.setHtml(content)
        self.js('reloadStylesheets()')


class Panel(QStackedWidget):
    def __init__(self, parent=None):
        self.parent = parent
        QStackedWidget.__init__(self)
        self.view = View(self)
        self.api = API()

        self.editor = Editor(self.parent, self.api.CWD + "organizer/__page.text")
        self.editor.editor.textChanged.connect(self.pageChanged)
        self.editor.panel = self
        #            self.editor.editor.setCompleter()

        s = CustomStyle
        font = self.api.config.options.qsci.font
        font_size = self.api.config.options.qsci.font_size
        styles = [s('Default', '.*', self.parent.config.options.qsci.fg_color, font),
                  s('Numbers', '(\d+)', '#e33100', font, font_size),
                  s('Tag', '(\%\w+)', '#3366cc', font, font_size, bold=True),
                  s('Class', '\.([\w]+)', '#9c3', font, font_size, bold=True, offset=1),
                  s('Id', '\#([\w]+)', '#e33100', font, font_size, bold=True, offset=1),
                  s('Html', '(<.*?>)', '#3366cc', font, font_size, bold=True),
                  s('Variable', '(\$\w+)', 'violet', font, font_size, bold=True),
                  s('URL',
                      '((http|https|ftp):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)',
                      'darkcyan', font, font_size, italic=True),
                  s('Attrs', '(\{.*\})', 'darkgreen', font, font_size, bold=True),
                  s('DQuotes', '\"(.*?)\"', '#e33100', font, font_size, italic=True, offset=1),
                  s('SQuotes', '\'(.*?)\'', '#e33100', font, font_size, italic=True, offset=1),


                  s('Punct', '([\.#\'\"])', '#c93', font, font_size, bold=True),
                  s('Comment', '(-#.*$)', '#8c8c8c', font, font_size, italic=True),
                  ]

        lexer = CustomLexer(self.editor, styles)
        self.editor.editor.setLexer(lexer)
        self.addWidget(self.editor)

        self.view.setHtml('Something wrong=(')
        self.addWidget(self.view)

        Atoggle = QAction('Toggle', self)
        Atoggle.setShortcut('F4')
        Atoggle.triggered.connect(self._toggle)
        self.addAction(Atoggle)

    def pageChanged(self):
        title = '%s [%s]*' % (self.api.config.info.title, self.tree.currentPage.title)
        self.parent.setWindowTitle(title)

    def toggle(self, ind):
        self.setCurrentIndex(ind)
        self.view.refresh()
        self.widget(ind).setFocus()

    def _toggle(self):
        ind = [1, 0][self.currentIndex()]
        self.toggle(ind)


    def newPage(self, *args):
        if not args:
            SBAction.objects.get(title='New').forceShowWidget()
        else:
            self.tree.newPage(args[0], self.tree.root)


class CommandLine(WinterLine):
    def __init__(self, parent):
        self.parent = parent
        WinterLine.__init__(self, parent.parent, 'Input command:')
        self.commands = {'tree': SBAction.objects.get(title='Content').forceShowWidget, 'new': self.parent.newPage,
                         'del': self.parent.tree.delPage, 'crypt': self.parent.tree.crypt,
                         'decrypt': self.parent.tree.decrypt, 'edit': SBAction.objects.get(title='Edit').forceShowWidget
            , 'ins': lambda *x: self.parent.tree.newPage(x, self.parent.tree.currentPage.path),
                         'view': self.parent.tree.viewPage}

        cc = [':%s' % c for c in self.commands]
        for page in Page.objects.all():
            cc.append(':view %s' % page.title)
        self.setComplete(cc)
        self.lineEditCompleter.setCompletionMode(QCompleter.InlineCompletion)

        self.api = API()

    def shortcut(self, text):
        self.setText(text)
        self.setFocus()


    def checkLine(self):
        ln = str(self.text()).split(' ')[0]
        if ln[1:] in self.commands:
            return True
        return False

    def _command(self):
        ln = str(self.text()).split(' ')
        try:
            self.commands[ln[0][1:]](*ln[1:])
            self.clear()
            self.setStyleSheet('')
        except KeyError:
            self.api.error('No such command')

#            except TypeError:
#                self.api.error('Incorrect number of arguments')
#            except Exception, e:
#                self.api.error(e)

#       Break autocomplete=(
#        def focusInEvent(self,event):
##            if not str(self.text()).startswith(':'):
##                self.setText(':%s' % self.text())
#            self._newchar()
#            event.accept()
#
#        def focusOutEvent(self,event):
#            self.setStyleSheet('QWidget{ color: #444; font-style: italic;}')
#            event.accept()


class CssPanel(FocusProxy):
    def __init__(self, parent, panel):
        self.parent = parent
        self.panel = panel
        filename = panel.tree.currentPage.path + '/__page.css'
        self.editor = WinterEditor(parent, filename, lexer='CSS')
        self.editor.onSave = lambda: self.onSave()
        self.editor.tb.hide()
        #            self.editor.editor.setLexer()
        FocusProxy.__init__(self, self.editor)
        l = QVBoxLayout()
        l.addWidget(self.editor)
        self.setLayout(l)

    def onShow(self):
        self.editor.open(self.panel.tree.currentPage.path + '/__page.css')

    def onSave(self):
        self.parent.statusBar.showMessage('Style for %s saved' % self.panel.tree.currentPage.title)
        self.panel.view.js('reloadStylesheets()')
