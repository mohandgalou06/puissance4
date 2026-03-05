print (" i love python ");print (" i love programing")
  # this is a comments
print (type(100)) ; print (type(100.9))
print (type([1,2,3,4,5,6,7,8,9]))
print (type("hello"))
print (type((1,2,3,4)))
print (type({ "one" : 1, "two":2, "three":3 }))
print (2==4)#booleen value 
print (type(2 == 4)) # booleen
 # variables should be :
  # not start with a special caractere or num
  # we can use un num when we write a var as mou4mouh but we can not use a special caractere 
   # as mou-mouh    
    #we can not write the variables on other way maj/min or min/ maj // on garde la variable 
  # comme elle est 
mouh = (" hello world ")
print ( mouh ) 
a,b,c = 1,2,5
print (a,b,c)
print (a)
print (b)
print (c)

#escape sequences characteres
 # back space
print ("hello\bworld")
# escape new line + back slash 
print ("hello\
 i love\
 python")
# escape back slash
# back slash\\")
# escape single quote
print ('i like boxing\'mohammed ali \' ')
# escape double quote  
print ("i like boxing\"mohammed ali \"")
 # line feed 
print ("hello world\nsecond line")
#carriage return 
print ("123456789\rabcd")
print ("abder\r1527")
 # horizontal tab 
print ("hello\tpython")
# charactere hex value
print ("\x6d\x6f\x75\x6d\x6f\x75\x68") 
 # conatination -------

msg=" i like"
lois="practice sport"
print (msg + " " + lois)
print ( msg + "\n" + lois )
# deuxieme methode 
full=msg + " " +lois 
print (full)
a = "first \
second\
third"
b="A\
B\
C"
print (a); print (b)
# strings ------>
mystringone = 'this is single quote'
mystringtwo = "this is double quote" 
mystringthree = 'this is single quote "Test"'
mystringfour = "this is single quote 'Test'"
print (mystringone)
print (mystringtwo)
print (mystringthree)
print (mystringfour)
mystringfive=('''first
second
third''')
mystringsix=("""first 
second 
third""")
print(mystringfive)
print(mystringsix)
# indexing ( access single item)
mystring= "ilovepython"
print (mystring[4]) # index 4 ---> v
print (mystring[2]) # index 2 ---> l
print (mystring[-1]) # first charactere from end 
print (mystring [-2]) # second charactere from end 

#slicing (access multiple sequence items)
# [ start:End]
# [start:End:steps]
print (mystring [4:6])  
print (mystring[:10])
print (mystring [6:])
print (mystring[:])#full data
print (mystring[0::1])#full data 
print (mystring[::1]) #full data
print (mystring[::2])
print (mystring[::3])
# --- string methods ---
a = "        i love python   "
print (len(a))
# strip () rstrip() lstrip()
print (a.strip())
print (a.rstrip())
print (a.lstrip())
print (len(a.lstrip()))
print (len(a.rstrip()))
b = " ----- i love python ---"
print (b.strip("-"))
print (b.rstrip("-"))
print (b.lstrip("-"))
# title()
l = "I Love 2d Graphics and 3g Technology and python"
print (l.title() )
#capitalize 
h= " I Love 2d Graphics and 3g Technology and python"
print (l.capitalize())
#zfill
c, d, e, f = "1", "11", "111", "1111"
print (c.zfill(5))
print (d.zfill(5))
print (e.zfill(5))
print (f.zfill(5))
# upper 
g = "osama" 
print (g.upper())
# lower
g = "OSama"
print (g.lower())

# split 
a = "I Love python and PHP" # la fct split devise la phrase selon l'espace q'on a fait 
print (a.split())  
b = "I-Love-python-and-PHP-and-MySQL"
print (b.rsplit("-", 3))
# center ()
e = "osama"
print (e.center(7))   #hashes 
print (e.center (9, "#")) #hashes
print (e.center (9, "@")) #hashes


# count ()
f = "i love python and php because php is easy"
print (f.count("php"))# 2 php words  
print (f.count("php",0,25)) # only one php word 

  # swapcase ()
g = "I Love Python"
h = "i lOVE pYTHON" 
print (g.swapcase())
print (h.swapcase())

 # startswith()

i = "I Love python"
print (i.startswith("I"))  # true 
print (i.startswith("v"))   # false
print (i.startswith("p",7,12))


# endswith()

j = "I Love python"
print (j.endswith("n"))  # true 
print (j.endswith("s"))   # false
print (j.endswith("e",2,6) ) # true 

# index(substring, start, end)
a = "I Love python"
print (a.index("p")) # index number 7
print (a.index("p", 0, 10)) # index number 7
#print (a.index("p", 0, 5)) # through error 


b = "I Love python"
print (b.find("p")) # index number 7
print (b.find("p", 0, 10)) # index number 7
print (b.find("p", 0, 5)) # through error 

# rjust() ljust ()
c = "osama"
print (c.rjust(10))
print (c.rjust(10,"#"))
print (c.ljust(10))
print (c.ljust(10,"#"))

# splitlines()
e = """first line 
second line
third line"""

print (e.splitlines())

f="First Line\nsecond Line\nThird Line"
print (f.splitlines)
# expandtabs()
g = "Hello\tworld\tI\tLove\tPython"
print (g.expandtabs())
print (g.expandtabs(3))
print (g.expandtabs(15))
one = "I Love Python And 3G"
print (one.istitle())
two = "I Love Python And 3g"
print (two.istitle())
three = " "
four = ""
print(three.isspace())
print (four.isspace())
five = 'i love python'
six = 'I Love Python'
print (five.islower())
print (six.islower())
seven = "osama_elzero"
eight = "osamaElzero100"
nine = "osama--Elzero100"

print (seven.isidentifier())
print (eight.isidentifier())
print (nine.isidentifier())

x = "AaaaaBbbbb"
y = "AaaaBbbbb111"

print (x.isalpha())
print (y.isalpha())

u = "AaaaaBbbbb"
z = "AaaaBbbbb111"
print (u.isalnum())
print (z.isalnum())

# replace(old value, New value, count)
a = "Hello One Two Three One One "
print (a.replace("One", "1"))
print (a.replace("One", "1", 1))
print (a.replace("One", "1", 2))

#join(Iteerable)

mylist = ["Osama", "Mohamed", "Elsayed"]
print (" - ".join(mylist))
print (" , ".join(mylist))
print (" ".join(mylist))
print(type(",".join(mylist)))