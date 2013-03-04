# -*- coding: utf-8 -*-
import json
import mimetypes
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.snowflake import getFileContent, CWD
from winterstone.base import WinterObject
#import regex as re
import sys

try:
    from PyQt4.Qsci import *

    QSCI_SUPPORT = True
except ImportError:
    QSCI_SUPPORT = False
    print('WARNING: QSCI_SUPPORT disabled')


class FocusProxy(QWidget):
    def __init__(self, focused=''):
        QWidget.__init__(self)
        self.focused = focused

    def focusInEvent(self, event):
        if self.focused:
            self.focused.setFocus()


class WinterLine(QLineEdit):
    def __init__(self, parent='', placeholder=''):
        QLineEdit.__init__(self)
        self.textChanged.connect(self._newchar)
        self.returnPressed.connect(self._command)

        self.hist_a = []
        self.hist_b = []

        self.correct = '#009600'
        self.error = '#8c0000'
        if parent:
            self.api = parent.api

            p = QPalette(QColor(self.api.config.options.ui.input_fg_color),
                QColor(self.api.config.options.ui.input_bg_color))
            self.setPalette(p)
            self.correct = self.api.config.options.ui.input_correct_color
            self.error = self.api.config.options.ui.input_error_color
            self.api.config.add(self)

        self.setPlaceholderText(placeholder)

    def onSubsChange(self, key, value):
        if key in ['input_fg_color', 'input_bg_color', 'input_correct_color', 'input_error_color']:
            p = QPalette(QColor(self.api.config.options.ui.input_fg_color),
                QColor(self.api.config.options.ui.input_bg_color))
            self.setPalette(p)
            self.correct = self.api.config.options.ui.input_correct_color
            self.error = self.api.config.options.ui.input_error_color

    def setComplete(self, array):
        self.completerList = []
        for line in array:
            self.completerList.append(QString(line))
        self.lineEditCompleter = QCompleter(self.completerList)
        self.lineEditCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.lineEditCompleter)

    def _command(self):
        pass

    def _newchar(self):
    #        ln = re.findall('[^ ]*', str(self.text().toUtf8()))[0]
        if self.checkLine():
            self.color = QColor(self.correct)
            self.decor = 'underline'
            self.dlock = False
        else:
            self.color = QColor(self.error)
            self.decor = 'none'
            self.dlock = True
        self.setStyleSheet(
            "QWidget { font: bold; color: %s; text-decoration: %s;}" % (self.color.name(), self.decor))
        self.onChange()

    def checkLine(self):
        return True

    def onChange(self):
        pass

    def _back(self):
        pass

    def keyPressEvent(self, event):
        if event.key() == 16777216:
            self.clear()
        elif event.key() in [16777235]:
            if str(self.text()):
                self.hist_b.append(str(self.text()))
                self.hist_b = list(set(self.hist_b))
            if self.hist_a:
                self.setText(str(self.hist_a.pop()))
        elif event.key() in [16777237]:
            if str(self.text()):
                self.hist_a.append(str(self.text()))
                self.hist_a = list(set(self.hist_a))
            if self.hist_b:
                self.setText(str(self.hist_b.pop()))
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            self._back()
        else:
            QLineEdit.keyPressEvent(self, event)


class WinterSearch(WinterLine):
    def __init__(self, container):
        WinterLine.__init__(self)
        self.container = container

    def checkLine(self):
        return self.container.WFind(self.text())

    def _command(self):
        self.container.WFindNext()

    def _back(self):
        self.container.WFindPrev()


class WinterEditor(FocusProxy, WinterObject):
    def __init__(self, parent, filename='', lexer='', autosave=True):
        FocusProxy.__init__(self)
        WinterObject.__init__(self)
        self.QSCI_SUPPORT = QSCI_SUPPORT
        self.parent = parent
        self.autosave = autosave
        try:
            self.api = parent.API()
        except AttributeError:
            from .baseQt import API

            self.api = API()
        self.filename = filename
        lay = QVBoxLayout()
        self.tb = QToolBar(self)
        lay.addWidget(self.tb)
        #TODO: toolbar-manager


        self.tb_save = QToolButton()
        #        self.tb_save.setIcon(QIcon.fromTheme('document-save', QIcon(self.api.icons['filesave'])))
        #        self.connect(self.tb_save, SIGNAL("clicked()"), self.save)
        #        self.tb.addWidget(self.tb_save)

        if QSCI_SUPPORT:
            self.errLine = QsciStyle(-1, 'Red', QColor('white'), QColor('red'), QFont('Sans'))
            editor = QsciScintilla(self)
            editor.setUtf8(True)
            self.lexers = {'Bash': QsciLexerBash, 'Batch': QsciLexerBatch, 'CMake': QsciLexerCMake, 'CPP': QsciLexerCPP,
                           'CSS': QsciLexerCSS, 'D': QsciLexerD, 'Diff': QsciLexerDiff, 'Fortran': QsciLexerFortran77, 'JavaScript': QsciLexerJavaScript,
                           'HTML': QsciLexerHTML, 'Lua': QsciLexerLua, 'Make': QsciLexerMakefile,
                           'Pascal': QsciLexerPascal,
                           'Perl': QsciLexerPerl, 'PostScript': QsciLexerPostScript, 'POV': QsciLexerPOV,
                           'Properties': QsciLexerProperties, 'Python': QsciLexerPython, 'Ruby': QsciLexerRuby,
                           'SQL': QsciLexerSQL, 'TCL': QsciLexerTCL, 'TeX': QsciLexerTeX,
                           'VHDL': QsciLexerVHDL, 'YAML': QsciLexerYAML, 'Plain': QsciLexerPython}

            if lexer:
                if isinstance(lexer, CustomLexer):
                    lex = lexer
                else:
                    lex = self.lexers[lexer]()
                editor.setLexer(lex)
                lex.setPaper(QColor(self.parent.config.options.qsci.bg_color))

            editor.resetSelectionBackgroundColor()
            editor.resetSelectionForegroundColor()
            editor.setCaretLineBackgroundColor(QColor(self.parent.config.options.qsci.caretline_color))
            editor.setMarginsBackgroundColor(QColor(self.parent.config.options.qsci.margins_bg_color))
            editor.setMarginsForegroundColor(QColor(self.parent.config.options.qsci.margins_fg_color))
            editor.setFoldMarginColors(QColor(self.parent.config.options.qsci.foldmargin_prim_color),
                QColor(self.parent.config.options.qsci.foldmargin_sec_color))
            editor.setSelectionBackgroundColor(QColor(self.parent.config.options.qsci.selection_bg_color))
            editor.setSelectionForegroundColor(QColor(self.parent.config.options.qsci.selection_fg_color))
            editor.setFolding(self.parent.config.options.qsci.folding)
            editor.setPaper(QColor(self.parent.config.options.qsci.bg_color))
            editor.setColor(QColor(self.parent.config.options.qsci.fg_color))

            editor.setCaretForegroundColor(QColor(self.parent.config.options.qsci.caret_fg_color))
            editor.setCaretLineBackgroundColor(QColor(self.parent.config.options.qsci.caretline_bg_color))
            editor.setCaretLineVisible(self.parent.config.options.qsci.caret_visible)

            font = QFont()
            font.setFamily(self.parent.config.options.qsci.font)
            font.setFixedPitch(True)
            font.setPointSize(self.parent.config.options.qsci.font_size)
            fm = QFontMetrics(font)
            editor.setFont(font)
            if self.parent.config.options.qsci.linenumbers:
                editor.setMarginsFont(font)
                editor.setMarginWidth(0, fm.width("000") + 5)
                editor.setMarginLineNumbers(0, True)
            if self.parent.config.options.qsci.folding:
                editor.setFolding(QsciScintilla.BoxedTreeFoldStyle)
            editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
            editor.setCaretLineVisible(self.parent.config.options.qsci.caretline)
        else:
            editor = QTextEdit(self)

        self.editor = editor
        self.focused = editor
        lay.addWidget(editor)
        if filename:
            self.open(filename)

        self.setLayout(lay)

        if self.autosave:
            self.editor.focusOutEvent = self.focusOutEvent

    def open(self, filename):
        self.filename = filename
        try:
            self.editor.setText(getFileContent(filename))
        except IOError:
            open(filename, "w").write('')

    def focusOutEvent(self, event):
        self.save()

    def WFind(self, text):
        return self.editor.findFirst(text, False, False, False, True)

    def WFindNext(self):
        return self.editor.findNext()

    def WFindPrev(self):
        return self.editor.findPrev()

    def _afterAppInit(self):
        if QSCI_SUPPORT:
            save = self.api.ex('createAction')('document-save', 'Save', self.save, keyseq=QKeySequence.Save)
#            save.setShortcutContext(Qt.WidgetShortcut)
            self.tb.addAction(save)
            self.tb.addAction(self.api.ex('createAction')('edit-undo', 'Undo', self.editor.undo))
            self.tb.addAction(self.api.ex('createAction')('edit-redo', 'Undo', self.editor.redo))
            self.tb.addWidget(QWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
            self.tb.addWidget(QLabel('Search:  '))
            self.tb.addWidget(WinterSearch(self))

    def save(self):
        try:
            f = open(self.filename, 'w')
            f.write(self.editor.text().toUtf8())
            f.close()
            self.onSave()
        except Exception as e:
            self.api.error(e)
            self.parent.statusBar.showMessage('Saving unseccessfull')

    def onSave(self):
        self.parent.statusBar.showMessage('%s saved' % self.filename)

    def setText(self, text):
        return self.editor.setText(text)

    def __getattr__(self, item):
        try:
            return self.__getattribute__(item)
        except AttributeError as e:
            if str(item) != 'editor':
                return self.editor.__getattribute__(item)
            else:
                raise e


class CustomStyle(WinterObject):
    def __init__(self, title, pattern, color, font, font_size=10, offset=0, bold=False, italic=False):
        WinterObject.__init__(self)
        self.title = title
        self.pattern = pattern
        self.color = QColor(color)
        self.offset = offset
        self.bold = bold
        self.italic = italic
        self.font_size = font_size
        self.font = QFont(font)
        self.font.setBold(self.bold)
        self.font.setItalic(self.italic)
        self.font.setPointSize(self.font_size)

    def getColor(self):
        return self.color

    def getFont(self):
        return self.font

if QSCI_SUPPORT:
    class CustomLexer(QsciLexerCustom):            #TODO: fix syntax highlighter crashes
        def __init__(self, parent, styles):
            QsciLexerCustom.__init__(self, parent)
            self.parent = parent
            self.styles = styles

        def description(self, style):
            return ''

        def defaultColor(self, style):
            try:
                return self.styles[style].getColor()
            except:
                return self.styles[0].getColor()

        def defaultPaper(self, style):
            return QColor(self.parent.parent.config.options.qsci.bg_color)

        def defaultFont(self, style):
            try:
                return self.styles[style].getFont()
            except:
                return self.styles[0].getFont()

        def styleText(self, start, end):
#            print(start, end, self.editor().length(), len(self.editor().text()))
            editor = self.editor()
            self.start = start
#            print(self.start)
            if editor is None:
                return

            # scintilla works with encoded bytes, not decoded characters.
            # this matters if the source contains non-ascii characters and
            # a multi-byte encoding is used (e.g. utf-8)
            source = ''
            if end > editor.length():
                end = editor.length()
            if end > start:
                source = bytearray(end - start)
                editor.SendScintilla(
                    editor.SCI_GETTEXTRANGE, start, end, source)

            if not source:
                return

#            print(start, end, self.editor().length(), len(self.editor().text()), len(source))
            self.source = source.replace(b'\t', b' ').decode("utf-8")
#            print(source)
            
#            if start:
#                print(start, self.start, self.source)
            # the line index will also be needed to implement folding
            #        index = editor.SendScintilla(editor.SCI_LINEFROMPOSITION, start)
            #        if index > 0:
            #            # the previous state may be needed for multi-line styling
            #            pos = editor.SendScintilla(
            #                editor.SCI_GETLINEENDPOSITION, index - 1)
            #            state = editor.SendScintilla(editor.SCI_GETSTYLEAT, pos)
            #        else:
            #            state = self.styles[0]

            for n, style in enumerate(self.styles):
#                self.styleGroup(style.pattern, n, off=style.offset)
                self.last = 0
                self.styleNG(style.pattern, n, offset=style.offset)

                #        index += 1
                
                
        def styleNG(self, pattern, style, offset=0):
            import pyparsing as p
            self.startStyling(self.start-12, 0x1f)
            off = 0
            text = self.source
            tokens = pattern.scanString(text)
            for i, token in enumerate(tokens):
                word = token[0][0]
                o = json.dumps(word).count('\\u')
                l = len(word) + o
                start = token[1] + self.start + offset            
                before = json.dumps(text[self.last:token[2]])
                off += before.count('\\u')
                start += off - o
                    
                try:
#                    print(start, l, len(self.editor().text()), len(self.source), len(text))
                    if start < len(self.editor().text()):       #temp, but not worked
                        self.startStyling(start, 0x1f)
                        self.setStyling(l, style)
#                    print(word, "<%s>" % self.editor().text()[start:start+l])
                except Exception as e:
                    print(e)
                    
                self.last = token[2]
                
            
            
            

        def styleGroup(self, pattern, style, off=0):
            set_style = self.setStyling
            self.startStyling(self.start, 0x1f)
            offset = 0
            n = 0
            lazy = 0
#            if pattern.find('?') != -1:
#                pattern = pattern.replace('?', '')
#                lazy = 1
            rx = QRegExp(pattern)
            if lazy:
                rx.setMinimal(True)

            for line in self.source.splitlines(True):
                length = len(line)
                matches = {}
                pos = 0
                if style:
                    while rx.indexIn(str(line), pos) != -1:
#                        print(rx.capturedTexts())
                        token = rx.cap(1)
#                        print(token)
                        pos = int(rx.indexIn(str(line), pos))

                        if token in matches:
                            if type(matches[token]) is not list:
                                tmp = matches[token]
                                matches[token] = [tmp]
                            matches[token].append(rx.indexIn(str(line), pos))
                        else:
                            matches[token] = rx.indexIn(str(line), pos)
                        pos += rx.matchedLength()
                if matches:

                    for token in matches:
                        if type(matches[token]) is list:
                            for p in matches[token]:
                                p += off
                                self.startStyling(self.start + offset + p, 0x1f)
                                set_style(len(token), style)
                        else:
                            p = matches[token] + off
                            self.startStyling(self.start + offset + p, 0x1f)
                            l = len(token)
                            u = str(token).count('\\x')
                            s = str(token.replace('\\x', '')).count('\\')
                            l -= u*3
                            l -= s
                            set_style(l, style)

                offset += length
                n += 1


class WinterDirTree(QTreeWidget):
    def __init__(self, parent, root, label='', viewer='', file_filter='', name_filter=''):
        QTreeWidget.__init__(self, parent)
        self.parent = parent
        self.root = os.path.expanduser(root)
        if viewer:
            self.viewer = viewer
            viewer.tree = self
        if name_filter:
            self.nameFilter = name_filter
        if file_filter:
            self.fileFilter = file_filter
        self.setHeaderLabel(label)
        item = self.headerItem()
        item.path = self.root
        self.insertTopLevelItem(0, item)
        self.items = []
        item.setExpanded(True)
        self.expanded(item, header=True)
        self.itemExpanded.connect(self.expanded)
        self.itemClicked.connect(self.ic)
        self.itemDoubleClicked.connect(self.dic)

        self.searchable_exts = ['.txt', '.html']

    def ic(self, item, column):
        if hasattr(self, 'viewer'):
            if hasattr(item, 'path'):
                self.viewer.cd(item.path)
            else:
                self.viewer.show(item)

    def dic(self, item, column):
        self.parent.api.dialog('info', 'File path', item.url)

    def expanded(self, item, header=False):
        items = []
        item.removeChild(item.child(0))
        root = os.path.join('/', item.path)
        if not hasattr(item, 'filled'):
            for d in sorted(os.listdir(root)):
                if self.fileFilter(os.path.join(root, d)):
                    name = self.nameFilter(d, root)
                    it = QTreeWidgetItem([name])
                    it.name = name
                    item.path = d
                    if os.path.isdir(os.path.join(root, d)):
                        it.path = os.path.join(root, d)
                        it.setIcon(0, QIcon.fromTheme('folder'))
                        it.addChild(QTreeWidgetItem(it, ['..']))
                    else:
                        mime = mimetypes.guess_type(os.path.join(root, d))[0]
                        if not mime is None:
                            mime = mime.replace("/", '-')
                            it.setIcon(0, QIcon.fromTheme(mime, QIcon.fromTheme('empty')))
                        else:
                            it.setIcon(0, QIcon.fromTheme('empty'))
                        it.url = os.path.join(root, d)
                    items.append(it)
                    self.items.append(it)
            item.filled = True

        items = sorted(items, key=lambda x: x.path if hasattr(x, 'path') else '', reverse=True)
        if not header:
            item.addChildren(items)
        else:
            self.insertTopLevelItems(0, items)

    def cd(self, path):
        for item in self.items:
            if hasattr(item, 'path') and item.path == path:
                item.setExpanded(True)
                self.expanded(item)
                break

    def nameFilter(self, name, root):
        return name

    def fileFilter(self, path):
        return True

    def WFind(self, text, full=False, getlist=False):
        its = []
        if self.full_text.checkState() == Qt.Checked or full:
            for i in self.items:
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
            if i not in its:
                i.setHidden(True)
            else:
                i.setHidden(False)
        if not getlist:
            return len(its)
        else:
            return its

    def getWidget(self, search=False, full=False):
        frame = QWidget()
        frame.tree = self
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


class WinterFileList(QListWidget):
    def __init__(self):
        QListWidget.__init__(self)
        self.itemDoubleClicked.connect(self.cd)
        self.cd(CWD)

    def cd(self, path):
        if not type(path).__name__ == 'str':
            path = path.path
            self.tree.cd(path)
        self.clear()
        item = QListWidgetItem(QIcon.fromTheme('folder'), '..')
        item.path = os.path.split(path)[0]
        self.addItem(item)
        if os.path.isdir(path):
            for d in os.listdir(path):
                if os.path.isdir(os.path.join(path, d)):
                    icon = 'folder'
                else:
                    mime = mimetypes.guess_type(os.path.join(path, d))[0]
                    if not mime is None:
                        mime = mime.replace("/", '-')
                        icon = mime
                    else:
                        icon = 'empty'
                item = QListWidgetItem(QIcon.fromTheme(icon, QIcon.fromTheme('empty')), d)
                item.path = os.path.join(path, d)
                self.addItem(item)


class WinterSideBar(QToolBar):
    def __init__(self, parent):
        self.parent = parent
        QToolBar.__init__(self)
        self.setObjectName('sideBar')
        self.parent.addToolBar(Qt.LeftToolBarArea, self)

        self.setIconSize(
            QSize(self.parent.config.options.ui.sbicon_size, self.parent.config.options.ui.sbicon_size))
        self.setMovable(self.parent.config.options.ui.sb_movable)

        self.dock = QDockWidget()
        self.dock.setObjectName('sideBarDock')
        self.dock.stack = QStackedWidget()
        self.stack = self.dock.stack
        self.dock.setWidget(self.stack)
        self.parent.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        self.dock.hide()
