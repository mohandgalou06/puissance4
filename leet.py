
# Definition for singly-linked list.
# class ListNode(object):
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
# un programme qui calcule la somme de deux liste qui ont une meme taille mais cette somme est de gauche vers la droite (inverser)
# c pas une somme normale de droite vers la gauche comme ona l'habitude de faire 
"""   
class Solution :
    def addTwoNumbers(self, l1: list, l2 :list)-> int :
     d ,s , c = 0 , 0 , 0 
     i , j = 0, 0     
     while i < len(l1) and  j < len(l2) :
          
          d = (c + l1[i] + l2[j]) % 10;
          c = (c + l1[i] + l2[j]) // 10;
          if ( i ==len(l1)-1 and j == len(l2)-1):
               if (c != 0):
                s = s * 10 + c
                i = i + 1
                j = j + 1
               else:
                i = i + 1
                j = j + 1
                continue     
          else :       
               s = s * 10 + d
               i = i + 1;
               j = j + 1;
        
             
     if i ==len(l1) or j == len(l2):
              s = s * 10 + d
     return s  
  

# Exemple d'utilisation
e = int(input (" entrer la taille de votre liste"))

ma_list = []
ma_list2 = []
i = 0 
while i < e:
     try:
        element = int(input("Entrez un nombre inférieur à 10 pour la premiere liste : "))
        element2 = int(input("Entrez un nombre inferieure a 10 pour la deuxieme liste: "))
        if element < 10 and element2 < 10:
            ma_list.append(element)
            ma_list2.append(element2)
            i = i + 1
        else:
            print("Le nombre doit être inférieur à 10. Veuillez réessayer.")
     except ValueError:
        break  # Si l'utilisateur entre quelque chose qui n'est pas un nombre, la boucle se termine

   
instance_solution = Solution()
result = instance_solution.addTwoNumbers(ma_list , ma_list2)
print (ma_list)
print (ma_list2)
print (" voici la somme des deux liste : ")
print(result)
"""
""" un programme qui calcule l'inverse d'un nombre : 
class Solution:
    def reverse(self, x):
     s = 0 ; d = 0
     if ( x != 0 ):    
        while x != 0: 
         s = x % 10
         x = x // 10
         d = d * 10 + s
     return d
a = int(input (" entrer la  votre nombre : "))
inverse = Solution()
resultat = inverse.reverse(a)
print("voici l'inverse de votre nombre :")
print(resultat)    
 """
class Solution :
    def lengthOfLongestSubstring(self, ch)-> int :
       j = 0
       s = " "
       for indice , caractere  in enumerate(ch) :
            if (indice == 0):
                s = s + caractere
                j = j + 1
            else:
              trouve = False
              for iteration , value  in enumerate(s) :
                 if (caractere == value):
                     trouve = True

                 if (trouve == True):
                     break; 
                 else :
                    continue;
              if (trouve == False):
                   s = s + caractere
                   j = j + 1        
       return j      
ch = str(input("donner la chaine de caractere et nous retournons sa taille sans considerer les repetitions des caracteres :"))          
a = Solution()
nbr = a.lengthOfLongestSubstring(ch)
print ("voici la taille de votre chaine de caractere sans considerer les repetitions des caracteres :")
print (nbr)

