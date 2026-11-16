#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include "method/base.h"
#include "method/dominance.h"
#include "method/bounding.h"

static double now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1000000.0;
}

int main(int argc,char* argv[])
{
    FILE* read;
    read=fopen(argv[1],"r");

    int n,c;
    fscanf(read,"%d%d",&n,&c);

    char* check=argv[2];
    int iter=0;
    while (*check != '\0')
    {
        iter=iter*10+*check-'0';
        check++;
    }

    //price & weight are all 1 based
    int* price=(int*)malloc(sizeof(int)*(n+1));
    int* weight=(int*)malloc(sizeof(int)*(n+1));
    for (int i=1;i<=n;i++)
        fscanf(read,"%d %d",price+i,weight+i);

    int* temp_price=(int*)malloc(sizeof(int)*(n+1));
    int* temp_weight=(int*)malloc(sizeof(int)*(n+1));

    FILE* basef=fopen("result/base.csv","a");
    FILE* dominancef=fopen("result/dominance.csv","a");
    FILE* boundf=fopen("result/bound.csv","a");

    double start, end;
    double time_base=0,time_dominance=0,time_bound=0;
    int result1,result2,result3;
    for (int i=0;i<iter;i++)
    {
        start=now_ms();
        result1=base(n,c,price,weight);
        end=now_ms();
        time_base+=end-start;

        start=now_ms();
        result2=dpwithlist(n,c,price,weight);
        end=now_ms();
        time_dominance+=end-start;

        for (int i=1;i<=n;i++)
        {
            temp_price[i]=price[i];
            temp_weight[i]=weight[i];
        }
        start=now_ms();
        result3=dpbound(n,c,temp_price,temp_weight);
        end=now_ms();
        time_bound+=end-start;

        if (result1 != result2 || result1 != result3 || result2 != result3)
        {
            free(price);
            free(weight);
            free(temp_price);
            free(temp_weight);
            fclose(read);
            fclose(basef);
            fclose(dominancef);
            fclose(boundf);

            printf("Fatal error");

            return 1;
        }
    }

    fprintf(basef,"file,num_of_item,capacity,iter,tot_time,aver_time\n");
    fprintf(dominancef,"file,num_of_item,capacity,iter,tot_time,aver_time\n");
    fprintf(boundf,"file,num_of_item,capacity,iter,tot_time,aver_time\n");

    fprintf(basef,"%s,%d,%d,%d,%lf,%lf\n",argv[1],n,c,iter,time_base,time_base/iter);
    fprintf(dominancef,"%s,%d,%d,%d,%lf,%lf\n",argv[1],n,c,iter,time_dominance,time_dominance/iter);
    fprintf(boundf,"%s,%d,%d,%d,%lf,%lf\n",argv[1],n,c,iter,time_bound,time_bound/iter);

    free(price);
    free(weight);
    free(temp_price);
    free(temp_weight);
    fclose(read);
    fclose(basef);
    fclose(dominancef);
    fclose(boundf);

    return 0;
}