def jsonify(m):
    # m is a gurobi model
    # returns a json object
    # with the form :
    # [{"task" : k, "start":B[k] "machine" : M[k], "operator" : O[k]} for k in tasks]
    # print(m.getVars())
    dico = {}
    for v in m.getVars():
        print("%s %g" % (v.VarName, v.X))
        if v.VarName[:3] == "b_":
            k = int(v.VarName[3::])
            if not (k in dico):
                dico[k] = {"task": k}
            dico[k]["start"] = v.X
        if v.VarName[:3] == "m_":
            k = int(v.VarName[3::])
            if not (k in dico):
                dico[k] = {"task": k}
            dico[k]["machine"] = v.X
        if v.VarName[:3] == "o_":
            k = int(v.VarName[3::])
            if not (k in dico):
                dico[k] = {"task": k}
            dico[k]["operator"] = v.X
    jsonStr = json.dumps([dico[k] for k in dico])
    return jsonStr
