# le chapitre 16 
from datetime import time, date, datetime 
from dateutil import tz
print (" le cour est la clsse time ")   
a = time(6 , 5 ,2 , 5) ; print (a)# heure , minute , secondes , micro secondes , c je ne declare pas 
#une information elle sera pas afficher mais on aura pas d'erreure 
print (type(a)) ; b = time.fromisoformat('18:00:02') ; print (b) ; print (type(b)) ; 
print (b.hour) ; print (b.minute) ; print (b.second) ; print (b.microsecond)
print (b.max) # il s'agit de max de temps dans la journee 23:59:59.999999
print (b.min) # il s'agit de min de temps dans la journee 00:00:00
c = b.replace (minute = 15) ; print (c) ; print (" le cour est la classe date ")
d = date (1920 , 2 , 1) ; print (d) ; e = date.today(); print (e) 
f = date.fromisoformat('2022-06-11') ; print (f)
i=date.fromtimestamp(445678934); print (i) # le timestamp compare par rapport a 1970-01-01,on donne la val on sec
print(i.isocalendar()) ; print (i.isoweekday()) ; print (i.timetuple()) 
print (i.timetuple()[1])
print (i.toordinal())# recuperer le nombre de jours depuis timestamp'1970-01-01'
print (i.strftime('%A %d %B %Y')); # on affiche la date de ce jour 
j = (i.toordinal() - date(1970,1,1).toordinal())*24*60*60  ; print (j)
k = date.fromtimestamp(j) ; print (k)
m = datetime(1960, 6, 8); print (m)
l = datetime.today() ; print (l) 
l = datetime.now() ; print (l) 

 