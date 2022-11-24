from gurobipy import Model

m = Model("trs0")

# Très grand nombre
M = 1000000000

n_machines = 10
n_operators = 10
n_jobs = 10
n_tasks_per_job = [i for i in range(10)]
p={}

### Decision variables
# beginning of tasks of jobs
B = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'b_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# ending of tasks of jobs
# c = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'c_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# tardiness of jobs
T = {j : m.addVar(vtype = GRB.INTEGER, name = f't_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}
U = {(j,k) : m.addVar(vtype = GRB.BINARY, name = f'u_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# Task-machine assignment
M = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'm_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# Task-operator assignment
O = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'o_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# One Task indicator
Y = {(j,k,jp,kp) : m.addVar(vtype = GRB.BINARY, name = f'o_{j}_{k}_{jp}_{kp}') for j in range(n_jobs) for k in range(n_tasks_per_job[j]) for jp in range(n_jobs) for kp in range(n_tasks_per_job[jp])}


for j in range(n_jobs):
  for k in  range(1,n_tasks_per_job[j]):
    m.addConstr(B[(j,k)] >= B[(j,k-1)]+p[(k,j)])