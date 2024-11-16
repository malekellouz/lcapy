"""
This module converts values into engineering format.

Copyright 2021--2024 Michael Hayes, UCECE
"""
from math import floor, log10


class ValueFormatter(object):

    def __init__(self, trim=True, hundreds=False, fmt=''):
        """If `hundreds` True format like 100 pF rather than 0.1 nF"""

        self.trim = trim
        self.hundreds = hundreds

        if fmt == '':
            self.num_digits = 3
        else:
            try:
                self.num_digits = int(fmt)
            except ValueError:
                raise ValueError('Expected a digit for format, got ' + fmt)

    def _do(self, value, unit, aslatex):

        prefixes = ('f', 'p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T')

        value = float(value)

        if value == 0:
            return self._fmt('0', unit, '', aslatex)

        m = log10(abs(value))

        if m < -1 or m >= 3.0:
            if not self.hundreds:
                m += 1
            n = int(floor(m / 3))
        else:
            n = 0

        # value       m   n
        # 3141592   6.5   2
        # 314159.   5.5   1
        # 31415.9   4.5   1
        # 3141.59   3.5   1
        # 314.159   2.5   0
        # 31.4159   1.5   0
        # 3.14159   0.5   0
        # .314159  -0.5   0
        # .0314159 -1.5  -1

        idx = n + 5
        # Handle extremely large or small values without a prefix
        if idx < 0:
            return self._fmt('%e' % value, unit, '', aslatex)
        elif idx >= len(prefixes):
            return self._fmt('%e' % value, unit, '', aslatex)

        svalue = value * 10**(-3 * n)

        # Round to num_digits
        scale = 10 ** (self.num_digits - 1 - floor(log10(abs(svalue))))
        rvalue = round(svalue * scale) / scale

        valstr = str(rvalue)

        if self.trim:
            # Remove trailing zeroes after decimal point
            valstr = valstr.rstrip('0').rstrip('.')

        return self._fmt(valstr, unit, prefixes[idx], aslatex)

    def latex_math(self, value, unit):
        """This is equivalent to the `latex()` method but encloses in $ $."""

        return '$' + self.latex(value, unit) + '$'

    def latex(self, value, unit):
        """Make latex string assuming math mode."""

        return self._do(value, unit, aslatex=True)

    def str(self, value, unit):
        """Make string."""

        return self._do(value, unit, aslatex=False)


class EngValueFormatter(ValueFormatter):

    def _fmt(self, valstr, unit='', prefix='', aslatex=True):

        if unit == '' and prefix == '':
            return valstr

        if not aslatex:
            return valstr + ' ' + prefix + unit

        s = valstr + '\\,'
        if prefix == 'u':
            if unit.startswith('$'):
                s += '\\mu' + unit[1:-1]
            else:
                s += '\\mu\\mathrm{' + unit + '}'
        else:
            if unit.startswith('$'):
                if prefix == '':
                    s += unit[1:-1]
                else:
                    s += '\\mathrm{' + prefix + '}' + unit[1:-1]
            else:
                s += '\\mathrm{' + prefix + unit + '}'
        return s


class SPICEValueFormatter(ValueFormatter):

    def _fmt(self, valstr, unit='', prefix='', aslatex=True):

        if unit == '' and prefix == '':
            return valstr

        if unit == '$\\Omega$':
            if prefix == '':
                unit = 'R'
            else:
                unit = ''

        # Ugly!
        if prefix == 'k':
            prefix = 'K'
        elif prefix == 'M':
            prefix = 'Meg'

        if not aslatex:
            return valstr + ' ' + prefix + unit

        return valstr + '\\,' + '\\mathrm{' + prefix + unit + '}'


class SciValueFormatter(ValueFormatter):

    def _do(self, value, unit, aslatex):

        value = float(value)

        fmt = '%%.%dE' % (self.num_digits - 1)

        valstr = fmt % value

        if not aslatex:
            return valstr + unit

        parts = valstr.split('E')
        exp = parts[1]

        if exp == '+00':
            valstr = parts[0]
        else:
            if exp[0] == '+':
                exp = exp[1:]
                if exp[0] == '0':
                    exp = exp[1:]
            elif exp[0] == '-' and exp[1] == '0':
                exp = '-' + exp[2]
            valstr = parts[0] + '\\times 10^{' + exp + '}'

        if unit.startswith('$'):
            return valstr + '\\,' + unit[1:-1]

        return valstr + '\\,' + '\\mathrm{' + unit + '}'


class RatfunValueFormatter(ValueFormatter):

    def _do(self, value, unit, aslatex):

        if not aslatex:
            return str(value) + ' ' + unit

        if unit.startswith('$'):
            return value.latex() + '\\,' + unit[1:-1]

        return value.latex() + '\\,' + '\\mathrm{' + unit + '}'


def value_formatter(style='eng3'):

    style = style.lower()

    if style.startswith('eng'):
        return EngValueFormatter(fmt=style[3:])
    elif style.startswith('spice'):
        return SPICEValueFormatter(fmt=style[5:])
    elif style.startswith('sci'):
        return SciValueFormatter(fmt=style[3:])
    elif style.startswith('ratfun'):
        return RatfunValueFormatter(fmt='')
    else:
        raise ValueError('Unknown style: ' + style)
