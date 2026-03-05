# exo 1 : pair ou impair 
"""
def pair_impair(a)->bool :
  if (a % 2 == 0):
        return True 
  else :
        return False
  
b =int(input("entrer un entier positif : ")) 
pair = pair_impair(b)
if (pair == True):
     print ("le nombre que vous avez entrer est pair ")
else :
     print (" le nombre que vous avez entrer est impair")
"""
# exo : un programme qui parcours et affiche tous les caracteres d'une chaine de caractere 


"""
ch = input(" entrer votre chaine de caractere ")
for caractere in iter (ch):
     print (caractere)
# comme ca on peut voir la difference entre enumerate est iter
for caractere in enumerate (ch):
     print (caractere)
"""
# ecrire un programme qui calcule le nombre d'apparition de chaque caractere dans la chaine de caractere 
ch = str(input(" entrer votre chaine de caractere "))
m = len(ch)
for caractere in iter (ch) :
 print (type(caractere))
 d = str(caractere)
 c =  ch.count(d) 
 print (f"le nbr d'occurence de caractere {caractere} dans la chaine de caractere est : " )
 print (c)    




def bessixtile ():
 annee = int(input("entrer une annee : "))
 if (annee % 4 == 0 and annee % 100 != 0):
    print("l'annee {0} est une annee bessixtile".format(annee));
 elif (annee % 400 == 0):
   print("l'annee {0} est une annee bessixtile".format(annee));
 else:
    print(f"l'annee {annee} n'est pas une annee bessixtile");
  
bessixtile()