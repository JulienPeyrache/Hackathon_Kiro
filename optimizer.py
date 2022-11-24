from functools import reduce
import re
import json
from gurobipy import *
import pprint


def array_parser(data):
    if data[0] != "[":
        return None
    parse_list = []
    data = data[1:].strip()
    while len(data):
        res = value_parser(data)
        if res is None:
            return None
        parse_list.append(res[0])
        data = res[1].strip()
        if data[0] == "]":
            return [parse_list, data[1:].strip()]
        res = comma_parser(data)
        if res is None:
            return None
        data = res[1].strip()

def boolean_parser(data):
    if data[0:4] == "true":
        return [True, data[4:].strip()]
    elif data[0:5] == "false":
        return [False, data[5:].strip()]


def colon_parser(data):
    if data[0] == ":":
        return [data[0], data[1:].lstrip()]


def comma_parser(data):
    if data and data[0] == ",":
        return [data[0], data[1:].strip()]


def null_parser(data):
    if data[0:4] == "null":
        return [None, data[4:].strip()]


def number_parser(data):
    regex_find = re.findall("^(-?(?:[0-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)", data)
    if not regex_find:
        return None
    pos = len(regex_find[0])
    try:
        return [int(regex_find[0]), data[pos:].strip()]
    except ValueError:
        return [float(regex_find[0]), data[pos:].strip()]


def object_parser(data):
    if data[0] != "{":
        return None
    parse_dict = {}
    data = data[1:].strip()
    while data[0] != "}":
        res = string_parser(data)
        if res is None:
            return None
        id = res[0]
        res = colon_parser(res[1].strip())
        if res is None:
            return None
        res = value_parser(res[1].strip())
        if res is None:
            return None
        parse_dict[id] = res[0]
        data = res[1].lstrip()
        res = comma_parser(data)
        if res:
            data = res[1].strip()
    return [parse_dict, data[1:]]


def string_parser(data):
    if data[0] == '"':
        data = data[1:]
        pos = data.find('"')
        return [data[:pos], data[pos + 1 :].strip()]


def all_parsers(*args):
    return lambda data: (reduce(lambda f, g: f if f(data) else g, args)(data))


value_parser = all_parsers(
    null_parser,
    number_parser,
    boolean_parser,
    string_parser,
    object_parser,
    array_parser,
)


def parser(filename):
    with open(filename, "r") as f:
        data = f.read()
    res = value_parser(data.strip())
    try:
        return res[0]
    except TypeError:
        print(None)

f="sujet/medium.json"
json_data = parser(f)

mod = Model("trs0")

# Très grand nombre
inf = 1000000000

beta = json_data["parameters"]["costs"]["tardiness"]
alpha = json_data["parameters"]["costs"]["unit_penalty"]
n_machines = json_data["parameters"]["size"]["nb_machines"]  ##Nombre de machines
n_operators = json_data["parameters"]["size"]["nb_operators"]  ##Nombre d'opérateurs
n_jobs = json_data["parameters"]["size"]["nb_jobs"]  ##Nombre de jobs
job_names = [json_data["jobs"][i]["job"] for i in range(n_jobs)]  ##Nom effectif des jobs


tasks_per_job = {}  ##Dictio des tâches par job (clé = nom du job)
for i in range(n_jobs):
    tasks_per_job[json_data["jobs"][i]["job"]] = json_data["jobs"][i][
        "sequence"
    ]  ##Nombre de tâches par job

w = {}  ##Dictio des poids des job (clé = nom du job)
d = {}  ##Dictio des durées des jobs (clé = nom du job)
r = {}  ##Dictio des ressources des jobs (clé = nom du job)
for i in range(n_jobs):
    w[json_data["jobs"][i]["job"]] = json_data["jobs"][i]["weight"]  ##Poids des jobs
    d[json_data["jobs"][i]["job"]] = json_data["jobs"][i][
        "due_date"
    ]  ##Date limite de fin des jobs
    r[json_data["jobs"][i]["job"]] = json_data["jobs"][i][
        "release_date"
    ]  ##Date de début des jobs

p_tasks = {}  ##Dictio des durées des tâches (clé = nom de la tâche)
op_tasks = {}  ##Dictio des opérateurs des tâches (clé = nom de la tâche)
m_tasks = {}  ##Dictio des machines des tâches (clé = nom de la tâche)
op_task_machine = (
    {}
)  ##Dictio des opérateurs par tâche et par machine (clé = nom de la tâche puis de la machine)
for i in tasks_per_job:
    for j in tasks_per_job[i]:
        p_tasks[j] = json_data["tasks"][j - 1]["processing_time"]
        m_tasks[j] = [
            json_data["tasks"][j-1]["machines"][k-1]["machine"]
            for k in range(len(json_data["tasks"][j - 1]["machines"]))
        ]
        op_task_machine[j] = {}
        for k in json_data["tasks"][j - 1]["machines"]:
            op_task_machine[j][k["machine"]] = k["operators"]
### Decision variables

# beginning of tasks of jobs
B = {
    k: mod.addVar(vtype=GRB.INTEGER, name=f"b_{k}")
    for j in job_names
    for k in tasks_per_job[j]
}

# tardiness of jobs
T = {j: mod.addVar(vtype=GRB.INTEGER, name=f"t_{j}") for j in job_names}
U = {j: mod.addVar(vtype=GRB.BINARY, name=f"u_{j}") for j in job_names}

# Task-machine assignment
M = {
    k: mod.addVar(vtype=GRB.INTEGER, name=f"m_{k}")
    for j in job_names
    for k in tasks_per_job[j]
}

# Task-operator assignment
O = {
    k: mod.addVar(vtype=GRB.INTEGER, name=f"o_{j}_{k}")
    for j in job_names
    for k in tasks_per_job[j]
}

# One Task indicator
X = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"x_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}  ##X indique si en dessous ou au dessus de l'intervalle de temps

Y = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"y_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}  ##Y indique si la tâche est réalisée ou non par la même machine

Z = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"z_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}  ##Z indique si la tâche est réalisée ou non par le même opérateur

# Vars A1, A2, A3, A4
A1 = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"a1_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}

A2 = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"a2_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}

A3 = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"a3_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}
A4 = {
    (k, kp): mod.addVar(vtype=GRB.BINARY, name=f"a4_{j}_{k}_{jp}_{kp}")
    for j in job_names
    for k in tasks_per_job[j]
    for jp in job_names
    for kp in tasks_per_job[jp]
}
Lambda_o = {
    (k, m, op): mod.addVar(vtype=GRB.BINARY, name=f"lambda_o_{k}_{m}_{op}")
    for j in job_names
    for k in tasks_per_job[j]
    for m in m_tasks[k]
    for op in op_task_machine[k][m]
}

Lambda_m = {
    (k, m): mod.addVar(vtype=GRB.BINARY, name=f"lambda_m_{k}_{m}")
    for j in job_names
    for k in tasks_per_job[j]
    for m in m_tasks[k]
}

### Constraints
for j in job_names:
    for i in range(1, len(tasks_per_job[j])):
        mod.addConstr(
            B[tasks_per_job[j][i]]
            >= B[tasks_per_job[j][i - 1]] + p_tasks[tasks_per_job[j][i]]
        )


for j in job_names:
    mod.addConstr(B[tasks_per_job[j][0]] >= r[j])

for j in job_names:
    mod.addConstr(T[j] >= 0)
    mod.addConstr(
        T[j] >= B[tasks_per_job[j][-1]] + p_tasks[tasks_per_job[j][-1]] - d[j]
    )
    mod.addConstr(
        T[j]
        <= B[tasks_per_job[j][-1]]
        + p_tasks[tasks_per_job[j][-1]]
        - d[j]
        + inf * (1 - U[j])
    )
    mod.addConstr(T[j] <= inf * U[j])

for j in job_names:
    for k in tasks_per_job[j]:
        for jp in job_names:
            for kp in tasks_per_job[jp]:
                if kp!=k:
                    mod.addConstr(B[kp] <= B[k] - 1 + inf * X[(k, kp)] + inf * Y[(k, kp)])
                    mod.addConstr(B[kp] >= B[k] + p_tasks[k] - inf * (1 - X[(k, kp)]) - inf * Y[(k, kp)])
                    mod.addConstr(B[kp] <= B[k] - 1 + inf * X[(k, kp)] + inf * Z[(k, kp)])
                    mod.addConstr(B[kp] >= B[k] + p_tasks[k] - inf * (1 - X[(k, kp)]) - inf * Z[(k, kp)])

                    mod.addConstr(M[k] - M[kp] >= -inf * A1[(k, kp)] + A2[(k, kp)])
                    mod.addConstr(M[k] - M[kp] <= -A1[(k, kp)] + inf * A2[(k, kp)])
                    mod.addConstr(A1[(k, kp)] + A2[(k, kp)] <= 1)
                    mod.addConstr(Y[(k, kp)] == A1[(k, kp)] + A2[(k, kp)])

                    mod.addConstr(A3[(k, kp)] + A4[(k, kp)] <= 1)
                    mod.addConstr(Z[(k, kp)] == A1[(k, kp)] + A2[(k, kp)])
                    mod.addConstr(O[k] - O[kp] >= -inf * A3[(k, kp)] + A4[(k, kp)])
                    mod.addConstr(O[k] - O[kp] <= -A3[(k, kp)] + inf * A4[(k, kp)])

# ##Linexpr constraints

for j in job_names:
    for k in tasks_per_job[j]:
        machine = LinExpr()
        lambd = LinExpr()
        for m in m_tasks[k]:
            machine += Lambda_m[(k, m)] * m
            lambd += Lambda_m[(k, m)]
        mod.addConstr(M[k] == machine)
        mod.addConstr(lambd == 1)

for j in job_names:
    for k in tasks_per_job[j]:
        operateur = LinExpr()
        lambd = LinExpr()
        for m in m_tasks[k]:
            for op in op_task_machine[k][m]:
                operateur += Lambda_o[(k, m, op)] * op
                lambd += Lambda_o[(k, m, op)]
        mod.addConstr(O[k] == operateur)
        mod.addConstr(lambd == 1)


# Cost function
cost = LinExpr()
for j in job_names:
    cost += w[j] * (B[tasks_per_job[j][-1]] + p_tasks[tasks_per_job[j][-1]] + alpha*U[j] + beta*T[j])
mod.setObjective(cost, GRB.MINIMIZE)

# Optimize model
mod.optimize()

# for v in mod.getVars():
#     print("%s %g" % (v.VarName, v.X))

print("Obj: %g" % mod.ObjVal)

def jsonify(m):
    # m is a gurobi model
    # returns a json_data object
    # with the form :
    # [{"task" : k, "start":B[k] "machine" : M[k], "operator" : O[k]} for k in tasks]
    # print(m.getVars())
    dico = {}
    for j in job_names:
        for k in tasks_per_job[j]:
            dico[k] = {"task": k}
            dico[k]["start"] = B[k].x
            dico[k]["machine"] = M[k].x
            dico[k]["operator"] = O[k].x
    jsonStr = json.dumps([dico[k] for k in dico])
    return jsonStr

s=jsonify(mod)
g=open(f,"w")
g.write(s)