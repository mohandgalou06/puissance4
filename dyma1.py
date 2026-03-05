# introduction aux  tuples
a = (1 ,2 ,3)
print (a[0]) ; # mais on peut pas modifie une valeure car il est de type immuable(tuple)
# a[0] = 'c' --> faux 
b = (4 ,5 ,6) ; c = a[0:2] ;print (a+b) ;  print (c)
d = (1 ,2 ,3) ; print (id(a)) ; print (id(d))
h = tuple("hello") ; g = tuple (range(4)) ; print (h) ; print (g)
a = (1 ,2 ,3 ,4 ,2 ,5 ,6 ,3 ,2)
print (a.index(2)) ; print (a.count(2)) ; # si on a fais print (a.index(9)) il va nous afficher une erreure car 9 n'existe pas dans 
# le tuple , mais avec la condition on peut afficher une instruction qui dit que 9 n'existe pas dans le tuple
if ( 9 in a) :
     print (" ok ")
else :
      print (" 9 n'existe pas dans a") 
# on peut utiliser cette methode pour s'avoir si une valeure existe dans le tuple ou bien la methode count() le nbr de repetition d'une val
      if ( 3 in a) :
         print (" 3 existe dans a")
      else :
        print (" 3 n'existe pas dans a") 
# introduction aux set
a = {1, 3, 6, 5, 2, 1, 7} ; # on peut pas parcourir un set ex: print (a[2]), il nous affiche erreure 
print (a) , #on peut pas afficher une valeure 2 fois python va l considerer juste une seule fois , set vers liste :
print (list(a)) ; print (tuple (a)) ; b = [1, 3, 7, 8, 7, 2, 3] # list vers set 
print (set(b)) ; h = set() ; print (h) # la recherche d'une val dans un set
print ( 6 in a); # methode pour les sets : 
b = a.copy() ; print (a) ; print (b) ; print (id(a)); print (id(b)) # on aura le meme affichage mais pas la meme reference 
a.add(1000); print(a) ; a.remove(1000) ; print (a) ; # si ona fais a.remove (val n'existe pas dans set) il nous affiche
# un message d'erreure mais avec la methode discard il nous affiche pas un message d'erreure # exemple 
a.discard (57) ; print (a); a.discard (5) ;print (a) # valeure existe c comme remove  
c = {1, 2, 3, 6, 7, 8} ; c.add(100) ; print (c) 
b = c.pop() ; print (b) ; print (c) ; d = c.pop() ; print (d) ; print (c) # la methode pop permet de supprimer un element quelconque 
# dans le set et le retourner dans une autre variable c on veut 
c. update ({"A" , "b" , 89}) ; print (c) # la methode update permet de modifier notre set on l'ajoutant des elements 
# comparaison des sets 
a = {1, 2, 3, 6, 7, 8} ; b = {3, 6, "A", 'b'} ; c = a.intersection(b) ; print (c)  
a.intersection_update(b) ; print (a) # avec intersection_update on aua le resultat dans a donc sa devient a = {3,6}
a = {1, 2, 3, 6, 7, 8} ; c = a.union(b) ; print (c) ; d = a | b ;print (d) # | represente union
c = a.difference(b) ; print (c) # les elements de a qui ne sont pas dans b
a.difference_update(b) ; print (a) # la meme choose que update mais le resultat sera affiche dans a sera a = {1, 2, 7, 8}
c = a.isdisjoint(b) ; print (c) ; a = {1, 2, 3, 6, 7, 8} # ona modifier la val de a 
c = a.isdisjoint(b) ; print (c) 
c = a.issubset(b) ; print (c) ; # il nous affiche false ; a.issubset(b) c a d est ce que a est inclus dans b
h =  {3, 6} ; c = h.issubset(b) ; print (c) ; # il nous affiche true 
c = b.issuperset(h) ; print (c) # c comme q on a dit c = h.issubset(b) 
# b is superset(h) c a d est ce que b contient tout les elements de h
                                                                           
print ("chapitre 9 , bienvenue au projet ");
import random
# preparationn de l'algorithme de jeu

print ('cree par moumouh galou')
words = "non moumouh toile sans espoir bilouche colonne vertebrale kiki pare-chocs francais bobine drone"
words_list = words.split()
secret = random.randint(0,len(words_list)-1)
secret_words = words_list[secret]
game = {
    "secret_word" : secret_words ,
    "guess_word" : "-" * len(secret_words),
    "life" : 7
  }
print (f"{game ['guess_word'] } | vie : {game ['life'] }")
while True :
       letter = input('? > ')
       if letter in game['secret_word'] and letter not in game['guess_word'] :
          guess_word_list = list(game['guess_word'])
          for index , current_letter in enumerate(game['secret_word']):
               if current_letter == letter :
                   guess_word_list [index] = letter
               game['guess_word']= "".join (guess_word_list)            
       elif letter not in game['secret_word'] :
           game['life'] -= 1
       print (f"{game ['guess_word'] } | vie : {game ['life'] }")
       if "-" not in game["guess_word"] :
          print ('gagne !')
          break
       elif game['life'] < 1:
          print ("perdu")
       break

# finalisation de jeu 
print (" le chapitre des fonctions ")
def myfunc(a , b):             
    c = a+b  
    return (c)
b = myfunc ;print(b) ;print (b ( 3 , 4 ))# on peut passer juste un seule valeure lorsque on appel la fonction mais a condition que
# on definer la 2 eme valeure dans la fonction (supposons que la fonction contient 2 parametre ) exemple :
print (" parametre et arguments ")
def func (a , b=3):
    return a+b
print (func (5)) # elle nous affiche 8 : # on peut declarer une fonction sans parametres 
def sans_para () :
    print (" my name is moumouh galou ")
sans_para();sans_para();sans_para();sans_para()

def greeting (firstname , lastname ):
    print (f"bonjour {firstname} {lastname}")

greeting ('galou' , 'moumouh')
greeting (lastname="galou" , firstname="moumouh") # sa fonctionne , mais c ona fait :
# greeting ('galou ' , firstname = 'moumouh') # erreure car le parametre firstname aura 2 valeur et ca se fait pas (c a d impossible)
greeting ('galou' , lastname = "kiki")
#greeting (firstname = 'galou' , 'moumouh') # erreure lorsque on fais parametre = ???? , il faut que tout les valeurs qui sont apres
# la valeure ???? on va les appeler par : parametre 1 = 2????? 
b = [1,2] ; a = [1,2] ; print (a is b); c = b ; print (c) ; print (c is b) ; print (" passer des valeursdynamique aux fonctions")
print (" la types mutables et immuables sur les fonctios") ; print ("immuables : ")
a = 1
def mysum (b) :
  print (a is b)
  b = 2
 print (a is b)

mysum(a) ; print (" mutables :")
a = [1,2]
def my_sum(b) :
    print (a is b)
    b.append("hello")
    print (a is b)
    print (a)
    print (b)
my_sum(a)

print (" passer un nombre indefini d'arguments")

def sum_everything (c , *args) :
    print (c)
    print (args)
    print (sum(args)) # la somme de l'ensemble de valeure qui sont dans args ; voici la deuxieme facon pour afficher la somme 46
    total = 0
    for n in args :
      total = total + n
    print (total) # meme choose total = 46

sum_everything(1,2,3,4,5,6,7,9,10) # le premier parametre prend la 1 er valeur , c on veut donner beaucoup d'arguments 
#  a une variable , on va definer la variable par *nom de variable c a d la variable prend beaucoup de valeure 
 # def sum_everything (*args , factor) :
  #      print (c)
    # print (args)
     #print (sum(args)) 
    # total = 0
   #  for n in args :
    #   total = total + n 
    # print (total) 

 #sum_everything(1,2,3,4,5,6,7,9,10) comme ca elle ne fonctionne pas (erreure) car tout les valeurs sont stocke dans args , factor
 # n'aura pas de valeure
   
def somme ( *args , factor) :
    print (factor)
    print (args)
    print (sum(args)) # la somme de l'ensemble de valeure qui sont dans args ; voici la deuxieme facon pour afficher la somme 46
    total = 0
    for n in args :
      total = total + n
    print (total) # meme choose total = 46
somme(1,2,3,4,5,6,7,9,10 , factor = 7) # comme ca ca fonction puisque ona donner une val pour factor

def fonction( val,*args ,**kwargs) : # **kwargs elle regroupe les arguments nomee de type dict
    print (val)
    print (args)
    print (sum(args)) # la somme de l'ensemble de valeure qui sont dans args ; voici la deuxieme facon pour afficher la somme 46
    print (kwargs)
      
fonction (1,2,3,4,5,6,7,9,10 , nom='galou' , prenom='moumouh' , bac = 16.46) 
# les fermetures 
def power_factor(power):
    def power_by(number):
        return number ** power
    return power_by
power_by_2 = power_factor(2)
print (power_by_2(2)) ;  print (power_by_2(3))
power_by_3 = power_factor(3)
print (power_by_3(2)) ;  print (power_by_3(3)) ; print (power_by_3(4))

def foo() :
    arr = []
    for item in range (3) :
        def display() :
            print (item)
        arr.append(display)
    return arr  
a = foo()
a[0]() # il affiche la derniere trace de item 
a[1]() # il affiche la derniere trace de item 
a[2]() # il affiche la derniere trace de item 

print ('my name is nabil' )
# c on fait :  exemple a = 1
# def foo() :
 # a += 1 ; print (a)
 # foo() ; il nous affiche une erreure ;  la correction comme ca 
a = 1
def foo():
  global a ;a += 1 ; print (a)
foo() 
# def foo():
#  a = 2
#  def fun() :
#    a += 1 ; print (a)
  # fun() on aura uune erreure , voici la correction 

def foo():
   a = 2
   def fun() :
      nonlocal a 
      a += 1  
      print (a)
   fun()
foo()   
def func():
    total = 0
    def fon():
        nonlocal total
        print (total)
        total += 1
    return fon
a = func()
a()
a()
a() 
#                     ou
# def addition(a: int | str , b: int | str ) -> int 
from typing import Any 
def addition_plus_one (a : int , b: int ) -> any:
    def addition():
        return a+b+1
    return addition 
b = addition_plus_one(3,5) ; print (b)

def addition (a:int , b:int ) -> int :
     '''
     info: you should invoke this function with some numbers   
      '''
     return a+b
addition(1,2) ; help(addition) 
print(addition._doc_)


