import os
from time import time
import re
import string
import weakref
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from winterstone.base import WinterObject
from winterstone.baseQt import SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons
from winterstone.extraQt import WinterEditor, CustomLexer, CustomStyle

from winterstone.baseQt import API

from mongate.connection import Connection

import urllib.request as req
import urllib.parse as parse

import json

import pystache
import pyparsing as p



#TODO: create "collection" class
#TODO: big files storage

#TODO: crud single item of collection



class Core(QObject):                   #TODO: Split for CoreUI and Core (without using self.app)
    """
        Store all your app logic here
    """

    SetProgress = pyqtSignal(int)

    def __init__(self):
        QObject.__init__(self)
        self.app = None
        self.collection_desc = None

    def _afterInit(self):
        """
            when application totally init
        """
        self.api = API()
        self.api.ex = self.app.getMethod
        self.api.config = self.app.config
        self.main()
        # self.api.info('Core loaded.')


    def main(self):
        """
            dummy for main core method.
        """
        url = 'http://%s:%s/orlangur/_authenticate' % (
        self.api.config.options.app.orlangur_server, self.api.config.options.app.orlangur_port)
        data = {'username': self.api.config.options.app.orlangur_user,
                'password': self.api.config.options.app.orlangur_password}
        from urllib.error import URLError

        try:
            r = req.Request(url, parse.urlencode(data).encode('utf8'))
            req.urlopen(r).read()
            connection = Connection(self.api.config.options.app.orlangur_server,
                self.api.config.options.app.orlangur_port)
            db = connection.orlangur
            self.db = db
        except URLError:
            QMessageBox.warning(self.app, 'Error',
                'Orlangur server seems down')
            return


        self.compiler = pystache

        self.app.async(self.getConfig, self.assignConfig)


    def getConfig(self):
        """
            Fetch cloud config
        """
        return self.getCollection('en_clients', title='Orlangur')[0]


    def assignConfig(self, config):
        """
            Callback after getConfig
        """
        self.orlangur_config = config


    def fillList(self):
        """
            Refresh collections list. See fillList_callback as callback
        """
        self.app.list.clear()
        self.app.statusBar.showMessage('Fetching meta collection...')
        self.app.async(lambda: self.getCollection('__meta__'), self.fillList_callback)

    def fillList_callback(self, meta):
        """
            See fillList
        """
        meta = sorted(meta, key=lambda x: x['desc'])
        for collection_meta in meta:
            item = QListWidgetItem('%s' % collection_meta['desc'])
            self.app.list.addItem(item)
            item.collection = collection_meta['name']
        self.app.statusBar.showMessage('Collection list filled.')


    def onClick(self, item):
        """
            Collection mouse click handler #Yoda style comment
        """
        self.editCollection(item.collection, item.text())


    def editCollection(self, collection_name, collection_desc=None, callback=None):
        self.collection_name = collection_name
        if collection_desc is not None:
            self.collection_desc = collection_desc
        else:
            self.collection_desc = collection_name

        if callback is None:
            callback = self.editCollection_callback

        self.app.async(lambda: self.getCollection(collection_name, meta=True), callback)
        self.app.statusBar.showMessage('Fetching collection...')


    def editCollection_callback(self, collection):

        editor = self.app.addEditorTab(self.collection_desc)

        self.app.selectTab(self.collection_desc)
#        self.app.viewer.setHtml('')
#        self.app.item_list.clear()
        try:
            meta, collection = collection
        except ValueError:
            meta = ''

        if 'sort_field' in meta:
            collection = sorted(collection, key=lambda x: x[meta['sort_field']])

#        self.app.rp.setTabText(self.app.rp.tab_list['Editor'], self.collection_desc)
        self.app.statusBar.showMessage('Collection fetched successfully')
        editor.collection = self.collection_name

        content = json.dumps(collection, sort_keys=True, indent=4, ensure_ascii=False)

        editor.setText(content)
        editor.editor.setModified(False)
        editor.editor.setReadOnly(False)

        #TODO: make good html view

#        if 'item_template' in meta:
#            for item in collection:
#                self.app.addListItem(self.compiler.render(meta['item_template'], item))
#
#        if 'item_template_html' in meta:
#            html = '<div id="meta">'
#            for item in collection:
#                html += self.compiler.render('<div>%s</div>' % meta['item_template_html'], item)
#            html += '</div>'
#
#            self.app.viewer.setHtml(html)


    def getCollection(self, col_name, fetch=True, meta=False, order_by="", **kwargs):
        collection = self.db.__getattr__(col_name)
        if fetch:
            if not order_by:
                items = collection.find(criteria=kwargs)
            else:
                crit = kwargs
                crit['$sort'] = {'order_by': 1}
                items = collection.find(criteria=crit)
            if not meta or col_name == '__meta__':
                return items
            else:
                return [self.getCollection('__meta__', name=col_name)[0], items]
        else:
            if not meta or col_name == '__meta__':
                return collection
            else:
                return [self.getCollection('__meta__', name=col_name)[0], collection]


    def saveCollection(self, name, content, callback=None):
        edited = self.app.editors[name].editor.isModified()
        edited = True      #TODO: fix
        if edited:
            self.app.pb.setMaximum(len(content))
            self.SetProgress.connect(self.app.pb.setValue)
            self.app.async(lambda: self._saveCollection(name, content),
                lambda: self.saveCollection_callback(name, callback))
        else:
            self.app.statusBar.showMessage('Collection not modified')

    def saveCollection_callback(self, name, callback=None):
        self.api.info('Collection %s saved' % name)
        self.app.editors[name].setText(json.dumps(self.getCollection(name), sort_keys=True, indent=4, ensure_ascii=False))
        if callback is not None:
            callback()

    def _saveCollection(self, name, content):
        collection = self.getCollection(name, fetch=False)
        col_content = self.getCollection(name)
        items = [i['_id'] for i in col_content]
        new_ids = []
        for i in content:
            if '_id' in i:
                new_ids.append(i['_id'])
        for i in items:
            if i not in new_ids:
                collection.remove({'_id': i})

        for i, item in enumerate(content):
            self.SetProgress.emit(i)
            if '_id' in item:
                orig = ''
                for it in col_content:
                    if it['_id'] == item['_id']:
                        orig = it
                        break
                if orig and item != orig:
                    mods = {'$set': {}, '$unset': {}}
                    for key in item:
                        if key != '_id':
                            mods['$set'][key] = item[key]
                    for key in orig:
                        if key not in item:
                            mods['$unset'][key] = ""

                    print(mods)
                    collection.update({'_id': item['_id']}, mods)

            else:
                collection.insert(item)


    def editMeta(self):
        self.collection_name = '__meta__'
        self.collection_desc = 'Meta'
        self.app.async(lambda: self.getCollection('__meta__'), self.editCollection)


    def addCollection(self):
        name, status = QInputDialog.getText(self.app, 'Add collection', 'Collection name')
        if status:
            self.app.async(lambda: self._addCollection(name), self.fillList)


    def _addCollection(self, name):
        collection = self.getCollection('__meta__', fetch=False)
        collection.save({
            "desc": name,
            "name": name,
            "template": self.api.config.options.app.default_template})
        return True

    def delCollection(self):
        if self.app.list.currentItem():
            name = self.app.list.currentItem().collection
            msgBox = QMessageBox()
            msgBox.setText("Delete collection")
            msgBox.setInformativeText("Do you want to delete %s collection?" % name)
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)
            msgBox.setDetailedText(json.dumps(self.getCollection(name), sort_keys=True, indent=4))
            ret = msgBox.exec_()
            if ret == QMessageBox.Yes:
#                self.app.editor.editor.setReadOnly(True)
                self.app.async(lambda: self._delCollection(name), self.fillList)

    def _delCollection(self, name):
        meta = self.getCollection('__meta__', fetch=False)
        meta.remove({'name': name})
        return True

    def backUp(self):
        self.app.pb.setVisible(True)
        self.app.async(self._backUp, lambda: self.app.statusBar.showMessage('Backuped successfully'))

    def _backUp(self):
        backup = {'__meta__': self.getCollection('__meta__')}
        self.app.pb.setMaximum(len(backup['__meta__']))
        for i, collection in enumerate(backup['__meta__']):
            print('Fetching %s' % collection['name'])
            backup[collection['name']] = self.getCollection(collection['name'])
            self.app.pb.setValue(i)

        json.dump(
            backup,
            open(os.path.join(self.api.CWD, 'backups', str(int(time())) + '.json'), 'w', encoding="utf8"),
            indent=4
        )


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
        self.editor = None
        self.collection = None
        self.api = None
        WinterEditor.__init__(self, parent, **kwargs)
        WinterEditor.__refs__[WinterEditor].append(weakref.ref(self))   #this is bad=(
        self.setLexer(JSONLexer(self.parent, self))

    def unN(self, text):
        result = text
        if self.allow_br:
            chunks = re.split(r'("(?:[^"\\]|\\.)*")', text)
            result = chunks[0]
            for i in range(1, len(chunks), 2):
                result +=\
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
        WinterEditor._afterAppInit(self)
        self.tb_2 = QToolBar(self)
        self.layout().insertWidget(1, self.tb_2)
        ak = self.api.ex('createAction')('circle-plus', 'Add key', self.addKey, keyseq=QKeySequence.New)
        self.tb_2.addAction(ak)

    def addKey(self):    #REMOVE: not very good idea=(
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
