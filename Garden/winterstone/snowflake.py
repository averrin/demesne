# -*- coding: utf-8 -*-
import os
import sys
import re

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    pass

CWD = sys.path[0] + '/'
vaults = [os.path.normpath(CWD + 'Vault/'), os.path.normpath(CWD + '../../Vault/') + '/', os.path.normpath(CWD + '../Vault/') + '/']
VAULT = ''
for v in vaults:
    if os.path.isdir(v):
        VAULT = v
# if not VAULT:
#     raise Exception('No Vault dir')

#if 'Vault' not in os.listdir(path):
#    while os.path.split(os.path.dirname(path))[1] != 'Vault':
#        dirname = os.path.split(os.path.dirname(path))[1]
#        if dirname == 'Demesne':
#            path += 'Vault/'
#            if os.path.split(os.path.dirname(CWD))[1] not in ['Ravenor', 'Butler', 'darni', 'Steam','AdomBrowser']:
#                CWD += 'Butler/'
#        else:
#            path = os.path.normpath(path + '../') + '/'
#    VAULT = path
#else:
#    VAULT = os.path.join(path, 'Vault/')


def loadIcons(icondir, ext=['.png', '.jpg']):
    """""
        return dict: {'iconname':'iconpath'}
    """""
    icons = {}
    dirList = os.listdir(icondir)
    for fname in dirList:
        print(str(icondir + fname), os.path.isdir(str(icondir + fname)))
        if os.path.isdir(str(icondir + fname)):
            subdirList = os.listdir(str(icondir + fname))
            for fi in subdirList:
                if fi[:4] in ext:
                    icons['fname/' + fi[:-4]] = str(icondir + fname + fi)
        elif fname[:4] in ext:
            icons[fname[:-4]] = str(icondir + fname)
    return icons


def getFileContent(filename):
    """""
        return file content
    """""
    with open(filename) as f:
        content = f.read()
        try:
            enc = BeautifulSoup(content).originalEncoding
            if enc == 'ISO-8859-2':
                content = content.decode('cp1251')
            elif enc in ['utf-8', 'utf8']:
                content = content.decode('utf8')
        except NameError:
            pass
    return content


def replaceInopen(file, str, repl):
    content = getFileContent(file)
    content = re.sub(str, repl, content)
    file = open(file, 'w')
    file.write(content)
    file.close()


def htmlColor(msg, color_str):
    if color_str == 'None':
        return ''
    else:
        return '<span class="color_%s">%s</span>' % (color_str, msg)


import pickle as pickle


def save(obj, filename):
    p = pickle.dumps(obj, 2)
    open(filename, 'wb').write(p)


def load(filename):
    return pickle.load(open(filename, 'rb'))
