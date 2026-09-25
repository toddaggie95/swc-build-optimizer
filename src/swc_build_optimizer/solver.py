"""Dependency smoke check only. No city optimization is claimed in v0.1."""

from ortools.sat.python import cp_model


def smoke_check() -> dict:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 2, "x")
    model.maximize(x)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.solve(model)
    return {
        "status": solver.status_name(status),
        "objective": solver.objective_value,
        "best_bound": solver.best_objective_bound,
    }
