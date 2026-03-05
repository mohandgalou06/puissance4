#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "fonctions.h"
  int sum_decroissant (int n){
   if (n==1){
   return 1;
   }else{
    return (n+sum_decroissant(n-1));
    }
    }
    int pgcd (int i,int j){
     if (i%j==0){
       return j;
       }else{
        return pgcd(j,i%j);
        }
        }
    int ppp (float a, float b){
     if (b==0){
       return 1;
       }else{
        return (a * (puissance(a,b-1)));
        }
        }
        int puissance(int x, int n) {
    if (n == 0) { // Cas de base : x^0 = 1
        return 1;
    }
    else if (n % 2 == 0) { // Si n est pair
        int y = puissance(x, n / 2); // Calcul de x^(n/2)
        return y * y; // x^n = (x^(n/2))^2
    }
    else { // Si n est impair
        return x * puissance(x, n - 1); // x^n = x * x^(n-1)
    }
}
        int dec_to_bin(int a){
        int c;
        if ((a/2)==0){
            return a%2;
        }else {
        return a%2+10*dec_to_bin(a/2);
                }
        }
        void montee(int n){
          if (n>0){
             montee(n-1);
             printf ("%d",n);
         }
         }

