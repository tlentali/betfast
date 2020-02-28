from __future__ import print_function
from ortools.sat.python import cp_model
import time
import pandas as pd
import datetime


class WeddingChartPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, seats, names, num_tables, num_guests):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0
        self.__start_time = time.time()
        self.__seats = seats
        self.__names = names
        self.__num_tables = num_tables
        self.__num_guests = num_guests

    def OnSolutionCallback(self):
        current_time = time.time()
        objective = self.ObjectiveValue()
        print("Solution %i, time = %f s, objective = %i" %
              (self.__solution_count, current_time - self.__start_time, objective))
        self.__solution_count += 1
        today = datetime.date.today()

        for t in range(self.__num_tables):
            next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=t+1)
            next_friday = next_monday + datetime.timedelta(days=4)

            print("Date %s: " % next_friday.strftime("%Y/%m/%d"))
            for g in range(self.__num_guests):
                if self.Value(self.__seats[(t, g)]):
                    print("  " + self.__names[g])

    def NumSolutions(self):
        return self.__solution_count


def BuildData():
    #
    # Data
    #

    # Easy problem (from the paper)
    # num_tables = 2
    # table_capacity = 10
    # min_known_neighbors = 1

    # Slightly harder problem (also from the paper)
    
    table_capacity = 2
    min_known_neighbors = 1

    # Connection matrix: who knows who, and how strong
    # is the relation
    df = pd.read_csv('../data/input/affinity.csv', sep=';')
    C = df.to_numpy()

    num_tables = int((len(df) / 2) + 1)

    # Names of the guests. B: Bride side, G: Groom side
    names = list(df.columns)
    return num_tables, table_capacity, min_known_neighbors, C, names


def SolveWithDiscreteModel():
    num_tables, table_capacity, min_known_neighbors, C, names = BuildData()

    num_guests = len(C)

    all_tables = range(num_tables)
    all_guests = range(num_guests)

    # Create the cp model.
    model = cp_model.CpModel()

    #
    # Decision variables
    #
    seats = {}
    for t in all_tables:
        for g in all_guests:
            seats[(t, g)] = model.NewBoolVar(
                "guest %i match on dej %i" % (g, t))

    colocated = {}
    for g1 in range(num_guests - 1):
        for g2 in range(g1 + 1, num_guests):
            colocated[(g1, g2)] = model.NewBoolVar(
                "guest %i match with guest %i" % (g1, g2))

    same_table = {}
    for g1 in range(num_guests - 1):
        for g2 in range(g1 + 1, num_guests):
            for t in all_tables:
                same_table[(g1, g2, t)] = model.NewBoolVar(
                    "guest %i match with guest %i on dej %i" % (g1, g2, t))

    # Objective
    model.Maximize(
        sum(C[g1][g2] * colocated[g1, g2]
            for g1 in range(num_guests - 1)
            for g2 in range(g1 + 1, num_guests)
            if C[g1][g2] > 0))

    #
    # Constraints
    #

    # Everybody seats at one table.
    for g in all_guests:
        model.Add(sum(seats[(t, g)] for t in all_tables) == 1)

    # Tables have a max capacity.
    for t in all_tables:
        model.Add(sum(seats[(t, g)] for g in all_guests) <= table_capacity)

    # Link colocated with seats
    for g1 in range(num_guests - 1):
        for g2 in range(g1 + 1, num_guests):
            for t in all_tables:
                # Link same_table and seats.
                model.AddBoolOr([
                    seats[(t, g1)].Not(), seats[(t, g2)
                                                ].Not(), same_table[(g1, g2, t)]
                ])
                model.AddImplication(same_table[(g1, g2, t)], seats[(t, g1)])
                model.AddImplication(same_table[(g1, g2, t)], seats[(t, g2)])

            # Link colocated and same_table.
            model.Add(
                sum(same_table[(g1, g2, t)] for t in all_tables) == colocated[(g1,
                                                                               g2)])

    # Min known neighbors rule.
    for t in all_tables:
        model.Add(
            sum(same_table[(g1, g2, t)] for g1 in range(num_guests - 1)
                for g2 in range(g1 + 1, num_guests)
                for t in all_tables
                if C[g1][g2] > 0) >= min_known_neighbors)

    # Symmetry breaking. First guest seats on the first table.
    model.Add(seats[(0, 0)] == 1)

    # Solve model.
    solver = cp_model.CpSolver()
    solution_printer = WeddingChartPrinter(
        seats, names, num_tables, num_guests)
    status = solver.SolveWithSolutionCallback(model, solution_printer)

    print("Statistics")
    print("  - conflicts    : %i" % solver.NumConflicts())
    print("  - branches     : %i" % solver.NumBranches())
    print("  - wall time    : %f ms" % solver.WallTime())
    print("  - num solutions: %i" % solution_printer.NumSolutions())


SolveWithDiscreteModel()
