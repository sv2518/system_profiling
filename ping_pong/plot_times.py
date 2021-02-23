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
ax[1].set_xlabel('Rate (bits/s)')
ax[1].set_ylabel('frequency')

fig.suptitle(args.title)

if args.output:
    plt_name = Path(args.output).absolute()
else:
    plt_name = inputfile.with_suffix('.png')
fig.savefig(plt_name, bbox_inches='tight', dpi=DPI)
# ~ plt.show()

if True:
    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches((8, 8))

    ax.loglog(latencies, rates, 'o')
    ax.set_title('Clustering')
    ax.set_xlabel('Latency (s)')
    ax.set_ylabel('Rate (bits/s)')

    plt_name = inputfile.with_suffix('.scatter.png')
    fig.savefig(plt_name, bbox_inches='tight', dpi=DPI)

if False:
    BLOCK = 1024
    with open(inputfile.with_suffix('.detailed.pickle'), 'rb') as fh:
        array_sizes, repeats, results = load(fh)

    # 8 Bits to a byte sent back _and_ forth
    x = np.array([16*BLOCK*a for a in array_sizes])
    x_range = np.linspace(x[0], x[-1], 100)

    cols = int(np.ceil(np.sqrt(len(results))))
    rows = int(np.ceil(len(results)/cols))
    fig, axes = plt.subplots(rows, cols, sharey=True, squeeze=False, figsize=(16, 9))
    for ax, (key, val) in zip(axes.ravel(), results.items()):
        y = np.array(val)
        y_mean = np.mean(y, axis=1)
        mean_m, mean_c = np.polyfit(x, y_mean, deg=1)
        # ~ print('Rate:', mean_m, 'bits/sec, Latency:', mean_c, 'sec')
        y_median = np.median(y, axis=1)
        median_m, median_c = np.polyfit(x, y_median, deg=1)
        y_min = np.min(y, axis=1)
        min_m, min_c = np.polyfit(x, y_min, deg=1)
        box_info = ax.boxplot(val,
                              sym='b+',
                              positions=x,
                              widths=100*BLOCK,
                              showfliers=False,
                              # ~ showmeans=True,
                              # ~ meanprops={'marker': 'x', 'mec': 'r'}
                              )
        #ax.plot(x, y_mean, 'r-')
        ax.plot(x_range, mean_m*x_range + mean_c, 'r-', label='Mean fit')
        ax.plot(x, y_median, 'x', color='orange')
        ax.plot(x_range, median_m*x_range + median_c, '-', color='orange', label='Median fit')
        ax.annotate(f'Rate   : {1/median_m:7.5g} bits/s\nLatency: {median_c:7.5g}s',
                    (0.1, 0.8),
                    xycoords='axes fraction',
                    color='orange')
        ax.plot(x, y_min, 'gx')
        ax.plot(x_range, min_m*x_range + min_c, 'g-', label='Min fit')
        ax.set_title(str(key))
        ax.set_xlabel('bits transferred')
        ax.xaxis.set_label_coords(0.8, 0.05, transform=ax.transAxes)
        ax.set_ylabel('time (s)')
        ax.set_xticklabels(x, rotation=22.5, ha="right")


    axes.ravel()[0].legend()
    fig.suptitle(args.title)
    fig.subplots_adjust(hspace=0.3)

    plt_name2 = inputfile.with_suffix('.detailed.png')
    fig.savefig(plt_name2, bbox_inches='tight', dpi=DPI)
    # ~ plt.show()
