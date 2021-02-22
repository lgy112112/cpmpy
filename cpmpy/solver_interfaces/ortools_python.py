from . import *
from ..expressions import *
from ..variables import *
from .minizinc_text import *

class ORToolsPython(SolverInterface):
    """
    Interface to the python 'ortools' API

    Requires that the 'ortools' python package is installed:
    $ pip install ortools

    Creates the following attributes:
    _model: the ortools.sat.python.cp_model.CpModel() created by _model()
    _solver: the ortools cp_model.CpSolver() instance used in solve()
    """

    def __init__(self):
        self.name = "ortools"

    def supported(self):
        try:
            import ortools
            return True
        except ImportError as e:
            return False

    def make_model(self, cpmpy_model):
        from ortools.sat.python import cp_model as ort

        # Constraint programming engine
        self._model = ort.CpModel()

        # Create corresponding solver variables
        self.varmap = dict() # cppy var -> solver var
        self.revarmap = dict() # reverse: solver var -> cppy var
        modelvars = get_variables(cppy_model)
        for var in modelvars:
            if isinstance(var, BoolVarImpl):
                revar = self._model.NewBoolVar(str(var.name))
            elif isinstance(var, IntVarImpl):
                revar = self._model.NewIntVar(var.lb, var.ub, str(var.name))
            self.varmap[var] = revar
            self.revarmap[revar] = var

        # post the constraint expressions to the solver
        # TODO: assumes 'flat' constraints (no subexpressions)
        for con in cppy_model.constraints:
            self.post_expression(con)

        # the objective
        if cppy_model.objective is None:
            pass # no objective, satisfaction problem
        else:
            # objective has to be an intvar or a linear expression
            print(type(cppy_model.objective))
            # TODO: convert objective to...?
            ort_obj = cppy_model.objective
            print(cppy_model.objective)
            if cppy_model.objective_max:
                self._model.Maximize(ort_obj)
            else:
                self._model.Minimize(ort_obj)

        return self._model

    def solve(self, cpmpy_model, num_workers=1):
        if not self.supported():
            raise "Install the python 'ortools' package to use this '{}' solver interface".format(self.name)
        from ortools.sat.python import cp_model as ort

        # create model (TODO: how to start from other model?)
        self._model = self.make_model(cpmpy_model)

        # solve the instance
        self._solver = ort.CpSolver()
        self._solver.parameters.num_search_workers = num_workers # increase for more efficiency (parallel)
        self._status = self._solver.Solve(self._model)

        # translate status
        solstats = SolverStats()
        if self._status == ort.FEASIBLE:
            solstats.status = ExitStatus.FEASIBLE
        elif self._status == ort.OPTIMAL:
            solstats.status = ExitStatus.OPTIMAL
        else:
            raise NotImplementedError
        # TODO, runtime?

        if self._status == ort.FEASIBLE or self._status == ort.OPTIMAL:
            # TODO, use a decorator for .value again so that can look like propety but is function
            # fill in variables
            for var in self.varmap:
                var._value = self._solver.Value(self.varmap[var])

        return solstats

    def post_expression(self, expr):
        #if is_any_list(expr):

        #if not isinstance(expr, Expression):

        #args_str = [self.convert_expression(e) for e in expr.args]

        # standard expressions: comparison, operator, element
        if isinstance(expr, Comparison):
            print(expr)
            raise NotImplementedError


        elif isinstance(expr, Operator):
            printmap = {'and': '/\\', 'or': '\\/',
                        'sum': '+', 'sub': '-',
                        'mul': '*', 'div': '/', 'pow': '^'}
            args = [self.varmap[var] for var in expr.args]
            if expr.name == 'or':
                self._model.AddBoolOr(args)
            elif expr.name == 'and':
                self._model.AddBoolAnd(args)
            else:
                print(expr.name, type(expr), expr)
                raise NotImplementedError


        elif isinstance(expr, Element):
            subtype = "int"
            # TODO: need better bool check... is_bool() or type()?
            if all((v == 1) is v for v in iter(expr.args[0])):
                subtype = "bool"
            print(expr.name, type(expr), expr)
            raise NotImplementedError
        

        # rest: global constraints
        elif expr.name == 'alldifferent':
           self._model.AddAllDifferent(expr) 


        elif expr.name.endswith('circuit'): # circuit, subcircuit
            print(expr.name, type(expr), expr)
            raise NotImplementedError

        else:
            # TODO: what is default action? how to catch if not supported?
            print(expr.name, type(expr), expr)
            raise NotImplementedError
        
        

