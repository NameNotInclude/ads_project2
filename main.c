#include <stdlib.h>
#include <stdio.h>
#include "method/base.h"
int main()
{
    int n,c;
    scanf("%d%d",&n,&c);
    int* price=(int*)malloc(sizeof(int)*(n+1));
    int* weight=(int*)malloc(sizeof(int)*(n+1));
    for (int i=1;i<=n;i++)
        scanf("%d %d",price+i,weight+i);

    int** result=base(n,c,price,weight);
    printf("%d",result[n][c]);

    free(price);
    free(weight);
    for (int i=0;i<=n;i++)
        free(result[i]);
    free(result);
    return 0;
}