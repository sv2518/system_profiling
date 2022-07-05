import numpy as np
import matplotlib.pyplot as plt

from argparse import ArgumentParser
from pathlib import Path
from pickle import load
from run_stream import size2val

parser = ArgumentParser()
parser.add_argument('--channels', type=int, default=None)
parser.add_argument('-i', '--input', default='results.pickle')
parser.add_argument('-o', '--output')
parser.add_argument('--single_channel', type=str, default=None)
parser.add_argument('-t', '--title', type=str, default=None)
args, _ = parser.parse_known_args()

inputfile = Path(args.input).absolute()
with open(inputfile, 'rb') as fh:
    results = np.array(load(fh))

cores = [ii + 1 for ii in range(len(results))]
if args.channels:
    channels = [ii + 1 for ii in range(args.channels)]
else:
    channels = [ii + 1 for ii in range(len(results))]
if args.single_channel:
    single_channel = size2val(args.single_channel)
else:
    single_channel = results[0]


DPI = 300
fig, ax = plt.subplots(1, 1)
fig.set_size_inches((8, 8))

perfect = [c*single_channel/(2**30) for c in channels]
# ~ ax.plot([0], [0], 'ko')
ax.plot(channels, perfect, 'k:')
ax.plot([channels[-1], cores[-1]], [perfect[-1], perfect[-1]], 'k:')
ax.plot(cores, results/(2**10), 'x-')
if args.title:
    ax.set_title(str(args.title))
else:
    ax.set_title('Streams')
ax.set_xlabel('Cores')
ax.set_ylabel('Rate GB/s')

if args.output:
    plt_name = Path(args.output).absolute()
else:
    plt_name = inputfile.with_suffix('.png')
fig.savefig(plt_name, bbox_inches='tight', dpi=DPI)
plt.show()
