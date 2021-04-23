import os
import sys
import time

from argparse import ArgumentParser
from csv import DictWriter
from pathlib import Path

parser = ArgumentParser()
subparsers = parser.add_subparsers(dest='command')
mon_parser = subparsers.add_parser('monitor')
mon_parser.add_argument('--target', type=str, help='Name of target application')
mon_parser.add_argument('--timeout', type=int, default=10, help='Time to wait for application to start')
mon_parser.add_argument('--free', action='store_true', help='Monitor remaining memory')
mon_parser.add_argument('--output', type=str, help='Name to save log to')
plot_parser = subparsers.add_parser('plot')
plot_parser.add_argument('--input', type=str, nargs='+', help='CSV to read')
plot_parser.add_argument('--output', type=str, help='Name to save plot to')
args, unknown = parser.parse_known_args()

def monitor(args):
    import psutil
    try:
        from mpi4py import MPI
        rank = MPI.COMM_WORLD.rank
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
    if args.output:
        outfile = f'{args.output}_{rank}.csv'
    else:
        outfile = f'free{rank}_{int(time.time())}.csv'
    with open(outfile, 'w') as fh:
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
        infile = [sorted(filter(lambda x: x.startswith('free') and x.endswith('.csv'), os.listdir()))[-1]]
    else:
        infile = args.input

    for ii, csv in enumerate(infile):
        data = read_csv(csv)
        data['available (GB)'] = data['available']/(1024**3)

        fig, ax = plt.subplots(1, 1)
        fig.set_size_inches(8, 6)
        data.plot('time', 'available (GB)', ax=ax)

        ax.set_xlabel('Time (s)')
        ax.set_ylim(0, data['total'][0]/(1024**3))
        ax.set_ylabel('Free Memory (GB)')

        if args.output:
            outfile = Path(args.output)
            if len(infile) > 1:
                outfile = outfile.with_stem(outfile.stem + f'_{ii}')
            fig.savefig(outfile)
        else:
            fig.savefig(Path(csv).with_suffix('.png'))

if __name__ == '__main__':
    if args.command == 'monitor':
        monitor(args)
    elif args.command == 'plot':
        plot(args)

