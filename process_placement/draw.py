import subprocess

from math import sqrt, log10


def int_w_units(value):
    mag = {'k': 1024,
           'm': 1024**2,
           'g': 1024**3,
           't': 1024**4
           }
    units = list(mag.keys())
    units += [m + 'b' for m in mag]
    units += [m + 'ib' for m in mag]
    parts = value.split()
    if (len(parts) == 2) and (parts[1].lower() in units):
        try:
            converted = int(parts[0]) * mag[parts[1][0].lower()]
        except ValueError:
            raise ValueError('String is not a value with bytes size units')
    else:
        converted = value
    return converted


def int_csv(value):
    for conversion in [int, int_range]:
        try:
            converted = [conversion(ii) for ii in value.split(',')]
            break
        except ValueError:
            pass
    else:
        raise ValueError('String is not comma separated list of integers')
    if isinstance(converted[0], list):
        converted = sum(converted, [])
    return converted


def int_range(value):
    try:
        low, high = value.split('-')
        converted = [ii for ii in range(int(low), int(high) + 1)]
    except ValueError:
        raise ValueError('String is not hyphen separated range of integers')
    return converted


def convert(value):
    for conversion in [int, float, int_csv, int_w_units]:
        try:
            converted = conversion(value)
            break
        except ValueError:
            pass
    else:
        converted = value

    return converted


def lscpu():
    lscpu_proc = subprocess.run(['lscpu'],
                                capture_output=True,
                                encoding='UTF-8')
    cpu_dict = {}
    for line in lscpu_proc.stdout.split('\n'):
        key, *value = line.split(':')
        cpu_dict[key] = convert((':'.join(value)).strip())

    if '' in cpu_dict.keys():
        del cpu_dict['']

    return cpu_dict


class CPUDrawing(object):
    def __init__(self, cores, max_threads=1, core_digits=1,
                 thread_digits=2, offset=0):
        self._cores = cores
        self._max_threads = max_threads
        self._core_digits = core_digits
        self._thread_digits = thread_digits
        self._offset = offset

        for ii in range(int(sqrt(cores)), 0, -1):
            q, r = divmod(cores, ii)
            if r == 0:
                break
        self._width = q
        self._height = ii
        self._space = core_digits + thread_digits + 1

        self._diagram = None

    def draw_ascii_cpu(self):
        w = self._width
        s = self._space

        diagram = ''
        header = ('R') + ('='*s + 'T')*(w - 1) + ('='*s + 'N\n')
        num_row = ('E')
        num_row += ('{:0' + str(self._core_digits) + 'd}'
                    + '-'*(self._thread_digits+1) + '+')*(w - 1)
        num_row += ('{:0' + str(self._core_digits) + 'd}'
                    + '-'*(self._thread_digits+1) + 'H\n')

        footer = ('L') + ('='*s + 'W')*(w-1) + ('='*s + 'J\n')

        diagram += header
        temp = '{:0' + str(self._core_digits) + 'd}/'
        temp += '{:0' + str(self._thread_digits) + 'd}'
        for ii in range(self._height):
            lower = self._offset + ii*w
            upper = self._offset + (ii + 1)*w
            diagram += num_row.format(*range(lower, upper))
            for kk in range(self._max_threads):
                row = ('I')
                for jj in range(w - 1):
                    row += temp.format(self._offset + ii*w + jj, kk) + 'i'
                row += temp.format(self._offset + ii*w + jj + 1, kk) + 'I\n'
                diagram += row
        diagram += footer
        self._diagram = diagram

    def __str__(self, utf8=True):
        '''
        R===T===N
        I   I   I
        E===O===H
        I   I   I
        L===W===J

        r---t---n
        i   i   i
        e---+---h
        i   i   i
        l---w---j
        '''
        if self._diagram is None:
            line = lambda s: chr(int('0x25' + s, 16))
            linedict = {
                'R': line('0F'),
                '=': line('01'),
                'T': line('2F'),
                'N': line('13'),
                'I': line('03'),
                'E': line('20'),
                'H': line('28'),
                'L': line('17'),
                'W': line('37'),
                'J': line('1B'),
                'r': line('0C'),
                '-': line('00'),
                't': line('2C'),
                'n': line('10'),
                'i': line('02'),
                'e': line('1C'),
                '+': line('3C'),
                'h': line('24'),
                'l': line('14'),
                'w': line('34'),
                'j': line('18')
            }

            self.draw_ascii_cpu()
            if utf8:
                for key, value in linedict.items():
                    self._diagram = self._diagram.replace(key, value)

        return self._diagram

    def __add__(self, other):
        assert(isinstance(other, type(self)))
        diagram = ''
        for d in [self, other]:
            if d._diagram is None:
                _ = str(d)
        sdiagram = self._diagram.split('\n')
        odiagram = other._diagram.split('\n')
        for ii, _ in enumerate(sdiagram):
            diagram += ('    ').join([sdiagram[ii], odiagram[ii]]) + '\n'
        return diagram

    def __radd__(self, other):
        assert(other is None)

        return str(self)

    def format(self, cpu_dict, utf8=True):
        if utf8:
            _ = str(self)
            sep = chr(int('0x2502', 16))
            borders = chr(int('0x2503', 16))
        else:
            _ = self.draw_ascii_cpu()
            sep = 'i '
            borders = 'I'

        diagram = self._diagram.split()

        for ii, line in enumerate(diagram):
            row = line.split(sep)
            if len(row) == 1:
                continue
            else:
                for cell in row:
                    placeholder = cell.strip(borders)
                    # ~ print(placeholder, end=' ')
                    cpu, thread = [int(x) for x in placeholder.split('/')]
                    try:
                        rank = '{:0' + str(self._space) + '.'
                        rank += str(self._thread_digits) + 'f}'
                        rank = rank.format(cpu_dict[cpu][thread])
                        # ~ print(rank)
                        diagram[ii] = diagram[ii].replace(placeholder, rank)
                    except IndexError:
                        diagram[ii] = diagram[ii].replace(placeholder,
                                                          ' '*self._space)
                        # ~ print()
        self._diagram = '\n'.join(diagram)
        return self


def get_current(max_cores, max_threads):
    cpu = lscpu()
    # ~ pprint(cpu)
    sockets = cpu['Socket(s)']
    cores = cpu['Core(s) per socket']
    hwthreads = cpu['Thread(s) per core']
    cpu_list = []

    offset = 0
    core_digits = int(log10(max_cores)) + 1
    thread_digits = int(log10(max_threads)) + 1

    for _ in range(sockets):
        cpu_list.append(CPUDrawing(cores,
                                   max_threads,
                                   core_digits,
                                   thread_digits,
                                   offset))
        offset += cores

    return cpu_list


def draw_symbol_table():
    print(' '*8 + ' '.join([hex(x)[-1].upper() for x in range(16)]))
    for val in range(int('0x2500', 16), int('0x2700', 16), 16):
        print(hex(val).upper(), end=': ')
        for offset in range(16):
            print(chr(val+offset), end=' ')
        print()


if __name__ == '__main__':
    cpu_list = get_current(2)
    print(sum(cpu_list[1:], cpu_list[0]))
