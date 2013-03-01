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
from winterstone.extraQt import WinterEditor, CustomLexer, CustomStyle
from winterstone.terminal import WinterTerminal, WinterTermManager

from PyQt4.QtWebKit import QWebView, QWebPage, QWebSettings

import json
import re
import pyparsing as p

import paramiko as ssh

__author__ = 'averrin'

#TODO: fix syntax highlighter crashes

#TODO: move this classes to core

class JSONLexer(CustomLexer):                          #TODO: do not highlight some collections. How? i dont know
    def __init__(self, parent, editor):
        self.api = parent.api
        self.parent = parent
        s = CustomStyle
        font = self.parent.config.options.qsci.font
#        font = 'Sans'
        font_size = self.parent.config.options.qsci.font_size
        styles = [  #TODO: make theme configurable
            s('Default', p.Word(p.alphas), self.parent.config.options.qsci.fg_color, font),
            s('nums', p.Word(p.nums), 'orange', font, font_size, bold=True),
            s('punct', p.Word('[]:,'), '#aaa', font, font_size, bold=True),
            s('qutes', p.Word('"'), '#555', font, font_size, bold=True),
            s('true', p.Keyword('true'), 'green', font, font_size, bold=True),
            s('false', p.Keyword('false'), 'red', font, font_size, bold=True),
            s('alphas', p.QuotedString('"', multiline=True, escChar ='\\'), '#629755', font, font_size, bold=True, offset=1),
            s('Key', p.QuotedString('"')+":", '#6C9ADC', font, font_size, offset=1, bold=True),
        ]
        CustomLexer.__init__(self, editor, styles)


class Editor(WinterEditor):
    
    def __init__(self, parent, **kwargs):
        self.parent = parent
        WinterEditor.__init__(self, parent, **kwargs)
        self.setLexer(JSONLexer(self.parent, self))
    
    def unN(self, text):
        result = text
        if self.allow_br:
            chunks = re.split(r'("(?:[^"\\]|\\.)*")', text)
            result = chunks[0]
            for i in range(1, len(chunks), 2):
                result += \
                    re.sub(r'\t', r'    ', 
                        re.sub(r'\r?\n', r'\\n', 
                            chunks[i]
                        )
                    )\
                    + chunks[i + 1]
        return result

    def save(self):
        try:
            text = self.unN(self.editor.text())
            
            if self.checkErrors():
                content = json.loads(text, encoding='utf8')
                self.parent.pb.setVisible(True)
                self.parent.core.saveCollection(self.collection, content, self.onSave)

        except Exception as e:
            self.api.error(e)
            self.parent.statusBar.showMessage('Saving unsuccessfully')

    def onSave(self):
        self.parent.statusBar.showMessage('%s saved' % self.collection)
        self.parent.core.fillList()

    def checkErrors(self):                #TODO:  correct error locating 
        text = self.unN(self.editor.text())
        if text:
            self.editor.clearAnnotations()
            try:
                json.loads(text)
                self.parent.statusBar.showMessage('Json valid')
                return True
            except ValueError as e:
                err = str(e)

                l = re.search('line (\d+)', err)
                if l is not None:
                    line = int(l.group(1)) - 1
                else:
                    line = 0
                self.editor.annotate(line, err, self.errLine)

                self.parent.statusBar.showMessage('Json error: %s' % err)
                return False
            
    def setText(self, content):
        if self.allow_br:
            content = '\n'.join(content.split("\\n"))
        WinterEditor.setText(self, content)
        
    def _afterAppInit(self):
        self.allow_br = False
        self.setCaretForegroundColor(QColor('#eee'))
        #        self.editor.editor.setCaretLineBackgroundColor(QColor('#4f4f4f'))         #TODO: to settings
        #        self.editor.editor.setCaretLineVisible(True)
        WinterEditor._afterAppInit(self)
        ak = self.api.ex('createAction')('circle-plus', 'Add key', self.addKey, keyseq=QKeySequence.New)
        self.tb_2.addAction(ak)
        
    def addKey(self):    #TODO: not very good idea=(
        line, pos = self.getCursorPosition()
        off = 0
        last_line = self.editor.text(line)
        while not last_line.strip(' \t\r\n'):
            last_line = self.editor.text(line-off)
            off += 1

        off = 1
        next_line = self.editor.text(line+off)
        while not next_line.strip(' \t\r\n'):
            next_line = self.editor.text(line+off)
            off += 1

        off = 1
        next_brace = self.editor.text(line+off)
        while not (next_brace.startswith(']') or next_brace.startswith('}')):
            next_brace = self.editor.text(line+off).strip(' \t\r\n')
            off += 1
        
        last_line = last_line.rstrip(' \t\r\n')
        next_line = next_line.lstrip(' \t\r\n')
#        print(last_line, next_line, next_brace)
        if next_brace.startswith(']'):
            k = '"value"'
        else:
            k = '"key":"value"'
        if not last_line.endswith(',') and last_line not in ['[', '{']:
            k = ', ' + k           
        if not (next_line.startswith(']') or next_line.startswith('}')):
            k += ','
            
        if (last_line.endswith(']') or last_line.endswith('}')) and (next_line.startswith(']') or next_line.startswith('}')):
            k = ', {\n\t"key":"value"\n}'
            
        self.insertAt(k, line, pos)
        self.setCursorPosition(line, pos + len(k))
            
            

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
