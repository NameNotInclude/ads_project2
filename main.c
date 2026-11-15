#include <stdlib.h>
#include <stdio.h>
#include "method/base.h"
#include "method/dominance.h"
int main()
{
    int n,c;
    scanf("%d%d",&n,&c);

    //price & weight are all 1 based
    int* price=(int*)malloc(sizeof(int)*(n+1));
    int* weight=(int*)malloc(sizeof(int)*(n+1));
    for (int i=1;i<=n;i++)
        scanf("%d %d",price+i,weight+i);

    int result=base(n,c,price,weight);
    printf("%d\n",result);

    result=dpwithlist(n,c,price,weight);
    printf("%d",result);

    free(price);
    free(weight);

    return 0;
}