
# liste et index
a = [1 , "hello" , [ True , 'a' , 2 ] ]
b = list(range(12))
print (a)
print (b)
a = [1 ,2 , 3 ,4 ,5 ,6 ,"hello"]
b = a[0:3]
c = a[6::-1]
d = a[6:0:-1]
print (b)
print (c)
print (d)
# liste et decomptage 
h = [1 , 2 , 3]
b,c,d = h
print (b,c,d) # b, c , d prend les valeurs de la liste h 
# mais si on a fait b,c,d,f = h il ya une erreure car le nombre des variables depasse la taille de la liste et aussi la eme case
# si la taille depasse le nombre de valeure exemple h = [ 1, 2,3 , 4] puis on met b,c,d = h erreure mais on peut mettre :
h = [1 ,2 ,3 ,4] # puis 
b , c , d , *k = h # elle affiche 123
print (b,c,d)
print (b,c,d,k) # elle affiche 1234 
b , c , *e = a   
print (b,c) # on aura 12
b , c , *e , f = a   
print (b,c,f) # on aura 1 2 hello
a = [1,2,3,[1,6]]   
b = [1,2,3]   #  mais c ona mets b=a on aura le meme id 
print (id(a))
print (id(b))
c = a[:]                   
print (c) ; print (id(c))
c[3][1] = 7           
print (a); print (c)
c[0] = 2 
print (a)
print (c)
g = [1,4,5,[1,6]]
g[3][0] = 'hello'
print(a)
print(g)
import copy 
b = copy.deepcopy(a)
print (a)
print (b)
b[3][0] = 'c' ; print (a) ; print (b)
# voila l'imporrtance de la methode deepcopy : meme si ona a l'interieure d'une liste un objet modifiable mais avec deepcopy on va 
# cree un nouvel objet python c a dire c ona modifie cet objet muable dans la variable b il sera pas modifie dans la variable a 
# car ona utilise la methode deepcopy
# ona ses deux syyntaxe signifie  la meme choose c = a[:] ; c = a.copy()
# l'operateure is pour voir c les deux objets ont la meme adresse de reference
m = [ 1 , 5 , 6] 
m.append(4) # la methode append permet d'ajouter un element a la fin de la liste \
print (m)
m.insert (1 , 7)# la methde insert fait la meme choose que append mais c pas a la fin de la liste on disigne l'index ou on insire
# la valeure et aussi la valeure \
print(m)
m.extend ("hello") # la methode extend elle ajoute une nouvelle valeure a notre liste a condition que cette valeure soit iterable 
# elle ne cree pas un autre objet python mais juste elle modifie la liste parcontre si on fait l'addition elle cree un  autre objet python 
# c'est ca la difference entre l'addition et la methode extend.
print (m)
n = [ 1 ,2 ,3 ,4 , "hello" , "moumouh" ]
n.remove(4) # par la methode remove on indique la valeure q 'on souhaite a supprimer dans la liste 
print (n) 
n.pop() 
print (n)
n.extend ("moumouh")
n.pop(0)
print (n)
# la methode pop supprime une valeure dans la liste on indiquant l'index de cette valeure mais c  indique pas l'index 
# elle supprime la derniere valeure par defaut et aussi la methode pop retourne la valeure q'ona supprimer dans la liste exemple 
# b = n.pop(2), b prend la valeure  qui est  a l'index 2
n.clear() # la methode clear supprime tout la liste 
print (n)
n = [ 1 ,2 ,3 ,4 , "hello" , "moumouh" ]
b = n.index(3,0,3) # b contient l'index de la valeure 3 dans la liste 
print(b)
c = n.index(1)  # c contient l'index de la valeure 1 dans la liste
print (c)
print ( 3 in n) ; print ('c' in 'chemin' ); print ('galou' in n) ; print ('z' in 'chemin')

a = [ 'a' , 'c' , 'z' , 'b']
a.sort() 
print (a)
a.sort(reverse = True) # \ on affiche la liste a mais triee dans l'ordre decroissant selon l'alphabet
print (a)
b = sorted(a) # la liste b contient la liste a mais  triee dans l'ordre croissant selon l'alphabet
print (a)
print (b)
a.reverse() # on va afficher la liste  a dans le sense inverse q'ona deja la declare 
print (a)
print ("m".join(a)) # a chaque caractere dans la liste a on va l'ajouter le caractere m puis on va concatiner tout les caracteres et 
# on affiche la chaine de caractere
print ("".join(a)) #  on va concatiner les caracteres de la liste a et on affiche la chaiine de caractere
h = {1 , 2 ,5 }
print (type(h))
 # le chapitre 7 lkes dictionnaires 

a = {
 
  'name' : 'moumouh',
   'age' : 19 ,
  'adresse' : {
      'city' : 'tazmalt',
       'rue' : 'la rue de beni melliikeche'
  },
  19 : " c,est l'age de moumouh " 
} 
print (a) , print (a["adresse"]["city"]) , print (a[19])
b = {
    'name' : "moumouh",
    'name' : "mohandlarbi", # quand on va declarer deux variables avec le meme nom pythion va prendre on consideration la valeure de 
}
# la derniere variable q'on a declare 
print (b['name']) # il nous affiche mohandlarbi
# la methode get copy et clear dans les dectionnaires
a = {
    'nom' : "galou",
    'prenom':"moumouh",
     'numero':[7,96,30,38,16],
       6 : " wilaya de bejaia",
       'grades' : [12 , 15 , 20] 
}  
if 'numero' in a :
      print ("ona trouve le num de moumouh ")
else :
      print (" numero introuvable ")
print (a.get("weight" , '80kg'))

if 'weight' in a :
      print ("ona trouve le weight de moumouh ")
else :
      print (" weight introuvable ")
b = a.copy()
print (b)
b['numero'].insert(0 , 17)
print(b) , print (a) # on remarque que so ona modifie b la liste a se modifie a condition que la variable q'ona modifie est de type
# muable , si elle est pas muable a ne sera pas modifier . b = a.copy()
# si ona fait a.clear() c a dire ona effacer tout les elements de dectionnaire a

# parcourir les dectionnaire 
for item in a:
      print (item)
for item in a.keys() :
      print (item)
for item in a.values() :
      print (item)
for item in a.items() :
      print (item)
for (keys , values) in a.items():    
      print (keys)
      print (values)      

# la suppression des elements dans un dectionnaires 

b = a.pop ('nom')
print (b)
print (a)
c = a.popitem() 
d = a.popitem() 
e = a.popitem()
print (c) , print (d), print (e), print (a)
a.update({'prenom': "larbi"}) # j'ai fais la modification de prenom 
print (a) 

a.setdefault('num' , [] ) 
a['num'].append(12)
print (a) # setdefault permet d'ajouter une et sa valeure au dectionnaire 
# on va la definer sans setdefault
b = 45
if 'num' in a :
   a['num'].append(12)
else :
      a['num'] = [b]
print (a)


