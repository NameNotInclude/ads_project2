#include <stdlib.h>
#include "dominance.h"

static node* merge(node* L1,int n1,node* L2,int n2,int* n3)
{
    int r=0;
    node* result=(node*)malloc(sizeof(node)*(n1+n2+1));

    int i=1,j=1;

    while (i <= n1 || j <= n2)
    {
        //Extract the lighter one
        node s;
        if (j > n2 || (i <= n1 && L1[i].weight <= L2[j].weight))
            s=L1[i++];
        else
            s=L2[j++];

        //The result list is empty, add it
        if (r == 0)
            result[++r]=s;

        else
        {
            node last;
            last=result[r];

            //case 1: s is dominated by last, simply skip
            if (s.price <= last.price)
                continue;
            //case 2: same weight but larger profit, substitude last with s
            else if (s.weight == last.weight)
                result[r]=s;
            //case 3: no one dominates the other, add it to list
            else
                result[++r]=s;
        }       
    }
    *n3=r;

    return result;
}  

int dpwithlist(int n,int c,int* price,int* weight)
{
    node* L1=(node *)malloc(sizeof(node)*(n+1));
    L1[1].weight=0;
    L1[1].price=0;
    int n1=1;

    //i means using item 1~i to construct the list
    for (int i=1;i<=n;i++)
    {
        node* l=(node*)malloc(sizeof(node)*(n1+1));
        int n2=0;

        //situation: use item number i
        for (int j=1;j<=n1;j++)
        {
            //exceed the capacity, break
            if (L1[j].weight + weight[i] > c)
                break;

            l[++n2].price = L1[j].price + price[i];
            l[n2].weight = L1[j].weight + weight[i];
        }

        //To constuct possible state of level i, there are two cases
        //case 1: using prior (i-1) item
        //case 2: using item i
        int n3;
        node* L3=merge(L1,n1,l,n2,&n3);

        //update list from level i-1 to i
        free(L1);
        L1=L3;
        n1=n3;
        free(l);
    }

    int re=L1[n1].price;
    free(L1);

    return re;
}
