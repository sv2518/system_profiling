import ctypes
import psutil

from draw import get_current
from math import log10
from mpi4py import MPI
from pprint import pprint

# MPI Get global communicator size and rank
size = MPI.COMM_WORLD.size
rank = MPI.COMM_WORLD.rank

# Get number of HWthreads and Cores
blocked = True
cores = psutil.cpu_count(logical=False)
hwthreads = psutil.cpu_count(logical=True)

# Get the Python process CPU number and affinity
process = psutil.Process()
num = process.cpu_num()
affinity = process.cpu_affinity()

# OpenMP threading
# COMPILE C WITH: gcc -fPIC -fopenmp -shared -o omp_cpu.so omp_cpu.c
# Import shared object
omp_so = ctypes.CDLL('./omp_cpu.so')
# Specify arguement type
omp_so.get_num.argtype = (ctypes.POINTER(ctypes.c_int),
                          ctypes.POINTER(ctypes.c_int)
                          )
# Specify return type
omp_so.get_num.restype = None

omp_so.omp_get_max_threads.argtype = None
omp_so.omp_get_max_threads.restype = ctypes.c_int

# Get each C thread's CPU number and affinity
nthreads = omp_so.omp_get_max_threads()
thread_num = (ctypes.c_int*nthreads)()
thread_num[:] = [-1]*nthreads
cpu_num = (ctypes.c_int*nthreads)()
cpu_num[:] = [-1]*nthreads

omp_so.get_num(thread_num, cpu_num)


thread_num = list(thread_num)
dp = int(log10(nthreads)) + 1
factor = 10**(-dp)
thread_num = [round(rank + factor*t, dp) for t in thread_num]
cpu_num = list(cpu_num)

tn = MPI.COMM_WORLD.gather(thread_num, root=0)
cn = MPI.COMM_WORLD.gather(cpu_num, root=0)
an = MPI.COMM_WORLD.gather(affinity, root=0)

if rank == 0:
    print('SIZE    RANK.THREAD    CPU_NUM     AFFINITY')
    core_dict = {c: [] for c in range(cores)}
    for thread, cpu, aff in zip(tn, cn, an):
        print('       '.join(str(x) for x in [size, thread, cpu, aff]))
        for c, t in zip(cpu, thread):
            if blocked:
                core_dict[c//cores].append(t)
            else:
                core_dict[c % cores].append(t)

    max_cores = hwthreads
    max_threads = max([len(v) for v in core_dict.values()])
    cpu_list = get_current(max_cores, max_threads)
    pprint(core_dict)
    output = [c.format(core_dict) for c in cpu_list]
    print()
    print(sum(output[1:], output[0]))
