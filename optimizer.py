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
<<<<<<< HEAD
def parser():
    with open("sujet/tiny.json", "r") as f:
=======


def parser(filename):
    with open(filename, "r") as f:
>>>>>>> 912c9e5 (variablesé)
        data = f.read()
    res = value_parser(data.strip())
    try:
        return res[0]
    except TypeError:
        print(None)

json = parser()

from gurobipy import Model

m = Model("trs0")

# Très grand nombre
M = 1000000000


n_machines = json["parameters"]["size"]["nb_machines"] ##Nombre de machines
n_operators = json["parameters"]["size"]["nb_operators"] ##Nombre d'opérateurs
n_jobs = json["parameters"]["size"]["nb_jobs"] ##Nombre de jobs
n_tasks_per_job = [len(json["jobs"][i]["sequence"])i for i in range(1,n_jobs+1)] ##Nombre de tâches par job
n_tasks = sum(n_tasks_per_job) ##Nombre de tâches
weight_per_job = [json["jobs"][i]["weight"] for i in range(1,n_jobs+1)] ##Poids des jobs
due_date_per_job = [json["jobs"][i]["due_date"] for i in range(1,n_jobs+1)] ##Date d'échéance des jobs
release_date_per_job = [json["jobs"][i]["release_date"] for i in range(1,n_jobs+1)] ##Date de début des jobs
jobs = [json["jobs"][i]["sequence"] for i in range(1,n_jobs+1)] ##Dictionnaire des tâches par job
p_tasks = [json["tasks"][i]["processing_time"] for i in range(1,n_tasks+1)] ##Dictionnaire des processing time par tâche
m_tasks = [json["tasks"][i]["machine"] for i in range(1,n_tasks+1)] ##Dictionnaire des machine par id de tâche
op_tasks = [json["tasks"][i]["operator"] for i in range(1,n_tasks+1)] ##Dictionnaire des opérateurs par id de tâche

### Decision variables
# beginning of tasks of jobs
B = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'b_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# ending of tasks of jobs
# c = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'c_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# tardiness of jobs
T = {j : m.addVar(vtype = GRB.INTEGER, name = f't_{j}') for j in range(n_jobs)}
U = {j : m.addVar(vtype = GRB.BINARY, name = f'u_{j}') for j in range(n_jobs)}

# Task-machine assignment
M = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'm_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# Task-operator assignment
O = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'o_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# One Task indicator
Y = {(j,k,jp,kp) : m.addVar(vtype = GRB.BINARY, name = f'o_{j}_{k}_{jp}_{kp}') for j in range(n_jobs) for k in range(n_tasks_per_job[j]) for jp in range(n_jobs) for kp in range(n_tasks_per_job[jp])}


for j in range(1,n_jobs):
  for k in  range(2,n_tasks_per_job[j]+1):
    m.addConstr(B[(j,k)] >= B[(j,k-1)]+p[(j,k)])

for j in range(1,n_jobs+1):
  m.addConstr(B[(j,1)] >= r[j])

for j in range(1,n_jobs+1):
  m.addConstr(T[j] >= 0)
  m.addConstr(T[j] >= B[(j,n_tasks_per_job[j])] + p[(j,n_tasks_per_job[j])] - d[j])
  m.addConstr(T[j] <= B[(j,n_tasks_per_job[j])] + p[(j,n_tasks_per_job[j])] - d[j] + M*(1-U[j]))
  m.addConstr(T[j] <= M*U[j])

