import ctypes
import numpy as np

from argparse import ArgumentParser
from itertools import combinations, repeat
from mpi4py import MPI
from pathlib import Path
from pickle import dump
from time import time

comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

assert size != 1, 'Running in serial, no ping pong results'

class CPingPong(object):
    ''' Class for handling wrapped C function
    '''
    def __init__(self):
        # COMPILE C WITH: mpicc -fPIC -shared -o omp_cpu.so omp_cpu.c
        # Import shared object
        self.pingpong_so = ctypes.CDLL('./pingpong.so')
        # double *pingpong(int ping, int pong, int *message_sizes, int mslen, int repeats)
        # Specify argument type
        self.pingpong_so.pingpong.argtype = (ctypes.c_int,
                                             ctypes.c_int,
                                             ctypes.POINTER(ctypes.c_int),
                                             ctypes.c_int,
                                             ctypes.c_int
                                             )
        # Specify return type
        self.pingpong_so.pingpong.restype = ctypes.POINTER(ctypes.c_double)

    def __call__(self, ping, pong, mesg_sizes, repeats=10):
        ''' Wrapper for C function pingpong
        '''
        comm = MPI.COMM_WORLD
        assert ping < comm.size, 'Ping rank bigger than comm size'
        assert pong < comm.size, 'Pong rank bigger than comm size'
        assert isinstance(mesg_sizes, list)

        mslen = len(mesg_sizes)
        message_sizes = (ctypes.c_int*mslen)()
        message_sizes[:] = mesg_sizes
        results = self.pingpong_so.pingpong(ctypes.c_int(ping),
                                            ctypes.c_int(pong),
                                            message_sizes,
                                            ctypes.c_int(mslen),
                                            ctypes.c_int(repeats))

        if comm.rank == ping:
            results = results[:mslen*repeats]
        results = comm.bcast(results, root=ping)
        return results

# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('-o', '--output', default='results.pickle')
args, _ = parser.parse_known_args()

# Different size arrays (will be multiplied by BLOCK=1024) to send
BLOCK = 1024
repeats = 20
array_sizes = [1, 10, 20, 40, 70, 100]

# Results
local_results = {}

# Compare rank 0 to all others if communicator count too large
if size > 32:
    # O(n)
    pairs = zip(repeat(0), range(1, size))
else:
    # O(n**2)
    pairs = combinations(range(size), 2)

# Perform ping pong test on all pairs
cpingpong = CPingPong()
comm.Barrier()
for ping, pong in pairs:
    if rank==0:
        print(f'Ping {ping}, Pong {pong}', flush=True)
    results = cpingpong(ping, pong, array_sizes, repeats=repeats)
    local_results[(ping, pong)] = [results[ii:ii+repeats] for ii in range(0, len(results), repeats)]
    comm.Barrier()

if rank==0:
    # 8 Bits to a byte sent back _and_ forth
    x = np.array([16*BLOCK*a for a in array_sizes])

    rates = []
    latencies = []
    for dat in local_results.values():
        y = np.array(dat)
        y_mean = np.mean(y, axis=1)
        mean_m, mean_c = np.polyfit(x, y_mean, deg=1)
        rates.append(1/mean_m)
        latencies.append(mean_c)
    print(latencies, rates)
    outfile = Path(args.output).absolute()
    with open(outfile, 'wb') as fh:
        dump((latencies, rates), fh)
    with open(outfile.with_suffix('.detailed.pickle'), 'wb') as fh:
        dump((array_sizes, repeats, local_results), fh)
