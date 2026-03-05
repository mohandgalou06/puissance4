#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

int main(){
 int n,s,c;
 int i,j;
 int  a,b;
printf ("entrer un entier n :\n");
scanf ("%d",&n);
s=sum_decroissant(n);
printf ("la somme des nombres de 1 a %d est %d \n:",n,s);
printf ("entrer deux nombres a calculer leur pgcd : \n");
scanf ("%d",&i);
scanf ("%d",&j);
c=pgcd(i,j);
printf ("le pgcd des deux nombres est : %d \n",c);
 printf ("on va calculer a puissance b , entrer a et b \n");
  scanf ("%d",&a);
  scanf ("%d",&b);
  c=puissance (a,b);
  printf (" la valeure de %d puissance %d est %d \n", a,b,c);
  printf (" entrer un entier en decimal \n");
  scanf("%d",&a);
  printf ("voici votre entier en binaire \n");
   c=dec_to_bin(a);
    printf ("%d \n",c);
    printf (" entrer un entier \n");
     scanf("%d",&a);
      montee(a);

 return 0;
}
