print (" python is a good language for programming")
a=1
b='2'
c=str(a)+b
print (c)
print (type(c))
d=a+int(b)
print (d)
print (type(d))
### il ya des types mutables (modifiables ) comme (dict,list,set) et des types immuables (ne sont pas modifiables) c a dire quand on change 
# la valeure de la variable on va changer tout l'objet et cet objet prend une auutre adresse.
a = 1  # cas d'entier qui est non modifiable les 2 adresses de references sont egaux car les deux pointe sur le meme objet
b = a
print (a==b) 
print (a is b)
print (id(a))
print (id(b))
a=[1,2] # dans e cas de type list quii est modifiables les deux adresses de references sont differntes car elles ne pointenet pas sur le meme 
#objet , chacune pointe sur un objet
b=[1,2]
print (a==b)
print (a is b)
print (id(a))
print (id(b))
# dans le cas de l'egalite == on compare les objets , dans le cas de l'identite  'is' on compare les adresses de references


# if , elif ,else 
 # if ----> si
# elif ----> sinon si 
#else -----> c pour le dernier cas (sinon)
# exemple 
degree = 123
if degree >= 100:
    print ("l'etat de l'eau est vapeure ")

elif 0 < degree < 100 : 
         print ("l'etat de l'eau est l'equide ") 
else:
       print ("l'etat de l'eau est solide ")

# l'operateure match 

error = 300
match error:
       case 400:
              print ('error vaut 400')
       case 300:
              print ('error vaut 300')
       case 200:
              print ('error vaut 200')
       case _:
              print ('on connait pas la valeure de la variable error ')
# match elle represente on algorithmique selon faire elle consiste a distinguer les cas:

# l'operateure ternaire:
#  l'instruction 1  if ( la condition)   else l'instruction 2
 # on execute l'instruction 1 si la condition est verifie  sinon on execute l'instruction 2
 #exemples :
age = 18
print (" tu es major ") if age >= 18 else print ("tu es minor")

age = age or 19 
adulte = age >= 18 or False
print (adulte)

# la boucle  for  , pour le type set on peut pas citer la meme valeure deux fois , python il va l considere q'une seule fois 
#ona la variable item

for item in [1 , 2 , 3, 4, "bonjour", True ]:
   for a in {1,2,3,True}:
         print (a,item)


print ("hello")  
for item in [1 , 2 , 3, 4, "bonjour", True ]:
   for a in {1,2,3,True}:
         print (item,a)
        


for i in range(10):
      print (f"Decolage dans { i } secondes")


my_range = list(range (10,2,-2))
print (my_range)  


for i in my_range:
      print ("bonjour")

for char in "bonjour" :
      print (char)

for char in enumerate ("bonjour") :
      print (char)

for char in enumerate ("bonjour") :
      print (char[0])

for char in enumerate ("bonjour") :
      print (char[1])

for char in enumerate ("bonjour") :
      print (char[0],char[1])
for index,valeur in enumerate ([True , "hello"]):
      print (valeur,index) 

my_tuple = (1,4,6)
counter = 0
for b in my_tuple:
      counter =counter + b 
print(counter)
               
value = input ('veullez entrer votre age : ') 
while int(value) <= 18 :
      value = input (" veullez entrer votre age : ") 
    
# break, continue et pass , l'instruction break permet de sortir dans une boucle , l'instruction continue permet de revenir au
#debut de la boucle et verifie la condition , l'instruction pass permet de contiuer a autre bloc d'instructions 

# les nombres entiers :

print (int ('111', base = 2)) 
# une autre natation
print (int('0B111' , 0))
# base 8 
print (int ('74' , base = 8))
print (int ('0O74' , 0))
# base 16 
print (int ("456" , base = 16))
print (int('0x456' , 0))
# quelque fonctions de laguage de programmation python 
# abs , min , min  ,max , pow , round , bin , hex 
print (abs(-4))
print (min ([ 2, 3, 5, 7.5]))
print (max ([ 12, 2, 5, 57, 102]))
print (pow(5 , 2))
print (round (2.7))
print (12 << 1) # elle transforme le nombre 12 binaire puis elle fais un decalage de bits a gauche selon le nombre designee 
# puis elle le transforme on decimal 
print (12 >> 1)  # la meme choose mais le decalage sa sera a droite 
print (bin(12))
print (hex(16))

greeting = ("bonjour   {name}  vous avez  {age}  ans").format( name = "moumouh"  ,  age = 19  )
print (greeting)
name = "moumouh"
age = 19
c = ("bonjour   {}  vous avez  {}  ans").format( name , age )
print (c)
nom = "moumouh"
years = 20
d = ("bonjour"  + " " + nom + " " +  "vous avez"  + " " +  str (years)  +  " " + "ans")
print (d)
a = "123";int (a);print (a)
a = "bonjour le monde !"
print (a[0:7])
print (a[7:])
print (a[ : : 2])
print (a[2:9:1])
print (a[ : : -1]) # pour inverser une chaine de caractere 
print (a[-1 : : -1])# pour inverser une chaine de caractere 
print (len("bonjour"))










