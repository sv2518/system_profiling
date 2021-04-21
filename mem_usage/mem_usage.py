import os
import sys
import time

from argparse import ArgumentParser
from csv import DictWriter

parser = ArgumentParser()
subparsers = parser.add_subparsers(dest='command')
mon_parser = subparsers.add_parser('monitor')
mon_parser.add_argument('--target', type=str, help='Name of target application')
mon_parser.add_argument('--timeout', type=int, default=10, help='Time to wait for application to start')
mon_parser.add_argument('--free', action='store_true', help='Monitor remaining memory')
plot_parser = subparsers.add_parser('plot')
plot_parser.add_argument('--input', type=str, help='CSV to read')
plot_parser.add_argument('--output', type=str, help='Name to save plot to')
args, unknown = parser.parse_known_args()

def monitor(args):
    import psutil
    try:
        from mpi4py import MPI
        rank = MPI.rank
    except ImportError:
        rank = 0

    process = []
    for _ in range(args.timeout):
        for p in psutil.process_iter(['pid', 'cmdline']):
            if (args.target in p.info['cmdline']) and (not sys.argv[0] in p.info['cmdline']):
                process.append(psutil.Process(p.info['pid']))
        if len(process) == 0:
            time.sleep(1)
        else:
            print('Target process started')
            break
    else:
        raise ProcessLookupError(f'Target application did not start within {args.timeout} seconds of this script launching')

    mem = psutil.virtual_memory()._asdict()
    with open(f'free{rank}_{int(time.time())}.csv', 'w') as fh:
        start = time.time()
        csv = DictWriter(fh, ['time'] + [k for k in mem.keys()])
        csv.writeheader()
        while all(p.is_running() for p in process):
            row = psutil.virtual_memory()._asdict()
            row['time'] = time.time() - start
            csv.writerow(row)
            fh.flush()
            time.sleep(0.1)

def plot(args):
    import matplotlib.pyplot as plt
    from pandas import read_csv

    if args.input is None:
        infile = sorted(filter(lambda x: x.startswith('free') and x.endswith('.csv'), os.listdir()))[-1]
    else:
        infile = args.input
    data = read_csv(infile)
    data['available (GB)'] = data['available']/(1024**3)

    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches(8, 6)
    data.plot('time', 'available (GB)', ax=ax)

    ax.set_xlabel('Time (s)')
    ax.set_ylim(0, data['total'][0]/(1024**3))
    ax.set_ylabel('Free Memory (GB)')

    if args.output:
        fig.savefig(args.output)
    else:
        plt.show()

if __name__ == '__main__':
    if args.command == 'monitor':
        monitor(args)
    elif args.command == 'plot':
        plot(args)

