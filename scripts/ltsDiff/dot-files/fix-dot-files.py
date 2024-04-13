'''
Some models don't have an incoming edge for some states, this causes a problem when solving the linear equations with the umfpack solver

Therefore we add a self loop to the models that don't have an incoming edge.
'''


import sys

import networkx as nx



if __name__ == "__main__":
    file = sys.argv[1]
    model = nx.drawing.nx_agraph.read_dot(file)
    for state in model.nodes:
        edges = model.in_edges(state)
        if len(edges) == 0 :
            model.add_edge(state,state,label="Self loop")
    nx.drawing.nx_agraph.write_dot(model,file)