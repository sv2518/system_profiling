import matplotlib.pyplot as plt

from argparse import ArgumentParser
from pathlib import Path
from pickle import load

parser = ArgumentParser()
parser.add_argument('-i', '--input', default='results.pickle')
parser.add_argument('-o', '--output')
args, _ = parser.parse_known_args()

inputfile = Path(args.input).absolute()
with open(inputfile, 'rb') as fh:
    latencies, rates = load(fh)

DPI = 300
fig, ax = plt.subplots(2, 1)
fig.set_size_inches((8, 8))
fig.subplots_adjust(hspace=0.3)

ax[0].hist(latencies)
ax[0].set_title('Latency Time')
ax[0].set_xlabel('time (s)')
ax[0].set_ylabel('frequency')

ax[1].hist(rates)
ax[1].set_title('Rate')
ax[1].set_xlabel('Rate (Bytes/s)')
ax[1].set_ylabel('frequency')

if args.output:
    plt_name = Path(args.output).absolute()
else:
    plt_name = inputfile.with_suffix('.png')
fig.savefig(plt_name, bbox_inches='tight', dpi=DPI)
# ~ plt.show()
