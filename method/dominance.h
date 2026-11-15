#pragma once

//List <w,p> to store the situation
//For <w,p> & <w',p'>
//If w<=w' & p>=p', and at least one inequality sign is  strict, we call it <w,p> dominates <w',p'>
//In list[1~n], list[i].weight < list[j].weight for every i<j, and no node dominates the other
//Weight of any node is less than c
typedef struct 
{
    int weight;
    int price;
}node;

node* merge(node* L1,int n1,node* L2,int n2,int* n3);

int dpwithlist(int n,int c,int* price,int* weight);
