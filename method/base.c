#include <stdlib.h>
#define INF 0x7FFFFFFF

//n:num of items
//c:capacity
//price[1~n]:profit
//weight[1~n]:weight
int base(int n,int c,int* price,int* weight)
{
    //table[i][j] max price using item 1~i with capcity j
    int** table=(int**)malloc(sizeof(int*)*(n+1));
    for (int i=0;i<=n;i++)
        table[i]=(int*)malloc(sizeof(int)*(c+1));

    //base case: 
    //no item selected;
    //capacity is zero
    for (int i=0;i<=c;i++)
        table[0][i]=0;
    for (int i=0;i<=n;i++)
        table[i][0] = (weight[i]==0)?price[i]:0;

    for (int i=1;i<=n;i++)
    {
        for (int j=1;j<=c;j++)
        {
            //case 1: Max value is acieved by prior (i-1) items
            int o1=table[i-1][j];

            //case 2: Max value is acieved by i-th item & max vlaue of the prior (i-1) item with max capacity (j-weight[i]) 
            int o2=(j-weight[i] >= 0)?table[i-1][j-weight[i]] + price[i]:-INF;

            //set max value the bigger one
            if (o2 > o1)
                table[i][j]=o2;
            else 
                table[i][j]=o1;
        }
    }

    int re=table[n][c];
    for (int i=0;i<=n;i++)
        free(table[i]);
    free(table);

    return re;
}
