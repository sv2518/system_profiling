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

# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('-o', '--output', default='results.pickle')
args, _ = parser.parse_known_args()

# Generate some large arrays
BLOCK = 1024
SMALL = BLOCK
LARGE = 1024*BLOCK
rng = np.random.Generator(np.random.PCG64(rank))
small_send = rng.integers(1024**2, size=SMALL)
large_send = rng.integers(1024**2, size=LARGE)

small_recv = np.zeros(SMALL)
large_recv = np.zeros(LARGE)

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
for ping, pong in pairs:
    if rank==0:
        pass
        # ~ print(f'Ping {ping}, Pong {pong}', flush=True)
    if rank == ping:
        # Small buffer
        short = time()
        comm.Send([small_send, MPI.INT], dest=pong, tag=10*ping)
        comm.Recv([small_recv, MPI.INT], source=pong, tag=20*pong)
        short = time() - short
        # Large buffer
        llong = time()
        comm.Send([large_send, MPI.INT], dest=pong, tag=30*ping)
        comm.Recv([large_recv, MPI.INT], source=pong, tag=40*pong)
        llong = time() - llong
        # ~ print(f'Short: {short}', flush=True)
        # ~ print(f'Long: {llong}', flush=True)
        local_results[(ping, pong)] = (short, llong)
        comm.Barrier()
    elif rank == pong:
        # Small
        comm.Recv([small_recv, MPI.INT], source=ping, tag=10*ping)
        comm.Send([small_recv, MPI.INT], dest=ping, tag=20*pong)
        # Large
        comm.Recv([large_recv, MPI.INT], source=ping, tag=30*ping)
        comm.Send([large_recv, MPI.INT], dest=ping, tag=40*pong)
        comm.Barrier()
    else:
        comm.Barrier()

# Gather all results
if size > 32:
    results = [local_results]
else:
    results = comm.gather(local_results, root=0)

if rank==0:
    all_results = {}
    for r in results:
        all_results.update(r)

    rates = []
    latencies = []
    for t1, t2 in all_results.values():
        r = (8*(LARGE - SMALL))/(t2 - t1)
        rates.append(r)
        latencies.append(t1 - SMALL/r)
    outfile = Path(args.output).absolute()
    with open(outfile, 'wb') as fh:
        dump((latencies, rates), fh)
