import psutil

from argparse import ArgumentParser
from os import environ
from pathlib import Path
from pickle import dump
from subprocess import run, PIPE

def guess_cores():
    return psutil.cpu_count(logical=False)


def guess_l3():
    try:
        output = run(['lscpu', '-C'], check=True, stdout=PIPE, stderr=PIPE, encoding='UTF-8')
        for s in reversed(output.stdout.split('\n')):
            if s:
                cache = s
                break
        size = cache.split()[2]
        if size.isdecimal():
            l3 = int(size)
        else:
            suffix = ['', 'k', 'm', 'g']
            *val, unit = size
            l3 = int(''.join(val)) * 2**(10*suffix.index(unit.lower()))
    except FileNotFoundError:
        print('No command `lscpu` using default value of 20MB for L3 cache size')
        l3 = 20*2**20
    return l3


# Parse command line arguments
parser = ArgumentParser()
parser.add_argument('-c', '--cores', type=int, default=None)
parser.add_argument('--cc', type=str, default='gcc')
parser.add_argument('-l3', '--l3', type=int, default=None)
parser.add_argument('-o', '--output', default='results.pickle')
parser.add_argument('--offset', type=int, default=0)
parser.add_argument('-r', '--repeats', type=int, default=10)
args, _ = parser.parse_known_args()

if args.cores:
    cores = args.cores
else:
    cores = guess_cores()

if args.l3:
    l3 = args.l3
else:
    l3 = guess_l3()

# L3 cache multiplied by 4, then divided by sizeof(double) = 8
array_size = l3//2

compiler = args.cc
cflags = '-march=native -O3 -fopenmp -ffast-math'
pp_defs = f'-DSTREAM_ARRAY_SIZE={array_size} -DNTIMES={args.repeats} -DOFFSET={args.offset}'
source_file = Path('stream.c').absolute()
executable_file = source_file.with_suffix('')

compile_command = [compiler] + cflags.split() + pp_defs.split()
compile_command += ['-o', str(executable_file)]
compile_command.append(str(source_file))

# ~ print(compile_command)
run(compile_command)

run_env = environ.copy()
run_env['OMP_DISPLAY_AFFINITY'] = 'TRUE'
run_env['OMP_PLACES'] = 'cores'
run_env['OMP_PROC_BIND'] = 'spread'
results = []
for ii in range(cores):
    run_env['OMP_NUM_THREADS'] = str(ii + 1)
    output = run([executable_file], env=run_env, check=True, stdout=PIPE, stderr=PIPE, encoding='UTF-8')
    for line in output.stdout.split('\n'):
        # ~ print(line)
        if line.startswith('level'):
            print(line)
        elif line.startswith('Triad'):
            speed = line.split()[1]
    results.append(speed)
    print('Cores:', ii + 1, 'Rate:', speed, 'MB/s')
    print('Affinity:\n', output.stderr)

outfile = Path(args.output).absolute()
with open(outfile, 'wb') as fh:
    dump(results, fh)
