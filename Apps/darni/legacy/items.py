from weapons import WEAPONS
TYPES={\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Head':{\
			'Common':[{'name':'Helmet','type':'armor','defense':1},{'name':'Cap','type':'cloth','defense':1},{'name':'Band','type':'cloth','defense':1}],\
			'Rare':[{'name':'Crown','type':'armor','defense':1},{'name':'Tiara','type':'armor','defense':1}],\
			'Unique':[{'name':'Diadem','type':'armor','defense':1},{'name':'Mask','type':'armor','defense':1}]},\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Body':{\
			'Common':[{'name':'Shirt','defense':5,'type':'cloth'},{'name':'Robe','type':'cloth','defense':5},{'name':'Jacket','type':'cloth','defense':5},{'name':'Armor','type':'armor','defense':5},{'name':'Studded Armor','type':'armor','defense':5},{'name':'Quilted Armor','type':'armor','defense':5}],\
			'Rare':[{'name':'Ring Mail','type':'armor','defense':5},{'name':'Chain Mail','type':'armor','defense':5}],\
			'Unique':[{'name':'Scale Mail','type':'armor','defense':5},{'name':'Plate Mail','type':'armor','defense':5},{'name':'Splint Mail','type':'armor','defense':5}]},\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Legs':\
			[{'name':'Pants','defense':2,'type':'cloth'},{'name':'Leggings','type':'armor','defense':2}],\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Boots':\
			[{'name':'Sandals','type':'cloth','defense':2},{'name':'Shoes','type':'cloth','defense':2},{'name':'Boots','type':'armor','defense':2},{'name':'High Boots','type':'armor','defense':2},],\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Gloves':\
			[{'name':'Gauntlet','type':'armor','defense':2},{'name':'Glove','type':'armor','defense':2},{'name':'Glove','type':'cloth','defense':2}],\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Neck':\
			[{'name':'Amulet','type':'jewel','defense':0},{'name':'Chaplet','type':'jewel','defense':0},{'name':'Necklace','type':'jewel','defense':0},{'name':'Pendant','type':'jewel','defense':0}],\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Cloak':\
			[{'name':'Cloak','type':'cloth','defense':0},{'name':'Hooded Cloak','type':'cloth','defense':0}],\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Rings':\
			[{'name':'Ring','type':'jewel'}],\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'Braces':\
			[{'name':'Bracelet','type':'jewel'},{'name':'Wristband','type':'cloth'}],\
		'Hands':{\
		'Weapons':WEAPONS,\
			'Shields':[{'name':'Shield','type':'armor','defense':5},{'name': 'Small Shield','type':'armor','defense':5}, {'name': 'Large Shield','type':'armor','defense':5}, {'name': 'Kite Shield','type':'armor','defense':5}, {'name': 'Tower Shield','type':'armor','defense':5}, {'name': 'Gothic Shield','type':'armor','defense':5}, {'name': 'Bone Shield','type':'armor','defense':5}, {'name': 'Spiked Shield','type':'armor','defense':5},{'name': 'Phoenix Shield','type':'armor','defense':5},{'name': 'Totem Shield','type':'armor','defense':5}, {'name': 'Bladed Shield','type':'armor','defense':5}, {'name': 'Bull Shield','type':'armor','defense':5}, {'name': 'Bronze Shield','type':'armor','defense':5}, {'name': 'Gilded Shield','type':'armor','defense':5},{'name': 'Heraldic Shield','type':'armor','defense':5}, {'name': 'Aerin Shield','type':'armor','defense':5}, {'name': 'Crown Shield','type':'armor','defense':5}],\
		}
		}

TM_EXCEPT={'Ring Mail':['Bone','Leather','Wood','Crystal','Glass','Onyx','Obsidian'],'Chain Mail':['Bone','Leather','Wood','Crystal','Glass','Onyx','Obsidian'],'Scale Mail':['Leather'],'Plate Mail':['Leather'],'Splint Mail':['Leather'],'Tiara':['Iron','Steel'],'Diadem':['Iron','Steel']}
TT_EXCEPT={'Gothic':['Pants','Shoes','Cap'],'Elven':['Pants','Shoes','Cap'],'Orchish':['Pants','Shoes'],'Daedric':['Pants','Shoes','Cap'],'Gnomish':['Pants','Shoes'],'Demonic':['Pants','Shoes','Cap'],'Aeris':['Pants','Shoes','Cap'],'Common':[''],'Imperial':['']}

MATERIALS={\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'armor':{\
				'Common':[{'name':'Iron','defense':2,'weight':1,'price':2,'capacity':2},{'name':'Steel','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Bone','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Leather','weight':1,'price':2,'capacity':2,'defense':2}],\
			'Rare':[{'name':'Silver','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Wood','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Crystal','weight':1,'price':2,'defense':2},{'name':'Mithril','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Glass','weight':1,'price':2,'capacity':2,'defense':2}],\
			'Unique':[{'name':'Obsidian','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Onyx','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Eternium','weight':1,'price':2,'capacity':2,'defense':2},{'name':'Aeonium','weight':1,'price':2,'capacity':2,'defense':2}]},\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'weapons':{\
				'Common':[{'name':'Iron','dmg':2,'weight':1,'price':2,'capacity':2},{'name':'Steel','weight':1,'price':2,'capacity':2,'dmg':2}],\
			'Rare':[{'name':'Silver','weight':1,'price':2,'capacity':2,'dmg':2},{'name':'Wood','weight':1,'price':2,'capacity':2,'dmg':2},{'name':'Crystal','weight':1,'price':2},{'name':'Mithril','weight':1,'price':2,'capacity':2,'dmg':2},{'name':'Glass','weight':1,'price':2,'capacity':2,'dmg':2}],\
			'Unique':[{'name':'Obsidian','weight':1,'price':2,'capacity':2,'dmg':2},{'name':'Onyx','weight':1,'price':2,'capacity':2,'dmg':2},{'name':'Eternium','weight':1,'price':2,'capacity':2,'dmg':2},{'name':'Aeonium','weight':1,'price':2,'capacity':2,'dmg':2}]},\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'cloth':{\
			'Common':[{'name':'Leather','price':1,'capacity':1},{'name':'Cotton','price':2,'capacity':1},{'name':'Wool','price':2,'capacity':1},{'name':'Fur','price':2,'capacity':1}],\
			'Rare':[{'name':'Silk','price':5,'capacity':3}],\
			'Unique':[{'name':'Aeonium','price':20,'capacity':5}]},\
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		'jewel':{\
			'Common':[{'name':'Iron'},{'name':'Steel'},{'name':'Bone'},{'name':'Leather'},{'name':'Wood'},{'name':'Copper'}],\
			'Rare':[{'name':'Crystal'},{'name':'Mithril'},{'name':'Glass'},{'name':'Obsidian'},{'name':'Onyx'},{'name':'Silver'}],\
			'Unique':[{'name':'Eternium'},{'name':'Aeonium'},{'name':'Gold'},{'name':'Platinum'}]}\
			}
QTITLES={\
		'Unique':[{'name':'Ancient','color':'ancient'},{'name':'Perfect','color':'perfect'},{'name':'Sacred','color':'sacred'}],\
		'Rare':[{'name':'Great','color':'great'},{'name':'Superior','color':'superior'}],\
		'Common':[{'name':'Wearied','color':'wearied'},{'name':'Common','color':'None'}]\
		}


TITLES={'Common':[{'name':'Elven'},{'name':'Orchish'},{'name':'Gnomish'},{'name':'Common'},{'name':'Imperial'}],\
		'Rare':[{'name':'Daedric'},{'name':'Gothic'}],\
		'Unique':[{'name':'Demonic'},{'name':'Aeris'}]}
PREFIXES=[]
POSTFIXES=[]
COLORS=['Snow','Ghost White','White Smoke','Gainsboro','Floral White','Old Lace','Linen','Antique White','Papaya Whip','Blanched Almond','Bisque','Peach Puff','Navajo White','Moccasin','Cornsilk','Ivory','Lemon Chiffon','Seashell','Honeydew','Mint Cream','Azure','Alice Blue','Lavender','Lavender Blush','Misty Rose','White','Black','Dim Gray','Slate Gray','Grey','Midnight Blue','Navy Blue','Cornflower Blue','Slate Blue','Royal Blue','Blue','Dodger Blue','Steel Blue','Powder Blue','Pale Turquoise','Turquoise','Cyan','Cadet Blue','Aquamarine','Sea Green','Pale Green','Spring Green','Lawn Green','Green','Chartreuse','Green Yellow','Lime Green','Yellow Green','Forest Green','Olive Drab','Khaki','Pale Goldenrod','Yellow','Gold','Goldenrod','Rosy Brown','Indian Red','Saddle Brown','Sienna','Peru','Burlywood','Beige','Wheat','Sandy Brown','Tan','Chocolate','Firebrick','Brown','Salmon','Orange','Coral','Tomato','Orange Red','Red','Hot Pink','Pink','Pale Violet Red','Maroon','Violet Red','Magenta','Violet','Plum','Orchid','Blue Violet','Purple','Thistle','Snow','Seashell','Antique White','Bisque','Peach Puff','Navajo White','Lemon Chiffon','Cornsilk','Ivory','Honeydew','Lavender Blush','Misty Rose','Azure','Slate Blue','Royal Blue','Blue','Dodger Blue','Steel Blue','Slate Gray','Pale Turquoise','Cadet Blue','Turquoise','Cyan','Aquamarine','Sea Green','Pale Green','Spring Green','Green','Chartreuse','Olive Drab','Khaki','Yellow','Gold','Goldenrod','Rosy Brown','Indian Red','Sienna','Burlywood','Wheat','Tan','Chocolate','Firebrick','Brown','Salmon','Orange','Coral','Tomato','OrangeRed','Red','Hot Pink','Pink','Pale Violet Red','Maroon','Violet Red','Magenta','Orchid','Plum','Purple','Thistle','Grey']

EFFECTS={}
