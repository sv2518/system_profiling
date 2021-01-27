#define _GNU_SOURCE

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <sched.h>
#include <omp.h>

void get_num(int *thread_num, int *cpu_num);

int main(int argc, char **argv){
    int n, ii;
    int *thread_num, *cpu_num;

    n = omp_get_max_threads();
    printf("%d\n", n);
    thread_num = malloc(sizeof(int)*n);
    cpu_num = malloc(sizeof(int)*n);

    for(ii=0; ii<n; ii++){
        thread_num[ii] = -1;
        cpu_num[ii] = -1;
    }


    get_num(thread_num, cpu_num);

    for(ii=0; ii<n; ii++){
        printf("Thread %3d is running on CPU %3d\n", thread_num[ii], cpu_num[ii]);
    }
    return EXIT_SUCCESS;
}

void get_num(int *thread_num, int *cpu_num){
    int n, threadn;
    int64_t ii;
    int64_t big = 1024*1024*16; /* Need big int */
    double *work;

    n = omp_get_max_threads();
    work = malloc(sizeof(double)*n*big);

    #pragma omp parallel private(ii, threadn)
    {
        threadn = omp_get_thread_num();
        for(ii=0; ii<big; ii++){
            work[threadn*big + ii] = ((double) ii)*((double) ii) / (double)big;
        }

        thread_num[threadn] = threadn;
        cpu_num[threadn] = sched_getcpu();

        for(ii=0; ii<big; ii++){
            work[threadn*big + ii] /= (double) ii + 1.0;
        }
    }
}
