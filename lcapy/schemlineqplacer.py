from numpy import zeros, hstack, dot, argsort, min, max, vstack
from scipy.linalg import inv, lu
from .cnodes import Cnodes
from .schemplacerbase import SchemPlacerBase
from warnings import warn

# This is an experimental component placement algorithm for schematics
# based on solving a system of linear equations.  The unknowns are the
# node positions and the stretch requried for stretchy components.
#
# The algorithm identifies the free stretch variables and assigns them
# to be zero.  However, this depends on the constraint ordering and
# so sometimes a negative stretch is generated due to a poor choice
# of basic variable.  This could be avoided with a constrained
# optimisation where the node positions and component stretches all
# need to be non-negative.


class Constraint(object):

    def __init__(self, size, stretch):
        self.size = size
        self.stretch = stretch

    def __repr__(self):
        return '%.2f%s' % (self.size, '*' if self.stretch else '')


class Constraints(dict):

    def __repr__(self):

        s = ''
        for key, constraint in self.items():
            s += '%s -> %s: %s\n' % (key[0], key[1], repr(constraint))
        return s


class Lineq(object):

    def __init__(self, direction, nodes, debug=0):

        self.direction = direction
        self.cnodes = Cnodes(nodes)
        self.debug = debug
        self.constraints = Constraints()

    def link(self, n1, n2):
        """Make nodes n1 and n2 share common node"""

        self.cnodes.link(n1, n2)

    def add(self, elt, n1, n2, size, stretch):

        if size == 0:
            return

        if size < 0:
            n1, n2 = n2, n1
            size = -size

        if n1 in self.cnodes:
            n1 = self.cnodes[n1]
        if n2 in self.cnodes:
            n2 = self.cnodes[n2]

        key = n1, n2
        key2 = n2, n1
        if key not in self.constraints and key2 not in self.constraints:
            self.constraints[key] = Constraint(size, stretch)
            return

        if key2 in self.constraints:
            size = -size
            key = key2
        constraint = Constraint(size, stretch)

        constraint2 = self.constraints[key]
        if not constraint2.stretch:
            if (not constraint.stretch and constraint2.size != constraint.size):
                raise ValueError('Incompatible fixed constraint of size %s and %s' % (
                    constraint.size, constraint2.size))
            self.constraints[key] = constraint
            return

        if abs(constraint.size) > abs(constraint2.size):
            self.constraints[key] = constraint

    def solve(self, stage=None):

        cnode_map = {}
        cnode_imap = []
        num = 0
        for node, cnode in self.cnodes.items():
            if cnode not in cnode_map:
                cnode_map[cnode] = num
                cnode_imap.append(cnode)
                num += 1

        Nstretches = 0
        for key, constraint in self.constraints.items():
            if constraint.stretch:
                Nstretches += 1

        Nnodes = len(cnode_map)

        if Nnodes == 1:
            pos = {}
            for node, cnode in self.cnodes.items():
                m = cnode_map[self.cnodes[node]]
                pos[node] = 0
            return pos, 0

        Nunknowns = Nnodes - 1 + Nstretches
        Nconstraints = len(self.constraints)

        A = zeros((Nconstraints, Nunknowns))
        b = zeros((Nconstraints, 1))

        m = 0
        s = 0

        for key, constraint in self.constraints.items():
            m1 = cnode_map[key[0]]
            m2 = cnode_map[key[1]]
            size = constraint.size

            if m1 != 0:
                A[m, m1 - 1] = -1
            if m2 != 0:
                A[m, m2 - 1] = 1
            if constraint.stretch:
                A[m, s + Nnodes - 1] = -1
                s += 1

            b[m] = size
            m += 1

        # Augmented matrix.
        W = hstack((A, b))

        # Extract upper triangular form (this is similar to
        # reduce row-echelon form (RREF) but not always).
        PL, U = lu(W, permute_l=True)

        # Non-zero for bound (basic) variables.
        bound = zeros(W.shape[-1], dtype=int)

        for r in range(Nnodes - 1):
            if U[r, r] == 0:
                raise ValueError(
                    'No basic variable for node %s' % cnode_imap[r])
            bound[r] = 1

        for r in range(U.shape[0]):
            if U[r, r] != 0:
                bound[r] = 1
                # For prettiness
                if U[r, r] < 0:
                    U[r, r:] = -U[r, r:]

        Nbasic = bound.sum()
        Ur = U[0:Nbasic, bound != 0]

        br = U[0:Nbasic, -1]
        # A slow one-liner!  Just need to back-substitute.
        xx = dot(inv(Ur), br)
        x = xx[0: Nnodes - 1]

        # A negative stretch can be generated by inconsistent constraints
        # or more likely by a poor choice of a stretch as a basic variable.
        # This depends on the constraint ordering since the first stretch
        # unknowns will be selected.
        for m in range(Nnodes - 1, xx.shape[0]):
            if xx[m] < 0:
                warn('Negative stretch %s' % xx[m])

        minx = min(x)
        width = max(x) - minx

        pos = {}
        for node, cnode in self.cnodes.items():
            m = cnode_map[self.cnodes[node]]
            if m == 0:
                pos[node] = 0 - minx
            else:
                pos[node] = x[m - 1] - minx

        self.W = W
        self.b = b
        self.U = U

        if ((self.direction == 'horizontal' and self.debug & 4)
                or (self.direction == 'vertical' and self.debug & 8)):

            if self.debug & 16:
                from .matrix import Matrix
                W = Matrix(W)
                print(W.latex())

            if self.debug & 32:
                from .matrix import Matrix
                U = Matrix(U)
                print(U.latex())

            if self.debug & 64:
                for key, cnode in self.cnodes.items():
                    print(key, cnode)

            if self.debug & 128:
                for key, constraint in self.constraints.items():
                    print(key, constraint)

            if self.debug & 256:
                import pdb
                pdb.set_trace()

        return pos, width


class SchemLineqPlacer(SchemPlacerBase):

    def __init__(self, elements, nodes, debug=0):

        self.elements = elements
        self.nodes = nodes
        self.debug = debug

        self.xgraph = Lineq('horizontal', nodes, debug)
        self.ygraph = Lineq('vertical', nodes, debug)

        warn('This is experimental')
