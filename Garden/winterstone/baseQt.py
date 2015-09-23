# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import json
import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

try:
    import dbus
    DBUS_SUPPORT = True
except:
    DBUS_SUPPORT = False
from winterstone.base import WinterApp, WinterAPI, WinterObject, Borg
from winterstone.winterBug import *
from winterstone.extraQt import *
from winterstone.extraQt import WinterSideBar
#from snowflake import *
import functools
import logging
import time

logging.basicConfig(format='[%(asctime)s] %(levelname)s:\t\t%(message)s', filename='winter.log', level=logging.DEBUG,
    datefmt='%d.%m %H:%M:%S')
logging.info('======')

try:
    from PyKDE4.kdeui import *

    KDE_SUPPORT = True
except ImportError:
    KDE_SUPPORT = False
    print('WARNING: KDE_SUPPORT disabled')


class WinterWorker(QThread, WinterObject):
    done = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, job):
        QThread.__init__(self)
        WinterObject.__init__(self)
        self.job = job

    def run(self):
        try:
            ret = self.job()
            self.done.emit(ret)
        except Exception as e:
            print(e)
            self.error.emit(e)



class API(WinterAPI):
    def echo(self, *args, **kwargs):
        self.ex('echo')(*args, **kwargs)

    def info(self, *args, **kwargs):
        if self.debugger:
            self.debugger.info(*args, **kwargs)
        else:
            self.echo(*args, **kwargs)
        logging.info(*args)

    def debug(self, *args, **kwargs):
        if self.debugger:
            self.debugger.debug(*args, **kwargs)
        else:
            self.echo(*args, **kwargs)
        logging.debug(*args)

    def error(self, *args, **kwargs):
        if self.debugger:
            self.debugger.error(*args, **kwargs)
        else:
            self.echo(*args, **kwargs)
        logging.error(*args)

    def showMessage(self, *args, **kwargs):
        if hasattr(self, 'statusBar'):
            self.statusBar.showMessage(*args, **kwargs)
        else:
            self.echo(*args, **kwargs)

    def setProgress(self, action, *args, **kwargs):
        SBAction.objects.get(title=action).setProgress(*args, **kwargs)

    def setEmblem(self, action, *args, **kwargs):
        SBAction.objects.get(title=action).setEmblem(*args, **kwargs)

    def setBadge(self, action, *args, **kwargs):
        SBAction.objects.get(title=action).setBadge(*args, **kwargs)

    def delBadge(self, action):
        SBAction.objects.get(title=action).reset()

    def delEmblem(self, action):
        SBAction.objects.get(title=action).reset()

    def flashAction(self, action, *args, **kwargs):
        SBAction.objects.get(title=action).flash(*args, **kwargs)

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


class WinterPainter(object):
    pass


class WinterAction(QAction, WinterObject):
    def __init__(self, *args, **kwargs):
        QAction.__init__(self, *args)
        WinterObject.__init__(self)
        self.title = self.text()
        self.api = API()
        if 'icon' in kwargs:
            icon = kwargs['icon']
            self.orig_icon = QIcon(self.api.icons[icon])
            self.setIcon(QIcon.fromTheme(icon, QIcon(self.api.icons[icon])))
        if isinstance(args[0], QIcon):
            icon = args[0]
            self.orig_icon = icon
            self.setIcon(icon)


class SBAction(WinterAction):
    def __init__(self, sideBarDock, *args, **kwargs):
        self.sideBarDock = sideBarDock
        WinterAction.__init__(self, *args, **kwargs)

    def showWidget(self):
        if self.sideBarDock.isHidden():
            self.sideBarDock.show()
        elif self.sideBarDock.stack.currentWidget() == self.widget:
            self.sideBarDock.hide()
        self.sideBarDock.stack.setCurrentWidget(self.widget)
        self.widget.setFocus()
        if hasattr(self.widget, 'onShow'):
            self.widget.onShow()

    def forceShowWidget(self):
        self.sideBarDock.show()
        self.sideBarDock.stack.setCurrentWidget(self.widget)
        self.widget.setFocus()
        if hasattr(self.widget, 'onShow'):
            self.widget.onShow()

    def setEmblem(self, emblem):
        self.reset()
        sz = API().config.options.ui.sbicon_size
        icon = self.icon().pixmap(QSize(sz+6, sz+6))
        paint = IconPainter()
        icon = paint.drawEmblem(icon, emblem)
        self.setIcon(QIcon(icon))

    def reset(self):
        self.setIcon(self.orig_icon)

    def setAlpha(self, alpha):
        self.reset()
        icon = self.icon().pixmap(QSize(32, 32))
        paint = IconPainter()
        icon = paint.setAlpha(icon, alpha)
        self.setIcon(QIcon(icon))

    def setBadge(self, color, text, fgcolor='white'):
        self.reset()
        text = str(text)
        sz = API().config.options.ui.sbicon_size
        icon = self.icon().pixmap(QSize(sz, sz))
        paint = IconPainter()
        icon = paint.drawBadge(icon, color, text, fgcolor)

        self.setIcon(QIcon(icon))

    def setProgress(self, value, color='#dd1111'):
        self.reset()

        sz = API().config.options.ui.sbicon_size
        icon = self.icon().pixmap(QSize(sz, sz))

        paint = IconPainter()
        icon = paint.drawProgress(icon, value, color)
        self.setIcon(QIcon(icon))

    def flash(self, ftime=0):
        self.thread = Flasher(self, ftime)
        self.thread.alpha.connect(self.setAlpha)
        self.thread.start()


class IconPainter(object):
    def drawProgress(self, icon, value, color):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        paint = QPainter()
        paint.begin(icon)
        h = icon.height()
        w = icon.width()

        paint.setPen(QColor('black'))

        paint.setBrush(QBrush(QColor('#333')))
        paint.drawRoundedRect(QRect(QPoint(4, (3 * h) / 4), QPoint(w - 4, h - 4)), 2, 2)
        paint.setBrush(QBrush(QColor(color)))
        v = (w - 4) * (int(value) / 100.)
        paint.drawRoundedRect(QRect(QPoint(4, (3 * h) / 4), QPoint(v, h - 4)), 4, 4)

        paint.end()
        return icon

    def drawBadge(self, icon, color, text, fgcolor):
        paint = QPainter()
        paint.begin(icon)
        h = icon.height()
        w = icon.width()

        paint.setPen(QColor(color).darker(150))

        linearGrad = QLinearGradient(QPointF(0, 0), QPointF(0, h))
        linearGrad.setColorAt(0, QColor(color))
        linearGrad.setColorAt(1, QColor(color).darker(200))

        paint.setBrush(QBrush(linearGrad))
        rect = QRect(w / 2 - 3, 2, w / 2 + 2, h / 3 + 2)
        paint.drawRoundedRect(rect, 2, 2)

        font = QFont('Sans')
        n = 0.8
        font.setPixelSize(int(rect.height() * n))
        fm = QFontMetrics(font)
        wi = fm.width(text[:4])
        hi = fm.height()

        while (rect.width() - wi) / 2 <= 0 or (rect.height() - hi) / 2 <= 0:
            n -= 0.1
            font.setPixelSize(int(rect.height() * n))
            fm = QFontMetrics(font)
            wi = fm.width(text[:4])
            hi = fm.height()
        paint.setFont(font)
        paint.setPen(QColor(fgcolor))
        x = rect.topLeft().x() + (rect.width() - wi) / 2
        y = rect.topLeft().y() + (rect.height() - hi) / 2
        x2 = rect.bottomRight().x() - (rect.width() - wi) / 2
        y2 = y + hi

        paint.setBrush(QBrush(QColor('white')))
        paint.drawText(QRect(QPoint(x, y), QPoint(x2, y2)), 0, text[:4])

        paint.end()
        return icon

    def drawEmblem(self, icon, emblem):
        paint = QPainter()
        paint.begin(icon)
        w = icon.width()
        light = QPixmap(API().icons['emblems/' + emblem])
        paint.drawPixmap(w / 2, -2, 22, 22, light)
        paint.end()
        return icon

    def setAlpha(self, icon, alpha):
        if alpha < 0:
            alpha = 0
        elif alpha > 255:
            alpha = 255
        alphaChannel = QPixmap(icon.width(), icon.height())
        alphaChannel.fill(QColor(alpha, alpha, alpha))
        icon.setAlphaChannel(alphaChannel)
        return icon


class Flasher(QThread):
    alpha = pyqtSignal(int)

    def __init__(self, action, ftime):
        self.ftime = ftime
        self.action = action
        QThread.__init__(self)

    def run(self):
        ftime = self.ftime
        if ftime < 0:
            ftime = 0
        for i in range(ftime):
            time.sleep(0.5)
            for a in range(5, 255, 10):
                time.sleep(0.025)
                self.alpha.emit(255 - a)
            time.sleep(0.25)
            for a in range(5, 255, 10):
                time.sleep(0.025)
                self.alpha.emit(a)


class WinterFlag(QLabel):

    clicked = pyqtSignal()

    def setIcon(self, icon, tooltip=''):
        icon = QPixmap(icon).scaled(20, 20)
        self.setPixmap(icon)
        self.setToolTip(tooltip)

    def mouseReleaseEvent(self, ev):
        self.clicked.emit()


class SettingsManager(QMainWindow):
    class myDelegate(QItemDelegate):
        def __init__(self, parent):
            QItemDelegate.__init__(self, parent)
            self.parent = parent
            self.methods = {'QLineEdit': {'set': lambda x, value: x.setText(value), 'get': lambda x: x.text()},
                            'QSpinBox': {'set': lambda x, value: x.setValue(int(value)), 'get': lambda x: x.text()},
                            'QComboBox': {'set': lambda x, value, item: x.setCurrentIndex(list(item.variants).index(value)),
                                          'get': lambda x: x.currentText()},
                            'KColorCombo': {'set': lambda x, value: x.setColor(QColor(value)), 'get': lambda x: x.color().name()},
                            'QFontComboBox': {'set': lambda x, value: x.setFont(QFont(value)), 'get': lambda x: x.currentText()},
                            'KFontComboBox': {'set': lambda x, value: x.setFont(QFont(value)), 'get': lambda x: x.currentText()},
                            'KKeySequenceWidget': {'set': lambda x, value: x.setKeySequence(QKeySequence(value)), 'get': lambda x: x.keySequence()}
                            }

        def paint(self, painter, option, index):
            value = index.model().data(index, Qt.EditRole)
            item = self.parent.items[index.row()]
            if not item.name.endswith('_color'):
                QItemDelegate.paint(self, painter, option, index)
            else:
                painter.save()
                painter.setPen(QPen(Qt.NoPen))
                painter.setBrush(QBrush(QColor(value)))
                painter.drawRect(option.rect)
                painter.setPen(QPen(Qt.black))
                if QColor(value).black() > 127:
                    painter.setPen(QPen(Qt.white))
                value = index.data(Qt.DisplayRole)
                if value:
                    text = value
                    rect = option.rect
                    rect.setLeft(3)
                    font = self.parent.font()
                    font.setFixedPitch(True)
                    font.setPointSize(self.parent.font().pointSize())
                    fm = QFontMetrics(font)
                    rect.setTop(rect.y() + (rect.height() - fm.height()) / 2)
                    if type(text) != str:
                        text = text.toString()
                    painter.drawText(rect, Qt.AlignLeft, text)

                painter.restore()

        def createEditor(self, parent, option, index):
            value = index.model().data(index, Qt.EditRole)
            item = self.parent.items[index.row()]

            try:
                value = int(value)
            except:
                pass
            if type(value) == int:
                editor = QSpinBox(parent)
                editor.setMaximum(9999)
            elif item.name.endswith('_color') and KDE_SUPPORT:
                editor = KColorCombo(parent)
            elif item.name.endswith('font') and KDE_SUPPORT:
                editor = KFontComboBox(parent)
            elif item.name.endswith('font') and KDE_SUPPORT:
                editor = QFontComboBox(parent)
            elif item.name.endswith('_shortcut') and KDE_SUPPORT:
                editor = KKeySequenceWidget(parent)
            elif type(value).__name__ != 'Mapping':  # i dont want import config.Mapping
                if hasattr(item, 'variants'):
                    editor = QComboBox(parent)
                    editor.addItems(item.variants)
                else:
                    editor = QLineEdit(parent)
            return editor

        def setEditorData(self, editor, index):
            wtype = type(editor).__name__
            value = index.model().data(index, Qt.EditRole)
            if wtype == 'QComboBox':
                item = self.parent.items[index.row()]
                self.methods[wtype]['set'](editor, value, item)
            else:
                self.methods[wtype]['set'](editor, value)

        def setModelData(self, editor, model, index):
            self.model = model
            wtype = type(editor).__name__
            value = self.methods[wtype]['get'](editor)
            model.setData(index, value, Qt.EditRole)

        def updateEditorGeometry(self, editor, option, index):
            editor.setGeometry(option.rect)

    class settingsTable(QTableWidget, WinterObject):

        def __init__(self, parent=None):
            QTableWidget.__init__(self, parent)
            WinterObject.__init__(self)

        def fill(self, main_conf, key, conf_file, parent):
            self.parent = parent
            self.parent.configs.append(self)
            self.main_conf = main_conf
            self.key = key
            self.conf_dict = main_conf
            for k in key.split('.'):
                if k:
                    self.conf_dict = self.conf_dict[k]
            self.conf_file = conf_file
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
            self.setSizePolicy(sizePolicy)
            self.setMaximumSize(QSize(16777215, 16777215))
            self.setAutoFillBackground(True)
            self.setColumnCount(2)
            self.setRowCount(0)
            item = QTableWidgetItem()
            self.setHorizontalHeaderItem(0, item)
            item = QTableWidgetItem()
            self.setHorizontalHeaderItem(1, item)
            self.horizontalHeader().setDefaultSectionSize(200)
            self.horizontalHeader().setStretchLastSection(True)
            self.verticalHeader().setStretchLastSection(False)

            self.itemChanged.connect(self.changeOption)

            self.delegate = self.parent.myDelegate(self)
            self.setItemDelegateForColumn(0, self.delegate)
            row = 0
            self.items = []
            array = self.conf_dict
            self.setIconSize(QSize(30, 30))
            for var in array:
                if not var.endswith('_desc') and not var.endswith(
                    '_hidden') and var != 'activated' and not var.endswith('_variants') and type(
                    array[var]).__name__ != 'Mapping' and not ('%s_hidden' % var in array and array['%s_hidden' % var]):
                    self.insertRow(row)
                    self.setVerticalHeaderItem(row, QTableWidgetItem(var))
                    vitem = QTableWidgetItem(str(array[var]))
                    vitem.name = var
                    self.items.append(vitem)
                    if array[var] in [True, False]:
                        vitem.setFlags(Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled))
                        check = Qt.Checked if array[var] else Qt.Unchecked
                        vitem.setCheckState(check)
                    self.setItem(row, 0, vitem)
                    if '%s_desc' % var in array:
                        desc = array['%s_desc' % var]
                    else:
                        desc = ''
                    if '%s_variants' % var in array:
                        vitem.variants = array['%s_variants' % var]
                    if var.endswith('_icon'):
                        vitem.setIcon(QIcon(API().icons[array[var]]))
                    ditem = QTableWidgetItem(desc)
                    ditem.name = 'ditem'
                    ditem.setFlags(Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled))
                    self.setItem(row, 1, ditem)
                    row += 1

        def changeOption(self, item):
            if item.checkState() == 2 or (not item.checkState() and item.text() in ['False', 'True']):
                text = 'True' if item.checkState() else 'False'
                item.setText(text)
            value = item.text().__str__().encode('cp1251')
            if item.name in self.conf_dict:
                if value in ['True', 'False']:
                    self.conf_dict[item.name] = eval(value)
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        if type(value) == list:
                            value = eval(value)
                        if item.name.endswith('_icon'):
                            self.blockSignals(True)
                            item.setIcon(QIcon(API().icons[value]))
                            self.blockSignals(False)
                    self.conf_dict[item.name] = value
                self.parent.statusBar.showMessage('%s change to %s' % (item.name, item.text()))

        def save(self):
            """
                Okey, its horrible. And executed much more times than needed.
            """
            keys = self.key.split('.')
            if len(keys) > 1:
                self.main_conf._dict[keys[0]][keys[1]] = self.conf_dict
            else:
                self.main_conf._dict[keys[0]] = self.conf_dict

            f = open(self.conf_file, 'w')
            self.main_conf.save(f)

    def addPage(self, widget, label, parent='', icon=''):
        self.stack.addWidget(widget)
        if not parent:
            item = QTreeWidgetItem([label])
            self.tree.addTopLevelItem(item)
        else:
            item = QTreeWidgetItem(parent, [label])
            parent.addChild(item)

        if icon:
            if not isinstance(icon, QIcon):
                item.setIcon(0, QIcon.fromTheme(icon, QIcon(self.app.api.icons[icon])))
            else:
                item.setIcon(0, icon)
        item.page = widget
        widget.item = item
        item.setExpanded(True)
        self.pages[widget] = item
        return widget

    def ic(self, item, column):
        self.stack.setCurrentWidget(item.page)

    def __init__(self, app, *args, **kwargs):
        QMainWindow.__init__(self)
        self.resize(900, 600)
        self.setWindowTitle('Settings Manager')

        self.centralwidget = QWidget(self)
        self.tabWidget = QTabWidget()

        self.stack = QStackedWidget()

        hb = QHBoxLayout(self.centralwidget)
        w = QWidget()
        w.setLayout(QVBoxLayout())
        self.tree = QTreeWidget(self.centralwidget)
        self.tree.setHeaderLabel('Settings')
        toolbar = QToolBar()
        self.search = QLineEdit()
        toolbar.addWidget(QLabel('Search: '))
        toolbar.addWidget(self.search)
        self.cls = QPushButton('X')
        toolbar.addWidget(self.cls)
        self.cls.setFixedWidth(30)
        self.cls.clicked.connect(self.search.clear)
        self.search.textChanged.connect(self.searchOption)
        w.layout().addWidget(toolbar)
        w.layout().addWidget(self.tree)
        hb.addWidget(w)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        hb.addLayout(self.verticalLayout)
        self.verticalLayout.addWidget(self.stack)
        hb.setStretch(1, 5)
        self.centralwidget.setLayout(hb)

        self.horizontalLayout = QHBoxLayout()
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cancelButton = QPushButton('Cancel', self.centralwidget)
        self.horizontalLayout.addWidget(self.cancelButton)
        self.restartButton = QPushButton('Apply and Restart', self.centralwidget)
        # self.restartButton.setEnabled(False)
        self.horizontalLayout.addWidget(self.restartButton)
        self.applyButton = QPushButton('Apply', self.centralwidget)
        # self.applyButton.setEnabled(False)
        self.horizontalLayout.addWidget(self.applyButton)

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        self.app = app
        self.app.sm = self
        self.configs = []
        self.pages = {}

        self.setWindowIcon(QIcon.fromTheme('configure', QIcon(self.app.api.icons['configure'])))

        self.tableWidget = self.settingsTable()
        self.tableWidget.fill(self.app.config, 'options', CWD + 'config/main.cfg', self)
        self.sttab = self.addPage(self.tableWidget, 'General', icon='configure')
        self.tables = [self.tableWidget]
        for var in self.app.config.options:
            val = self.app.config.options[var]
            if type(val).__name__ == 'Mapping':
                if not self.app.schema[var].hide:
                    st = self.settingsTable(self.tableWidget)
                    self.tables.append(st)
                    st.fill(self.app.config, 'options.%s' % var, CWD + 'config/main.cfg', self)
                    self.ui = self.addPage(st, self.app.schema[var].title, icon=QIcon(self.app.schema[var].icon),
                        parent=self.sttab.item)
        self.stack.setCurrentWidget(self.sttab)

        if self.app.config.options.debug:
            self.dbgTable = self.settingsTable(self.stack)
            self.tables.append(self.dbgTable)
            self.dbgTable.fill(self.app.debugger.config, 'options', CWD + 'config/debug.cfg', self)
            self.dbgtab = self.addPage(self.dbgTable, 'Debug', icon='warning')

        if self.app.config.options.plugins:
            self.tabPlugins = QWidget()
            self.verticalLayout = QVBoxLayout(self.tabPlugins)
            self.listWidget = QListWidget(self.tabPlugins)
            self.verticalLayout.addWidget(self.listWidget)
            self.plainTextEdit = QPlainTextEdit(self.tabPlugins)
            self.verticalLayout.addWidget(self.plainTextEdit)
            self.plugtab = self.addPage(self.tabPlugins, 'Plugins', icon='plugins')
            self.loadPlugins()
            self.listWidget.itemClicked.connect(self.echoInfo)
            self.listWidget.itemChanged.connect(self.togglePlugin)

            for plugin in self.app.pm.plugins:
#                print(plugin, plugin.active)
                if plugin.active:
                    st = self.settingsTable(self.tabPlugins)
                    self.tables.append(st)
                    st.fill(plugin.config, 'options', '%splugins/%s/plugin.cfg' % (CWD, plugin.name), self)
                    plugin.icon = QIcon(os.path.abspath(plugin.config.info.icon))
                    plugin.st = st
                    self.addPage(st, plugin.name, self.tabPlugins.item, icon=plugin.icon)

        self.restartButton.clicked.connect(self.restart)
        self.cancelButton.clicked.connect(self.close)
        self.applyButton.clicked.connect(self.applyOptions)

        self.tree.itemClicked.connect(self.ic)

    def searchOption(self):
        q = self.search.text()
        for t in self.tables:
            n = 0
            for i in t.items:
                if not re.search(str(q), i.name):
                    t.setRowHidden(i.row(), True)
                    n += 1
                else:
                    t.setRowHidden(i.row(), False)
            if n == len(t.items) and t not in [self.sttab, self.plugtab]:
                self.tree.setItemHidden(self.pages[t], True)
            else:
                self.tree.setItemHidden(self.pages[t], False)

    #TODO: make it right
    def reloadPluginSettings(self):
        for plugin in self.app.pm.plugins:
            if plugin.active:
                item = plugin.st.item
                self.stack.removeWidget(plugin.st)
                st = self.settingsTable(self.stack)
                plugin.st = st
                item.page = st
                st.fill(plugin.config, '', '%splugins/%s/plugin.cfg' % (CWD, plugin.name), self)
                self.stack.addWidget(st)
            else:
                self.tree.removeItemWidget(plugin.st.item, 0)

    def loadPlugins(self):
        for plugin in self.app.pm.plugins:
            item = QListWidgetItem(plugin.name)
            item.plugin = plugin
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

            check = Qt.Checked if plugin.active else Qt.Unchecked

            item.setCheckState(check)
            self.listWidget.addItem(item)

    def applyOptions(self):
        for table in self.settingsTable.objects.all():
            table.save()
        self.savePlugins()
        self.close()

    def restart(self):
        self.applyOptions()
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def echoInfo(self, item):
        info = self.getInfo(item.plugin)
        self.plainTextEdit.setPlainText(info)

    def togglePlugin(self, item):
        state = item.checkState()
        if state:
            self.app.pm.activate(item.plugin)
        else:
            self.app.pm.deactivate(item.plugin)

        check = Qt.Checked if item.plugin.active else Qt.Unchecked
        item.setCheckState(check)
        if check == Qt.Checked:
            self.statusBar.showMessage('%s activated' % item.plugin.name)
        else:
            self.statusBar.showMessage('%s deactivated' % item.plugin.name)
            #        self.reloadPluginSettings()

    def savePlugins(self):
        names = []
        if self.app.config.options.plugins:
            for plugin in self.app.pm.plugins:
                names.append(plugin.name)
        self.app.p_config.plugins.active = names
        print(self.app.p_config)
        cfgfile = open(CWD + 'config/plugins.cfg', 'w')
        self.app.p_config.save(cfgfile)

    def getInfo(self, pi):
        return '''Name: %s
Description: %s
Author: %s
Version: %s
State: %s
        ''' % (pi.name, pi.config.info.description, pi.config.info.author, pi.config.info.version, pi.state)


class WinterScript(object):
    def __init__(self, app):
        self.app = app
        self.api = API()
        self.objects = {'api': self.api, 'script': self}
        if not self.app.config.options.script_safe:
            self.objects['app'] = self.app
        self.aliases = {'set': '__setattr__'}

    def executeFile(self, filename, raw=False):
        f = open(filename, 'r')
        for line in f:
            if line.strip() and not line.startswith('#'):
                line = line.lstrip().rstrip()
                if not raw:
                    self.executeLine(line)
                else:
                    self.executeRaw(line)

    def executeRaw(self, line):
        words = line.split(' ')
        self.executeLine('{"command":"%s","args":%s}' % (words[0], str(words[1:])))

    def executeLine(self, line):
        if self.app.config.options.script_engine:
            line = json.loads(line.replace("'", '"'), 'utf8')
            try:
                name, method = line['command'].split('.')
            except ValueError:
                name = None
                method = line['command']
            if name is None:
                object = self.objects['app']
            else:
                object = self.objects[name]

            for i, arg in enumerate(line['args']):
                try:
                    line['args'][i] = arg.strip()
                except:
                    pass
                try:
                    line['args'][i] = int(arg)
                except ValueError:
                    pass

            if method in self.aliases:
                method = self.aliases[method]

            try:
                method = object.__getattribute__(method)
                try:
                    if not 'keys' in line:
                        method(*line['args'])
                    else:
                        self.app.createAction('', line['command'], lambda: method(*line['args']), keyseq=line['keys'])
                except Exception as e:
                    self.api.error(e)
            except AttributeError as e:
                self.api.error(e)

    def addObject(self, name, object):
        self.objects[name] = object


class WinterQtApp(QMainWindow, WinterApp, QObject):
    __apiclass__ = API

    def __init__(self, app):
        QMainWindow.__init__(self)
        self.setObjectName('MainWindow')
        try:
            for font in os.listdir(CWD + 'fonts'):
                try:
                    QFontDatabase.addApplicationFont(CWD + 'fonts/' + font)
                except Exception as e:
                    print(e)
        except OSError:
            pass

        self.workers_pool = []

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)

        self.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        self.toolBar = QToolBar(self)
        self.toolBar.setObjectName('toolBar')

        self._afterMWInit()
        WinterApp.__init__(self)

        self.api.toolBar = self.toolBar
        self.api.statusBar = self.statusBar
        self.api.dialog = self.dialog
        self.api.notify = self.notify

        if os.path.isfile(VAULT + 'themes/%s/style.css' % self.config.options.ui.theme):
            self.setStyleSheet(open(VAULT + 'themes/%s/style.css' % self.config.options.ui.theme, 'r').read())

        if os.path.isfile(CWD + 'themes/%s/style.css' % self.config.options.ui.theme):
            self.setStyleSheet(open(CWD + 'themes/%s/style.css' % self.config.options.ui.theme, 'r').read())

        theme_variants = ['system']
        if os.path.isdir(CWD + 'themes/'):
            for d in os.listdir(CWD + 'themes/'):
                theme_variants.append(d)
        if os.path.isdir(VAULT + 'themes/'):
            for d in os.listdir(VAULT + 'themes/'):
                theme_variants.append(d)
        self.config.options.ui.theme_variants = list(set(theme_variants))

        self.sideBar = WinterSideBar(self)
        self.statusBar.addPermanentWidget(QWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        self._afterAppInit()
        if self.config.options.debug:
            self.debugger = WinterQtDebug(self)
            self.api.debugger = self.debugger
            self.createAction('warning', self.tr('Debugger'), 'toggleDebug',
                keyseq=QKeySequence(self.debugger.config.options.debug_shortcut), toolbar=True)
            self.flag = WinterFlag()
            self.flag.setIcon(self.api.icons['green'],
                self.tr('Toggle debug panel: %s' % self.debugger.config.options.debug_shortcut))
            self.flag.clicked.connect(self.toggleDebug)
            self.statusBar.addPermanentWidget(self.flag)
            self.api.setFlag = self.flag.setIcon

        screen = QDesktopWidget().screenGeometry()
        QMainWindow.setGeometry(self, 0, 0, screen.width(), screen.height())

        self.setWindowTitle(self.config.info['title'])
        self.setWindowIcon(QIcon(self.api.icons['app']))

        if hasattr(WinterEditor, 'objects'):
            for we in WinterEditor.objects.all():
                we._afterAppInit()

        # self.statusBar.showMessage('Done. Switch modes: F4')
        if self.config.options.plugins:
            self.pm.activateAll()
            self.api.info(self.tr('Plugins initialised'))

        self.sm = SettingsManager(self)
        self.createAction('configure', self.tr('Settings'), self.sm.show, keyseq=QKeySequence('Ctrl+P'), toolbar=True)
        self.smflag = WinterFlag()
        self.smflag.setIcon(self.api.icons['configure'], self.tr('Options: Ctrl+P'))
        self.smflag.clicked.connect(self.sm.show)
        self.statusBar.addPermanentWidget(self.smflag)
        self.api.info('Application initialised')

        self.createAction('about', self.tr('About'), 'about', keyseq=QKeySequence.HelpContents, toolbar=True)

        self.addToolBar(Qt.TopToolBarArea, self.toolBar)
        if not self.config.options.ui.tb_show:
            self.toolBar.hide()

        self.qs = QSettings('Winterstone', self.config.info.title)
        #        self.restoreGeometry(self.qs.value("geometry").toByteArray())
        #todo: fix
        #        self.restoreState(self.qs.value("windowState").toByteArray())

        self.signalMapper = QSignalMapper(self)

        self.toolBar.setIconSize(
            QSize(self.config.options.ui.tbicon_size, self.config.options.ui.tbicon_size))
        self.toolBar.setMovable(self.config.options.ui.tb_movable)
        self.resize(self.config.options.ui.width, self.config.options.ui.height)
        self.api.sm = self.sm

        self.config.add(self)

        scriptfiles = ['init.ws', 'hotkeys.ws']

        for fname in scriptfiles:
            path = self.api.CWD + 'scripts/' + fname
            if os.path.isfile(path):
                self.script.executeFile(path)

    def async(self, job, callback, error_callback=None):
        w = WinterWorker(job)
        self.workers_pool.append(w)
        w.done.connect(callback)
        if error_callback is not None:
            w.error.connect(error_callback)
        w.start()

    def on_tb_show(self, value):
        if value:
            self.toolBar.show()
        else:
            self.toolBar.hide()

    def on_tbicon_size(self, value):
        self.toolBar.setIconSize(QSize(value, value))

    def on_tb_movable(self, value):
        self.toolBar.setMovable(value)

    def on_sbicon_size(self, value):
        self.sideBar.setIconSize(QSize(value, value))

    def on_sb_movable(self, value):
        self.sideBar.setMovable(value)

    def on_height(self, value):
        self.resize(self.config.options.ui.width, value)

    def on_width(self, value):
        self.resize(value, self.config.options.ui.height)

    def setMainWidget(self, widget):
#        print '!!!!!!!!!!!!!!'
        if hasattr(self, 'mainWidget'):
            self.mainWidget.hide()
            del self.mainWidget
        self.mainWidget = widget
        self.mainWidget.api = self.api
        self.api.mainWidget = self.mainWidget
#        self.setLayout(QHBoxLayout())
#        self.layout().addWidget(self.mainWidget)
        self.horizontalLayout_2.addWidget(self.mainWidget)
        self.horizontalLayout_2.setStretch(0, 3)

    def createSBAction(self, icon, name, widget, keyseq='', toolbar=False):
        if type(icon).__name__ != 'QIcon':
            icon = QIcon.fromTheme(icon, QIcon(self.api.icons[icon]))
        action = SBAction(self.sideBar.dock, icon, name, self)
        action.widget = widget
        self.sideBar.stack.addWidget(widget)
        action.triggered.connect(functools.partial(action.showWidget))
        if keyseq:
            action.setShortcut(keyseq)
        if toolbar:
            self.sideBar.addAction(action)
        self.addAction(action)
        return action

    def showSideBar(self, widget):
        print(widget)

    def createAction(self, icon, name, method, module='main', keyseq='', toolbar=False):
        if not isinstance(icon, QIcon) and icon:
            icon = QIcon.fromTheme(icon, QIcon(self.api.icons[icon]))
        elif not icon:
            icon = QIcon()
        action = WinterAction(icon, name, self)
        if keyseq:
            if not isinstance(keyseq, QKeySequence):
                keyseq = QKeySequence(keyseq)
            action.setShortcut(keyseq)
        if isinstance(method, str):
            method = self.getMethod(method, module)
        action.triggered.connect(method)
        if toolbar:
            self.toolBar.addAction(action)
        self.addAction(action)
        return action

    def about(self):
        self.dialog('about', 'About %s (%s)' % (self.config.info.title, self.config.info.version),
            getFileContent(CWD + 'ABOUT'))

    def input(self, title='Input dialog', text='Please input'):
        inputline = ''
        inputline = QInputDialog.getText(self, title, text)
        self['debug']('input value: %s' % inputline[0])
        return inputline[0]

    def dialog(self, type='info', title='Dialog', text='oops!!'):
        if type == 'info':
            QMessageBox.information(self, title, text)
        elif type == 'warning':
            QMessageBox.warning(self, title, text)
        elif type == 'critical':
            QMessageBox.critical(self, title, text)
        elif type == 'about':
            QMessageBox.about(self, title, text)

    def toggleDebug(self):
        if self.debugger.isHidden():
            self.debugger.show()
        else:
            self.debugger.hide()

    def _afterMWInit(self):
        pass

    def _afterAppInit(self):
        pass

    def info(self, *args, **kwargs):
        self.api.info(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.api.error(*args, **kwargs)

    def debug(self, *args, **kwargs):
        self.api.debug(*args, **kwargs)

    def echo(self, *args, **kwargs):
        self.dialog(title='Echo', text=args[0])

    #    @try_this(API())
    def getMethod(self, key, module='main'):
        return WinterApp.getMethod(self, key, module)

    def closeEvent(self, event):
        self.qs.setValue("geometry", self.saveGeometry())
        self.qs.setValue("windowState", self.saveState())
        event.accept()

    def notify(self, title, body):
        if DBUS_SUPPORT and self.config.options.notification:
            knotify = dbus.SessionBus().get_object("org.kde.knotify", "/Notify")
            knotify.event('warning', 'inkmoth', [], title, body, [], [], 0, 0, dbus_interface="org.kde.KNotify")

    def setTitle(self, msg):
        self.setWindowTitle('%s [%s]' % (self.config.info.title, msg))

    def exit(self):
        exit()

    def beforeCore(self):
        self.script = WinterScript(self)
        self.api.script = self.script

from winterstone import snowflake


def load():
    filename = QFileDialog.getOpenFileName(None, "Load map", CWD, "Map files (*.svg)")
    if len(filename):
        obj = snowflake.load(filename)
        return obj
    else:
        return False


def save(obj):
    filename = QFileDialog.getSaveFileName(None, "Save map", CWD, "Map files (*.svg)")
    if len(filename):
        return snowflake.save(obj, filename)
    else:
        return False


class WinterPool(Borg, list):
    _shared_state = {}

    def __init__(self):
        Borg.__init__(self)

    def append(self, worker):
        QThreadPool.globalInstance().start(worker)
        list.append(self, worker)

    def remove(self, worker):
        list.remove(self, worker)
        worker._stop()

WINTERPOOL = WinterPool()


class WinterRunnable(WinterObject, QRunnable):
    class emmiterClass(QObject):
        shot = pyqtSignal()
        firstShot = pyqtSignal()
        lastShot = pyqtSignal()
        stop = pyqtSignal()

    def __init__(self, every, total=0, **kwargs):
        WinterObject.__init__(self, **kwargs)
        QRunnable.__init__(self)
        self.emmiter = self.emmiterClass()
        self.setAutoDelete(False)
        self.timer = QTimer()
        self.timer.timeout.connect(self._shot)
        self.every = every
        self.total = total
        self.sum = 0

        self.first = True

    def firstShot(self):
        self.emmiter.firstShot.emit()

    def lastShot(self):
        self.emmiter.lastShot.emit()

    def run(self):
        if self.first:
            self.first = False
            self.firstShot()
        self.timer.start(self.every)

    def _shot(self):
        self.shot()
        self.sum += self.every
        print(self.sum, self.every, self.total)
        if self.total and self.sum > (self.total - self.every):
            self.lastShot()
            self.timer.stop()

    def shot(self):
        self.emmiter.shot.emit()

    def _stop(self):
        self.timer.stop()
        self.emmiter.stop.emit()

    def stop(self):
        pass
