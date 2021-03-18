import numpy as np
import matplotlib.pyplot as plt

from argparse import ArgumentParser
from pathlib import Path
from pickle import load

parser = ArgumentParser()
parser.add_argument('-i', '--input', default='results.pickle')
parser.add_argument('-o', '--output')
parser.add_argument('-t', '--title', type=str, default=None)
args, _ = parser.parse_known_args()

inputfile = Path(args.input).absolute()
with open(inputfile, 'rb') as fh:
    results = load(fh)

cores = [ii +1 for ii in range(len(results))]

DPI = 300
fig, ax = plt.subplots(1, 1)
fig.set_size_inches((8, 8))

ax.plot(results, 'x-')
if args.title:
    ax.set_title(str(args.title))
else:
    ax.set_title('Streams')
ax.set_xlabel('Cores')
ax.set_ylabel('Rate MB/s')

if args.output:
    plt_name = Path(args.output).absolute()
else:
    plt_name = inputfile.with_suffix('.png')
fig.savefig(plt_name, bbox_inches='tight', dpi=DPI)
plt.show()
