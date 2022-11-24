from functools import reduce
import re
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


json = parser("sujet/tiny.json")

from gurobipy import Model

m = Model("trs0")

# Très grand nombre
inf = 1000000000


n_machines = json["parameters"]["size"]["nb_machines"]  ##Nombre de machines
n_operators = json["parameters"]["size"]["nb_operators"]  ##Nombre d'opérateurs
n_jobs = json["parameters"]["size"]["nb_jobs"]  ##Nombre de jobs
job_names = [json["jobs"][i]["job"] for i in range(n_jobs)]  ##Nom effectif des jobs


tasks_per_job = {}  ##Dictio des tâches par job (clé = nom du job)
for i in range(n_jobs):
    tasks_per_job[json["jobs"][i]["job"]] = json["jobs"][i][
        "sequence"
    ]  ##Nombre de tâches par job

w = {}  ##Dictio des poids des job (clé = nom du job)
d = {}  ##Dictio des durées des jobs (clé = nom du job)
r = {}  ##Dictio des ressources des jobs (clé = nom du job)
for i in range(n_jobs):
    w[json["jobs"][i]["job"]] = json["jobs"][i]["weight"]  ##Poids des jobs
    d[json["jobs"][i]["job"]] = json["jobs"][i][
        "due_date"
    ]  ##Date limite de fin des jobs
    r[json["jobs"][i]["job"]] = json["jobs"][i][
        "release_date"
    ]  ##Date de début des jobs

p_tasks = {}  ##Dictio des durées des tâches (clé = nom de la tâche)
op_tasks = {}  ##Dictio des opérateurs des tâches (clé = nom de la tâche)
m_tasks = {}  ##Dictio des machines des tâches (clé = nom de la tâche)
for i in tasks_per_job:
    for j in tasks_per_job[i]:
        p_tasks[j] = json["tasks"][j][
            "processing_time"
        ]  ##Dictionnaire des processing time par tâche
        m_tasks[j] = json["tasks"][j][
            "machine"
        ]  ##Dictionnaire des machine par id de tâche
        op_tasks[j] = json["tasks"][j][
            "operator"
        ]  ##Dictionnaire des opérateurs par id de tâche


### Decision variables

# beginning of tasks of jobs
B = {
    (j, k): m.addVar(vtype=GRB.INTEGER, name=f"b_{j}_{k}")
    for j in range(n_jobs)
    for k in range(tasks_per_job[j])
}

# ending of tasks of jobs
# c = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'c_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# tardiness of jobs
T = {j: m.addVar(vtype=GRB.INTEGER, name=f"t_{j}") for j in range(n_jobs)}
U = {j: m.addVar(vtype=GRB.BINARY, name=f"u_{j}") for j in range(n_jobs)}

# Task-machine assignment
M = {
    (j, k): m.addVar(vtype=GRB.INTEGER, name=f"m_{j}_{k}")
    for j in range(n_jobs)
    for k in (tasks_per_job[j])
}

# Task-operator assignment
O = {
    (j, k): m.addVar(vtype=GRB.INTEGER, name=f"o_{j}_{k}")
    for j in range(n_jobs)
    for k in (tasks_per_job[j])
}

# One Task indicator
X = {
    (j, k): m.addVar(vtype=GRB.BINARY, name=f"x_{j}_{k}")
    for j in range(n_jobs)
    for k in (tasks_per_job[j])
}  ##X indique si en dessous ou au dessus de l'intervalle de temps

Y = {
    (j, k): m.addVar(vtype=GRB.BINARY, name=f"y_{j}_{k}")
    for j in range(n_jobs)
    for k in (tasks_per_job[j])
}  ##Y indique si la tâche est réalisée ou non par la même machine

Z = {
    (j, k): m.addVar(vtype=GRB.BINARY, name=f"z_{j}_{k}")
    for j in range(n_jobs)
    for k in (tasks_per_job[j])
}  ##Z indique si la tâche est réalisée ou non par le même opérateur

# Vars A1, A2, A3, A4

A1 = m.addVar(vtype=GRB.BINARY, name=f"A1")
A2 = m.addVar(vtype=GRB.BINARY, name=f"A2")
A3 = m.addVar(vtype=GRB.BINARY, name=f"A3")
A4 = m.addVar(vtype=GRB.BINARY, name=f"A4")


### Constraints
for j in range(1, n_jobs):
    for k in range(2, tasks_per_job[j] + 1):
        m.addConstr(B[(j, k)] >= B[(j, k - 1)] + p_tasks[(j, k)])

for j in range(1, n_jobs + 1):
    m.addConstr(B[(j, 1)] >= r[j])

for j in range(1, n_jobs + 1):
    m.addConstr(T[j] >= 0)
    m.addConstr(T[j] >= B[(j, tasks_per_job[j])] + p[(j, tasks_per_job[j])] - d[j])
    m.addConstr(
        T[j]
        <= B[(j, tasks_per_job[j])]
        + p_tasks[(j, tasks_per_job[j])]
        - d[j]
        + M * (1 - U[j])
    )
    m.addConstr(T[j] <= M * U[j])

for j in range(1, n_jobs):
    for k in range(1, tasks_per_job[j] + 1):
        m.addConstr(B[(j, k)] >= B[(j, k - 1)] + p_tasks[(j, k)])


# Optimize model
m.optimize()

for v in m.getVars():
    print("%s %g" % (v.VarName, v.X))

print("Obj: %g" % m.ObjVal)
