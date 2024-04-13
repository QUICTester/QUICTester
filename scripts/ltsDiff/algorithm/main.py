'''Main module'''
import getopt
import sys
import warnings

import networkx as nx

from fsm import FSMDiff, SMT_SOLVERS
from read_pairs import read_pairs
import fsm
import debug


def main():
    '''Main function for reading the commandline parameters and execution the FSM_diff algorithm'''
    k_value = 0.5
    threshold = 0.2
    ratio = 1
    matching_file = None
    reference_model = None
    updated_model = None
    reference_filename = None
    updated_filename = None
    output_file = "out.dot"
    try:
        arguments = getopt.getopt(sys.argv[1:],"idelphs:k:t:r:m:o:",["time","debug","equation","log","performance","help","k-pairs","smt","k_value","threshold","ratio","matching-file","ref=", "upd=", "out="])

        for current_arg, current_val in arguments[0]:
            if current_arg in ("-s", "--smt"):
                if current_val in SMT_SOLVERS:
                    fsm.current_solver = current_val
                else:
                    print("invalid smt-solver")
                    return
            elif current_arg in ("-d", "--debug"):
                fsm.debug = True
            elif current_arg in ("-i", "--time"):
                fsm.timing = True
            elif current_arg in ("-p", "--performance"):
                fsm.performance = True
            elif current_arg in ("-l", "--log"):
                fsm.logging = True
            elif current_arg in ("-k", "--k_value"):
                k_value = float(current_val)
            elif current_arg in ("-t", "--threshold"):
                threshold = float(current_val)
            elif current_arg in ("-r", "--ratio"):
                ratio = float(current_val)
            elif current_arg in ("--k-pairs"):
                fsm.k_pairs_output = True
            elif current_arg in ("-e", "--equation"):
                fsm.equation = True
            elif current_arg in ("-m","--matching-file"):
                matching_file = current_val
            elif current_arg in ("--ref"):
                reference_model = nx.drawing.nx_agraph.read_dot(current_val)
                reference_filename = current_val
            elif current_arg in ("-o", "--out"):
                if current_val.split(".")[-1] == "dot":
                    output_file = current_val
                else:
                    warnings.warn("output file needs to end on .dot, default out.dot is used instead")
            elif current_arg in ("--upd"):
                updated_model = nx.drawing.nx_agraph.read_dot(current_val)
                updated_filename = current_val
            elif current_arg in ("-h", "--help"):
                print("Usage: main.py --ref=<reference dot model> --upd=<updated dot model> [-l (add logging in out file) -d (print smt) -e (print linear equation output) -i (print time smt takes) -p (performance matrix) -o <output file> -s <smt-solver> -k <k value> -t <threshold value> -r <ratio value> -m <matching file>]")
                print("<smt-solver> options:")
                for solver in SMT_SOLVERS:
                    print('\t' + solver)
                return
    except getopt.error as err:
        print(str(err))
    debug.debug_file = output_file
    if (not reference_model or not updated_model):
        print("Model not set")
        return

    fsm.output_file = output_file.split(".dot")[0] + ".txt"
    
    matching_pairs = None
    if matching_file is not None:
        matching_pairs = read_pairs(matching_file)

    for edge in reference_model.edges.data():
        if not "label" in edge[2]:
            edge[2]["label"] = ""
    for edge in updated_model.edges.data():
        if not "label" in edge[2]:
            edge[2]["label"] = ""

    graph = FSMDiff().algorithm(reference_model,updated_model,k_value,threshold,ratio,matching_pairs)
    if fsm.logging:
        for idx,val in {"Reference":reference_filename, "Updated":updated_filename, "Output":output_file}.items():
            graph.graph.setdefault(idx,{})
            graph.graph[idx]["Filename"] = val
    nx.drawing.nx_agraph.write_dot(graph,output_file)

if __name__ == "__main__":
    main()
