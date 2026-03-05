# mini projet jeu de Morpion
map = [
    [' . ' , ' . ' , ' . ' ],
    [' . ' , ' . ' , ' . ' ],
    [' . ' , ' . ' , ' . ' ],
]

player = 'joueur1'
def draw ():
  for i in range (3) :
     for j in range (3):
        print (map[i][j],end="")
     print()
def check_win()-> bool :
   for i in range (3):
       if  map[i][0] == map[i][1]== map[i][2] != ' . ' :
             return True 
   for i in range(3) :
       if map [0][i] == map[1][i] == map[2][i] != ' . ':
            return True 
   if map [0][0] == map [1][1] == map [2][2] != ' . ':
            return True     
   if map [0][2] == map [1][1] == map [2][0] != ' . ':
            return True 
   return False
i = 0      
while True :
   choice = int(input(f'{player} [1-9] > ? '))
   row = (choice - 1) // 3
   column = (choice - 1) % 3
   if map[row][column] == ' . ' :
      map[row][column] = ' x ' if player == 'joueur1' else ' o '
      draw()
      player = 'joueur1' if player == 'joueur2' else 'joueur2'
      i = i+1; 
      a = (check_win())
      print (check_win())
      if (a == True) :
         if (player == 'joueur1') :
                print (" le gagnant est le joueur 2")
                break;
         else :
                   print (" le gagnant est le joueur1")
                   break;
      elif (i == 9) and (a != True ):
             print (" le match est null ")
             break;

print (" le deuxieme jeux ")                          


from random import randint 
nbr = randint (1,100)                
nbr_of_try = 0
class number_to_big_error(Exception):
   def __init__(self ,message,nbr_secret):        
    self.message = message;
    self.nbr_secret = nbr_secret
   def __str__(self):
      return f"{self.message}:{self.nbr_secret}"
class number_to_small_error(Exception):
 def __init__(self , message,nbr_secret):        
    self.message = message;
    self.nbr_secret = nbr_secret;
 def __str__(self):
      return f"{self.message}:{self.nbr_secret}"
def fun(nbr):
    if nbr == nbr_secret :
         print (" Bravo tu as gagne ") 
    elif nbr > nbr_secret:
          raise number_to_big_error("le nombre est trop grand paraport a" ,{nbr_secret})
    else :
          raise number_to_small_error("le nombre est trop petit paraport a" ,{nbr_secret})
        
while True :
   try :
    nbr_secret = int (input (" entrer un nombre  :  "))
   except ValueError:  
    print (" vous devez entrer un nombre ")
   else :  
    try:
       fun(nbr)
    except number_to_big_error as err :
       print (err)
    except number_to_small_error as err :
       print (err)
   finally:
      nbr_of_try += 1
 



