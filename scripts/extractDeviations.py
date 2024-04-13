# 

# extract the deviations state transitions from the diff Models
# usage: python3 extractDeviations.py -d 

import argparse
import networkx as nx
import pydot
import os

class State_trans:
    def __init__(self, source_node, target_node, input, color) -> None:
        self.source_node = source_node
        self.target_node = target_node
        self.input = input
        self.color = color

# open the dot file and create a graph with it
def dot_to_graph(dot_file):
    graph = nx.DiGraph()
    deviating_state_trans = []

    with open(dot_file, 'r') as f:
        dot_graph = pydot.graph_from_dot_data(f.read())[0]

        for edge in dot_graph.get_edges():
            source_node = edge.get_source()
            target_node = edge.get_destination()
            weight = 1
            input = edge.get_attributes().get('label', '') # Get edge label if available
            color = edge.get_attributes().get('color', '')
            graph.add_edge(source_node, target_node, weight=float(weight), label=input)

            if(color == 'red' or color == 'green'):
                deviating_state_tran = State_trans(source_node, target_node, input, color)
                deviating_state_trans.append(deviating_state_tran)
    
    return graph, deviating_state_trans

# get the shortest path to the source of the deviating edge
def find_shortest_path_to_edge(graph, source_node, target_node):
    shortest_path = nx.shortest_path(graph, source_node, target_node)
    return shortest_path

def identify_starting_state(dot_file, graph):
    starting_state = None

    with open(dot_file, 'r') as f:
        lines = f.readlines()

        for node in graph.nodes():
            incoming_edge = " -> " + str(node) + "\t"
            is_starting_state = True

            for line in lines:
                if(incoming_edge in line):
                    is_starting_state = False
                    break
                
            if(is_starting_state):
                outgoing_edge = "\t" + str(node) + " -> "

                for line in lines:
                    if(outgoing_edge in line and "[key=0];" in line):
                        if(starting_state == None):
                            starting_state = node
                        # else:
                        #     print("Error: there are more than 1 starting state in the graph")
    
    return starting_state

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", type=str, required=True, help="Directory that store all the diff models.")
    args = parser.parse_args()

    for file in os.listdir(args.dir):
        if(".dot" in file):
            if(args.dir[-1] != '/'):
                args.dir = args.dir + '/'
            
            filepath = args.dir + file
            all_deviating_input_seq = []
            count = 0

            # get the graph and all deviating state transitions
            graph, deviating_state_trans = dot_to_graph(filepath)

            # identify the start state
            starting_state = identify_starting_state(filepath, graph)

            for state_tran in deviating_state_trans:
                deviating_input_seq = []

                # get the shortest path to the source of the green/red edges
                shortest_path = find_shortest_path_to_edge(graph, starting_state, state_tran.source_node)

                # the input sequence of the deviation will be shortest path to source of the green/red edges + the input (label)
                for i in range(len(shortest_path) - 1):
                    source_node = shortest_path[i]
                    target_node = shortest_path[i + 1]
                    input = graph.edges[source_node, target_node]['label'].replace('"', '')
                    deviating_input_seq.append(input)
                
                deviating_input_seq.append(state_tran.input.replace('"', ''))
                deviating_input_seq.remove("")
                deviating_input_seq = str(deviating_input_seq) + "\n"

                if(deviating_input_seq not in all_deviating_input_seq):
                    all_deviating_input_seq.append(deviating_input_seq)

                # print(deviating_input_seq)
                count += 1

            # write all the state transition to file
            deviating_file_name = None
            
            if("-B-" in file):
                deviating_file_name = "1_B_deviating_state_trans.txt"
            elif("-BWR-" in file):
                deviating_file_name = "1_BWR_deviating_state_trans.txt"
            elif("-BWCA-" in file):
                deviating_file_name = "1_BWCA_deviating_state_trans.txt"
            elif("-BWRCA-" in file):
                deviating_file_name = "1_BWRCA_deviating_state_trans.txt"
            elif("-PSK-" in file):
                deviating_file_name = "1_PSK_deviating_state_trans.txt"
            
            if(deviating_file_name != None):
                deviating_filepath = args.dir + deviating_file_name

                if(os.path.exists(deviating_filepath)):
                    lines = []

                    with open(deviating_filepath, 'r') as f:
                        lines = f.readlines()

                        for input_seq in all_deviating_input_seq:
                            if(input_seq not in lines):
                                lines.append(input_seq)
                    
                    with open(deviating_filepath, 'w') as f:
                        lines = sorted(lines)
                        for line in lines:
                            f.write(line)
                else:
                    with open(deviating_filepath, 'w') as f:
                        all_deviating_input_seq = sorted(all_deviating_input_seq)

                        for input_seq in all_deviating_input_seq:
                            f.write(input_seq)

if __name__ == "__main__":
    main()