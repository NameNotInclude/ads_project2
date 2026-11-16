#include <stdlib.h>
#include "dominance.h"

static void swap(int i,int j,double* per_price,int* price,int* weight)
{
    double temp=per_price[i];
    per_price[i]=per_price[j];
    per_price[j]=temp;

    int t=price[i];
    price[i]=price[j];
    price[j]=t;

    t=weight[i];
    weight[i]=weight[j];
    weight[j]=t;
}

//sift the element down inside the min-heap stored in per_price[base..base+size-1]

static void sift_down(int base,int size,int root,double* per_price,int* price,int* weight)
{
    while (1)
    {
        int child=2*root+1;
        if (child >= size)
            break;

        //choose the smaller child
        if (child+1 < size && per_price[base+child+1] < per_price[base+child])
            child++;

        if (per_price[base+root] <= per_price[base+child])
            break;

        swap(base+root,base+child,per_price,price,weight);
        root=child;
    }
}

//heap sort the range [left,right] in decreasing order of per_price
//price[] and weight[] are moved together with per_price[]
static void heap_sort(int left,int right,double* per_price,int* price,int* weight)
{
    int size=right-left+1;

    //build a min-heap bottom up
    for (int i=size/2-1;i>=0;i--)
        sift_down(left,size,i,per_price,price,weight);

    //the minimum goes to the end of the current heap, then shrink the heap by one
    for (int end=size-1;end>0;end--)
    {
        swap(left,left+end,per_price,price,weight);
        sift_down(left,end,0,per_price,price,weight);
    }
}

//Upper bound of the remaining items i+1..n with capacity r: the fractional knapsack
//Taking the fraction rounded down keeps it an upper bound, because the optimum is an integer
static int bound(int i,int r,int n,int* price,int* weight,int* Wsum,int* Psum)
{
    if (r <= 0)
        return 0;

    //binary search the largest t in [i,n] with Wsum[t]-Wsum[i] <= r
    int lo=i,hi=n,t=i;
    while (lo <= hi)
    {
        int mid=(lo+hi)/2;
        if (Wsum[mid]-Wsum[i] <= r)
        {
            t=mid;
            lo=mid+1;
        }
        else
            hi=mid-1;
    }

    int val=Psum[t]-Psum[i];

    //take a fraction of the next item
    if (t < n)
    {
        int rest=r-(Wsum[t]-Wsum[i]);
        val+=(int)((long long)rest*price[t+1]/weight[t+1]);
    }

    return val;
}

int dpbound(int n,int c,int* price,int*weight)
{
    double* per_price=(double*)malloc(sizeof(double)*(n+1));
    for (int i=1;i<=n;i++)
        per_price[i]=1.0*price[i]/weight[i];

    //sort items in decreasing order, according to the average price
    heap_sort(1,n,per_price,price,weight);

    int Wsum[n+1],Psum[n+1];
    Wsum[0]=0;
    Psum[0]=0;

    for (int i=1;i<=n;i++)
    {
        Wsum[i]=Wsum[i-1]+weight[i];
        Psum[i]=Psum[i-1]+price[i];
    }

    //greedy method to get the approximate solution
    int rest=c,z=0;
    for (int i=1;i<=n;i++)
        if (weight[i] <= rest)
        {
            rest-=weight[i];
            z+=price[i];
        }

    //DP-with-Lists (section 3.4): keep only the undominated states of every layer
    //L: states of the current layer, S: states where item i is taken
    node* S=(node*)malloc(sizeof(node)*(c+2));
    node* L=(node*)malloc(sizeof(node)*(c+2));

    L[1].weight=0;
    L[1].price=0;
    int len=1;

    for (int i=1;i<=n;i++)
    {
        //situation: use item number i
        int lenS=0;
        for (int k=1;k<=len;k++)
        {
            //exceed the capacity, break
            if (L[k].weight+weight[i] > c)
                break;

            S[++lenS].weight=L[k].weight+weight[i];
            S[lenS].price=L[k].price+price[i];
        }

        //To constuct possible state of level i, there are two cases
        //case 1: using prior (i-1) item
        //case 2: using item i
        int lenM=0;
        node* M=merge(L,len,S,lenS,&lenM);
        //update list from level i-1 to i
        free(L);
        L=M;

        //fathom the states whose upper bound cannot beat the incumbent z
        int keep=0;
        for (int k=1;k<=lenM;k++)
        {
            //improve the incumbent if it exceed the current optimal
            if (L[k].price > z)
                z=L[k].price;

            //check whether it's possible to reach the current optimal solution
            if (L[k].price+bound(i,c-L[k].weight,n,price,weight,Wsum,Psum) > z)
                L[++keep]=L[k];
        }
        len=keep;
    }

    int result=z;

    free(L);
    free(S);
    free(per_price);

    return result;
}
