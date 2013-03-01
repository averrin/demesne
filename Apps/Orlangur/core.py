import os
from time import time
import re
import string
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from winterstone.baseQt import SBAction
from winterstone.winterBug import try_this
from winterstone.snowflake import CWD, loadIcons

from winterstone.baseQt import API

from mongate.connection import Connection

import urllib.request as req
import urllib.parse as parse

import json

import pystache


#TODO: create "collection" class
#TODO: big files storage

#TODO: crud single item of collection


class Core(QObject):
    """
        Store all your app logic here
    """

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
        except URLError:
            QMessageBox.warning(self.app, 'Error',
                'API не отвечает, проверьте доступность сервера и корректность настроек')

        self.db = db

        self.compiler = pystache

        self.app.async(self.getConfig, self.assignConfig)


    def getConfig(self):
        return self.getCollection('en_clients', title='Orlangur')[0]


    def assignConfig(self, config):
        self.orlangur_config = config
        print(config)


    def fillList(self):
        self.app.list.clear()
        self.app.statusBar.showMessage('Fetching meta collection...')
        self.app.async(lambda: self.getCollection('__meta__'), self._fillList)

    def _fillList(self, meta):
        meta = sorted(meta, key=lambda x: x['desc'])
        for collection_meta in meta:
            item = QListWidgetItem('%s' % collection_meta['desc'])
            self.app.list.addItem(item)
            item.collection = collection_meta['name']
        self.app.statusBar.showMessage('Collection list filled.')


    def onClick(self, item):
        self.editCollection(item.collection, item.text())


    def editCollection(self, collection_name, collection_desc=None):
        self.collection_name = collection_name
        if collection_desc is not None:
            self.collection_desc = collection_desc
        else:
            self.collection_desc = collection_name
        self.app.async(lambda: self.getCollection(collection_name, meta=True), self._editCollection)
        self.app.statusBar.showMessage('Fetching collection...')


    def _editCollection(self, collection):
        self.app.selectTab('Editor')
        self.app.viewer.setHtml('')
        self.app.item_list.clear()
        try:
            meta, collection = collection
        except ValueError:
            meta = ''

        if 'sort_field' in meta:
            collection = sorted(collection, key=lambda x: x[meta['sort_field']])

        self.app.rp.setTabText(0, self.collection_desc)
        self.app.statusBar.showMessage('Collection fetched successfully')
        self.app.editor.collection = self.collection_name

        content = json.dumps(collection, sort_keys=True, indent=4, ensure_ascii=False)

        self.app.editor.setText(content)
        self.app.editor.editor.setModified(False)
        self.app.editor.editor.setReadOnly(False)

        if 'item_template' in meta:
            for item in collection:
                self.app.addListItem(self.compiler.render(meta['item_template'], item))

        if 'item_template_html' in meta:
            html = '<div id="meta">'
            for item in collection:
                html += self.compiler.render('<div>%s</div>' % meta['item_template_html'], item)
            html += '</div>'

            self.app.viewer.setHtml(html)


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
        if self.app.editor.editor.isModified():
            self.app.pb.setMaximum(len(content))
            self.connect(self, SIGNAL('setProgress'), self.app.pb.setValue)
            self.app.async(lambda: self._saveCollection(name, content),
                lambda: self._afterSaveCollection(name, callback))
        else:
            self.app.statusBar.showMessage('Collection not modified')

    def _afterSaveCollection(self, name, callback=None):
        self.api.info('Collection %s saved' % name)
        self.app.editor.setText(json.dumps(self.getCollection(name), sort_keys=True, indent=4, ensure_ascii=False))
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
            self.emit(SIGNAL('setProgress'), i)
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
                self.app.editor.editor.setReadOnly(True)
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
            
        