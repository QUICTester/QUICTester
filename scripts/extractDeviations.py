# author: Kian Kai Ang

# extract the deviations state transitions from the diff Models
# usage: python3 extractDeviations.py -d 

import argparse
import networkx as nx
import pydot
import os
import subprocess

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

def extract_output_seq(input_seq, model_path):
    output_seq = []
    current_state = "s0"
    input_seq = input_seq[1:-2]
    input_seq = input_seq.replace('\'', '')
    input_seq = input_seq.replace(' ', '')
    input_seq = input_seq.split(',')
    # print(input_seq)

    # compare against the learned model (NOT optimised model)
    with open(model_path, 'r') as f:
        dot_graph = pydot.graph_from_dot_data(f.read())[0]

        for input in input_seq:
            # print(current_state)
            suffix_added = False
            
            # do not add "_short" and "/" if it is a mapper config input or "initCltHello-"
            # This is because there are multiple cipher suite for initCltHello-
            if('[' not in input[0] and ']' not in input[-1] and "initCltHello-" not in input):
                # if the input does not specify what timeout, use "_short"
                # The main reason we need to add "_short" is because we are extracting from learned model, not optimised model  
                # The main reason why we add "/" is to prevent we detect the output as the input (e.g. hndCertificate from server)
                if("_long" not in input or "_short" not in input):
                    input += "_short/"
                    suffix_added = True
                else:
                    input += '/'

            for edge in dot_graph.get_edges():
                source_node = edge.get_source()

                if(source_node == current_state):
                    label = edge.get_attributes().get('label', '') # Get edge label if available

                    if(input in label):
                        if(suffix_added):
                            label = label.replace("_short", "")
                        output_seq.append(label)
                        current_state = edge.get_destination()
                        break

    return output_seq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", type=str, required=True, help="Directory that store all the diff models.")
    parser.add_argument("-s", "--server", type=str, required=True, help="Name of the server implementation.")
    args = parser.parse_args()

    # extract the output sequence of each deviating input sequences
    possible_deviating_file_name = ["1_B_deviating_state_trans.txt", "1_BWR_deviating_state_trans.txt", "1_BWCA_deviating_state_trans.txt", "1_BWRCA_deviating_state_trans.txt", "1_PSK_deviating_state_trans.txt"]
    
    if(args.dir[-1] != '/'):
        args.dir = args.dir + '/'
    
    for file in possible_deviating_file_name:
        if(os.path.exists(args.dir + file)):
            os.remove(args.dir + file)
    
    for file in os.listdir(args.dir):
        if(".dot" in file):    
            filepath = args.dir + file
            all_deviating_input_seq = []
            count = 0

            # get the graph and all deviating state transitions
            graph, deviating_state_trans = dot_to_graph(filepath)

            # identify the start state
            starting_state = identify_starting_state(filepath, graph)

            for state_tran in deviating_state_trans:
                deviating_input_seq = []

                try:
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
                except nx.exception.NetworkXNoPath as e:
                    # print(filepath)
                    # print("starting: " + starting_state)
                    # print("state trans: " + str(state_tran.input))
                    # print()
                    continue


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
            
            # convert .dot to pdf file
            try:
                new_filepath = filepath.replace(".dot", ".pdf")
                subprocess.run(["dot", "-Tpdf", filepath, "-o", new_filepath], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")
    
    for deviating_file_name in possible_deviating_file_name:
        deviating_filepath = args.dir + deviating_file_name

        if(os.path.exists(deviating_filepath)):
            all_deviating_input_seq = []
            model_path = args.dir
            
            if(model_path[-1] == '/'):
                model_path = model_path[:-1]

            model_path = model_path.split(os.path.sep)
            model_path = os.path.sep.join(model_path[:-1])
            model_path = model_path + "/CS-temporal/" + args.server

            # check which file exist, results generate from local or results generate from docker file?
            if("_B_" in deviating_file_name):
                if(os.path.exists(model_path + "-B-0/learnedModel.dot")):
                    model_path += "-B-0/learnedModel.dot" # results generate from local
                else:
                    model_path += "-B-B-0/learnedModel.dot" # results generate from docker
            elif("_BWR_" in deviating_file_name):
                if(os.path.exists(model_path + "-BWR-0/learnedModel.dot")):
                    model_path += "-BWR-0/learnedModel.dot"
                else:
                    model_path += "-BWR-BWR-0/learnedModel.dot"
            elif("_BWCA_" in deviating_file_name):
                if(os.path.exists(model_path + "-BWCA-0/learnedModel.dot")):
                    model_path += "-BWCA-0/learnedModel.dot"
                else:
                    model_path += "-BWCA-BWCA-0/learnedModel.dot"
            elif("_BWRCA_" in deviating_file_name):
                if(os.path.exists(model_path + "-BWRCA-0/learnedModel.dot")):
                    model_path += "-BWRCA-0/learnedModel.dot"
                else:
                    model_path += "-BWRCA-BWRCA-0/learnedModel.dot"
            elif("_PSK_" in deviating_file_name):
                if(os.path.exists(model_path + "-PSK-0/learnedModel.dot")):
                    model_path += "-PSK-0/learnedModel.dot"
                else:
                    model_path += "-PSK-PSK-0/learnedModel.dot"

            # get all deviating input sequences
            with open(deviating_filepath, 'r') as f:
                all_deviating_input_seq = f.readlines()
            
            # extract output sequence for each deviating input sequence and write to the file
            with open(deviating_filepath, 'w') as f:
                for deviating_input_seq in all_deviating_input_seq:
                    output_seq = extract_output_seq(deviating_input_seq, model_path)
                    f.write("Input sequences: " + deviating_input_seq + "\n")
                    f.write("State transitions: " + str(output_seq) + "\n")
                    f.write("###############################################################################################################\n\n")

if __name__ == "__main__":
    main()