#import re
from winterstone.base import WinterObject

def giveId(element):
	id=element.__hash__()
	return "%s%d" % (element.prefix,id)

class Shiver(WinterObject):
	def __init__(self,prefix):
		self.prefix=prefix
		self.id=giveId(self)
		self.line=self.__dict__
	def __getitem__(self,key):
		return self.__dict__[key]
	def __setitem__(self,key,value):
		self.__dict__[key]=value
	#def __str__(self):
		#return self.line
	def onAdd(self):
		pass
	def onDestroy(self):
		pass

class Cube(object):
	def __init__(self,elementClass=Shiver):
		self.elementClass=elementClass
		self.elements=[]
		self.lists={}

	def addList(self,list,name):
		self.lists[name]=list
		return self.lists
	def addListAttr(self,attr):
		return self.addList(self.listAttr(attr),attr)
	def addListBy(self,attr,value):
		return self.addList(self.listBy(attr,value),'%s[%s]' % (attr,value))

	def add(self,element):
		l=False
		if type(element).__name__=='list':
			l=True
			for e in element:
				self.add(e)
		if (isinstance(element,self.elementClass) or issubclass(element.__class__,self.elementClass)) and element not in self.elements:
			self.elements.append(element)
			element.destroy=lambda: self.remove(element)
			element.onAdd()
			self.onAdd(element)
			return self.elements
		elif l:
			return self.elements
		else:
			self.error='wrong type of <element> [%s]' % element
			return False

	def addTrig(self,element,attr):
		if type(element).__name__=='list':
			for item in element:
				item[attr]=True
		else:
			element[attr]=True
		self.add(element)
		return self.listBy(attr,True)

	def remove(self,element): #id or index
		if type(element).__name__=='str':
			tp='id'
		elif type(element).__name__=='int' and element<len(self.elements):
			tp='index'
		elif isinstance(element,self.elementClass) and element in self.elements:
			tp='element'
		else:
			self.error='wrong type of <element> [%s] or no such <element> in %s' % (element,self)
			return False
		if tp=='index':
			e=self.elements[element]
		elif tp=='id':
			for e in self.elements:
				if e.id==element:
					break
		elif tp=='element':
			e=element
		try:
			self.elements.remove(e)
			e.onDestroy()
			self.onRemove(e)
			return self.elements
		except:
			self.error='can`t remove <element> [%s]' % element
			return False
	def removeTrig(self,element,attr):
		element[attr]=False
		self.remove(element)
		return self.listBy(attr,True)
	def count(self):
		return len(self.elements)

	def listAttr(self,attr,unique=False):
		l=[e[attr] for e in self.elements if hasattr(e,attr)]
		if unique:
			set = {}
			map(set.__setitem__, l, [])
			l=set.keys()
		return l
	def dictAttr(self,attr):
		l={}
		for e in self.elements:
			if hasattr(e,attr):
				l[e[attr]]=e
		return l

	def listBy(self,attr,value):
		l=[e for e in self.elements if hasattr(e,attr) and e[attr]==value]
		return l
	def itemBy(self,attr,value):
		return self.listBy(attr,value)[0]
	def list(self,name):
		return self.lists[name]

	def onAdd(self,element):
		pass
	def onRemove(self,element):
		pass

	def refresh(self):
		backup=self.elements[:]
		self.elements=[]
		for e in backup:
			self.add(e)
