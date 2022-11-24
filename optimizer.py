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


def parser():
    with open("sujet/tiny.json", "r") as f:
        data = f.read()
    res = value_parser(data.strip())
    try:
        return(res[0])
    except TypeError:
        print(None)


json = parser()

from gurobipy import *

m = Model("trs0")

# Très grand nombre
M = 1000000000

n_machines = parser[]
n_operators = 10
n_jobs = 10
n_tasks_per_job = [i for i in range(10)]

### Decision variables
# beginning of tasks of jobs
b = {
    (j, k): m.addVar(vtype=GRB.INTEGER, name=f"b_{j}_{k}")
    for j in range(n_jobs)
    for k in range(n_tasks_per_job[j])
}

# ending of tasks of jobs
# c = {(j,k) : m.addVar(vtype = GRB.INTEGER, name = f'c_{j}_{k}') for j in range(n_jobs) for k in range(n_tasks_per_job[j])}

# tardiness of jobs
t = {
    j: m.addVar(vtype=GRB.INTEGER, name=f"t_{j}_{k}")
    for j in range(n_jobs)
    for k in range(n_tasks_per_job[j])
}
u = {
    (j, k): m.addVar(vtype=GRB.BINARY, name=f"u_{j}_{k}")
    for j in range(n_jobs)
    for k in range(n_tasks_per_job[j])
}

# Task-machine assignment
m = {
    (j, k): m.addVar(vtype=GRB.INTEGER, name=f"m_{j}_{k}")
    for j in range(n_jobs)
    for k in range(n_tasks_per_job[j])
}

# Task-operator assignment
o = {
    (j, k): m.addVar(vtype=GRB.INTEGER, name=f"o_{j}_{k}")
    for j in range(n_jobs)
    for k in range(n_tasks_per_job[j])
}

# One Task indicator
y = {
    (j, k, jp, kp): m.addVar(vtype=GRB.BINARY, name=f"o_{j}_{k}_{jp}_{kp}")
    for j in range(n_jobs)
    for k in range(n_tasks_per_job[j])
    for jp in range(n_jobs)
    for kp in range(n_tasks_per_job[jp])
}
