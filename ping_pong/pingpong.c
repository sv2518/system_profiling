#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <mpi.h>

#define BLOCK 1024
#define MAX_INT ( 1<<24 )

int32_t *empty_buff(int size);
void randomise(int32_t *buff, int size);
double *pingpong(int ping, int pong, int *message_sizes, int mslen, int repeats);

int main(int argc, char **argv){
    char processor_name[MPI_MAX_PROCESSOR_NAME];
    int name_len;
    int world_rank, world_size;

    int rank, ii, jj;
    int lens = 6;
    int reps = 20;
    double average = 0;
    double *results;
    int message_sizes[] = {1, 10, 20, 40, 70, 100};

    /* Seed RNG */
    srandom(111);
    /* Initialize the MPI environment */
    MPI_Init(&argc, &argv);
    /* Get the number of processes and rank */
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    /* Get the name of the processor/host */
    MPI_Get_processor_name(processor_name, &name_len);
    /* Display MPI info */
    printf("Host: %s Rank: %d/%d total\n", processor_name, world_rank, world_size);

    /* Do a ping pong rank 0 -> all other ranks */
    for(rank=1; rank<world_size; rank++){
        results = pingpong(0, rank, message_sizes, lens, reps);

        if(world_rank == 0){
            printf("(0->%d) ", rank);
            for(ii=0; ii<lens; ii++){
                printf("MS %d :", message_sizes[ii]);
                average = 0;
                for(jj=0; jj<reps; jj++){
                    average += results[ii*reps + jj];
                    // printf("%g\n", results[ii*reps + jj]);
                }
                average /= reps;
                printf("%g s ", average);
            }
            printf("\n");
        }
    }

    if(world_size > 1){
        free(results);
    }

    /* Finalize the MPI environment */
    MPI_Finalize();
    return EXIT_SUCCESS;
}

int32_t *empty_buff(int size){
    int ii;
    int32_t *buff;
    buff = (int32_t*)malloc(sizeof(int32_t)*size);
    assert(("Unable to malloc", buff != NULL));

    for(ii=0; ii<size; ii++){
        buff[ii] = 0;
    }

    return buff;
}

void randomise(int32_t *buff, int size){
    int ii;

    for(ii=0; ii<size; ii++){
        buff[ii] = random();
    }
}

double *pingpong(int ping, int pong, int *message_sizes, int mslen, int repeats){
    int ii, jj;
    int mesg_size, rank, size;
    int32_t *send, *recv;
    double t = 0;
    double *results;
    MPI_Status status;

    results = NULL;

    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);


    if(rank == ping){
        // Results array
        results = (double*)malloc(mslen*repeats*sizeof(double));
        assert(("Unable to malloc", results != NULL));

        for(ii=0; ii<mslen; ii++){
            // Malloc here
            mesg_size = BLOCK*message_sizes[ii];
            send = empty_buff(mesg_size);
            recv = empty_buff(mesg_size);

            for(jj=0; jj<repeats; jj++){
                // printf(".");
                randomise(send, mesg_size);
                t = MPI_Wtime();
                MPI_Send(send,
                         mesg_size,
                         MPI_INT32_T,
                         pong,
                         (10*mesg_size*ping + jj)%MAX_INT,
                         MPI_COMM_WORLD);
                // printf("!%d\n", (20*mesg_size*pong + jj)%MAX_INT);
                MPI_Recv(recv,
                         mesg_size,
                         MPI_INT32_T,
                         pong,
                         (20*mesg_size*pong + jj)%MAX_INT,
                         MPI_COMM_WORLD,
                         &status);
                results[repeats*ii + jj] = MPI_Wtime() - t;
            }
            // Free here
            free(send);
            free(recv);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }else if(rank == pong){
        for(ii=0; ii<mslen; ii++){
            // Malloc here
            mesg_size = BLOCK*message_sizes[ii];
            recv = empty_buff(mesg_size);
            for(jj=0; jj<repeats; jj++){
                MPI_Recv(recv,
                         mesg_size,
                         MPI_INT32_T,
                         ping,
                         (10*mesg_size*ping + jj)%MAX_INT,
                         MPI_COMM_WORLD,
                         &status);
                MPI_Send(recv,
                         mesg_size,
                         MPI_INT32_T,
                         ping,
                         (20*mesg_size*pong + jj)%MAX_INT,
                         MPI_COMM_WORLD);
            }
            // Free here
            free(recv);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }else{
        MPI_Barrier(MPI_COMM_WORLD);
    }

    return results;
}
