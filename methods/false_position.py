import timeit

from resultset import ResultSet
from table import Table
from util import *


def false_position(func, xl, xu, iterations=50, eps=0.00001):
    if evaluateFunc(func, xl) * evaluateFunc(func, xu) > 0:
        return float('nan')

    boundaryLines = [xl, xu]
    boundaryChordEqn = getLineEquation((xl, evaluateFunc(func, xl)), (xu, evaluateFunc(func, xu)))
    iterationRows = []
    startTime = timeit.default_timer()
    xr_old = None

    for i in xrange(iterations):
        xr = (xl * evaluateFunc(func, xu) - xu * evaluateFunc(func, xl)) / (
            evaluateFunc(func, xu) - evaluateFunc(func, xl))

        if xr_old != None:
            ea = abs(xr - xr_old)
            ea_rel = abs(xr - xr_old) / max(abs(xr_old), abs(xr))
        else:
            ea = "-"

        iterationRows.append([i + 1, xl, evaluateFunc(func, xl), xu, evaluateFunc(func, xu), xr, ea])
        xr_old = xr

        if evaluateFunc(func, xr) > 0:
            xu = xr
        else:
            xl = xr

        if evaluateFunc(func, xr) == 0:
            ea_rel = 0
            break
        if i > 0 and ea < eps: break

    executionTime = timeit.default_timer() - startTime
    table = Table("False-Position", ['Step', 'xl', 'f(xl)', 'xu', 'f(xu)', 'xr', 'Abs. Error'], iterationRows)
    return ResultSet(table, xr, calcPrecision(ea_rel), executionTime, i,
                     [sympy.lambdify('x', func, 'numpy'), sympy.lambdify('x', boundaryChordEqn, 'numpy')],
                     vLines=boundaryLines)


# Test

if __name__ == '__main__':
    str = 'x^3 - 3x + 1'
    stra = 'x^3 - 0.165x^2'
    expr = parseExpr(stra)

    print false_position(0, 1, expr, 100, 10 ** -20)