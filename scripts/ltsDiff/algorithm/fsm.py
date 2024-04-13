'''FSM module containing the FSM_diff algorithm'''
from dataclasses import dataclass
import string
from typing import List, Tuple, Dict, final
from time import time
import warnings

from pysmt.shortcuts import Symbol, And, Equals, GE, Plus, Minus, Times, Equals, Real, get_model
from pysmt.typing import REAL
import networkx as nx
from scipy.sparse.linalg import spsolve
import numpy as np
from scipy.sparse import csc_matrix

from debug import print_smtlib, write_k_pairs_to_file

SMT_SOLVERS = ["msat","cvc4","z3","yices"]

current_solver = "umfpack"
debug = False
timing = False
performance = False
logging = False
equation = False
output_file = "out.txt"
k_pairs_output = False

@dataclass
class ComparingStates:
    '''This dataclass holds the states with the matched and non matched transitions'''
    states: Tuple[str,str]
    matching_trans: List[Tuple[Dict,Dict]]
    non_matching_trans: Tuple[List[Dict],List[Dict]]

class Singleton(type):
    '''This class is used to create a singleton instance of the FSM_Diff class'''
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class FSMDiff(metaclass=Singleton):
    '''This is singleton class which impelents the FSM_Diff algorithm'''

    def __init__(self):
        self.out_time = None
        self.in_time = None

    def pair_matching_transition(self,fsm_1,fsm_2,s1,s2,out):
        '''
        Match the transitions of a set of states

        Parameters
        ----------
        fsm_1: nx.MultiDiGraph
        fsm_2: nx.MultiDiGraph
        s1: str
            A state from fsm_1
        s2: str
            A state from fsm_2
        out: bool
            True if it must match on outgoing transitions
            False if must match on incoming transitions

        Returns
        -------
        Intsance of ComparingStates
        '''
        used_trans1 = []
        used_trans2 = []
        state_compare = ComparingStates((s1,s2),[],([],[]))
        for t1 in fsm_1.edges.data():
            if (t1[0] == s1 and out) or (t1[1] == s1 and not out):
                used_trans1.append(t1)
        for t2 in fsm_2.edges.data():
            if (t2[0] == s2 and out) or (t2[1] == s2 and not out):
                used_trans2.append(t2)

        for t1 in used_trans1:
            matched = False
            for t2 in used_trans2:
                if t1[2]["label"] == t2[2]["label"]:
                    state_compare.matching_trans.append((t1,t2))
                    matched = True
            if not matched:
                state_compare.non_matching_trans[0].append(t1)
        for t2 in used_trans2:
            matched = False
            for t1 in used_trans1:
                if t1[2]["label"] == t2[2]["label"]:
                    matched = True
            if not matched:
                state_compare.non_matching_trans[1].append(t2)

        return state_compare

    def matching_transitions(self,fsm_1,fsm_2,out):
        '''
        Run pair_matching_transition with all different pairs possible
        '''
        outcome = []
        for s1 in fsm_1.nodes:
            for s2 in fsm_2.nodes:
                outcome.append(self.pair_matching_transition(fsm_1,fsm_2,s1,s2,out))
        return outcome

    def is_a_match(self, matching_pairs, t1, t2):
        if matching_pairs == None:
            return True # need to pick K
        else:
            if (t1,t2) in matching_pairs:
                return True
            for (m1,m2) in matching_pairs:
                if t1 == m1 or t2 == m2:
                    return False
        return True # If the states are not listed in matching_pairs we pick normal K

    def linear_equation_solver(self, state_pairs, k, out, matching_pairs = None):
        '''
        Solve the linear equation for the FSM_Diff algorithm

        Parameters
        ----------
        state_pairs: list(ComparingStates)
            All matched and unmatched transitions for all the possible pairs
        k: float
            k-value of the FSM_Diff algorithm
        out: bool
            True if it must match on outgoing transitions,
            False if must match on incoming transitions

        Returns
        -------
        Dictionary with the pairs as key and value as output
        '''
        results = []
        equations = []

        columns = []
        rows = []

        state_pair_map = {}
        for i in range(0,len(state_pairs)):
            state_pair_map[state_pairs[i].states] = i
        
        row = 0
        for state_pair in state_pairs:
            denominator = 2 * (len(state_pair.matching_trans) + len(state_pair.non_matching_trans[0]) + len(state_pair.non_matching_trans[1]))
            matched_states = [((t1[1] if out else t1[0]),(t2[1] if out else t2[0])) for t1, t2 in state_pair.matching_trans]

            equation = [0] * len(state_pairs)
            equation[state_pair_map[state_pair.states]] = denominator
            for matched_state in matched_states:
                if (self.is_a_match(matching_pairs,matched_state[0],matched_state[1])):
                    equation[state_pair_map[matched_state]] = equation[state_pair_map[matched_state]] -1 * k

            columns = columns + list(range(0,len(state_pairs)))
            rows = rows + ([row] * len(state_pairs))

            row = row + 1

            equations = equations + equation
            results.append(len(matched_states))
            if debug:
                print(equation, " ",  len(matched_states))

        matrix = csc_matrix((np.array(equations),(np.array(rows),np.array(columns))))

        start_time = time()
        final_result = spsolve(matrix,np.array(results))
        
        if out:
            self.out_time = (time() - start_time)
        else:
            self.in_time = (time() - start_time)
        if timing:
            print("%s seconds umfpack execution for " % self.out_time if out else self.in_time, end="")
            print("outgoing transitions" if out else "incoming transitions")
        
        return_dict = {}
        for i in range(0,len(final_result)):
            return_dict[state_pairs[i].states] = final_result[i]
        
        return return_dict
        

        


    def linear_equation_solver_smt(self, state_pairs, k, out, matching_pairs = None):
        '''
        Solve the linear equation with SMT-solvers for the FSM_Diff algorithm

        Parameters
        ----------
        state_pairs: list(ComparingStates)
            All matched and unmatched transitions for all the possible pairs
        k: float
            k-value of the FSM_Diff algorithm
        out: bool
            True if it must match on outgoing transitions,
            False if must match on incoming transitions

        Returns
        -------
        Dictionary with the pairs as key and value as output
        '''
        names = []
        variables = []
        domain = []
        equations = []
        for state_pair in state_pairs:
            names.append(state_pair.states)
            variable = Symbol("(" + state_pair.states[0] + "," + state_pair.states[1] + ")", REAL)
            variables.append(variable)
            domain.append(GE(variable,Real(0.0)))
            denominator = 2 * (len(state_pair.matching_trans) + len(state_pair.non_matching_trans[0]) + len(state_pair.non_matching_trans[1]))
            matched_states = [((t1[1] if out else t1[0]),(t2[1] if out else t2[0])) for t1, t2 in state_pair.matching_trans]
            reached_states_vars = [ Times(Real(k) if self.is_a_match(matching_pairs, t1, t2) else Real(0),Symbol("(" + t1 + "," + t2  + ")", REAL)) for (t1,t2) in matched_states]
            times = Real(0) if len(reached_states_vars) < 1 else Plus(list(i for i in reached_states_vars))
            equation = Equals(Minus(Times(Real(denominator), variable),  times), Real(len(state_pair.matching_trans)))
            equations.append(equation)
        formula = And(And( (i for i in domain)), And( (i for i in equations)))
        if debug:
            print_smtlib(formula)
        start_time = time()
        model = get_model(formula, solver_name=current_solver)
        if out:
            self.out_time = (time() - start_time)
        else:
            self.in_time = (time() - start_time)
        if timing:
            print("%s seconds SMT execution for " % self.out_time if out else self.in_time, end="")
            print("outgoing transitions" if out else "incoming transitions")
        return_dict = {}
        for i in range(0,len(names)):
            return_dict[names[i]] = eval(str(model.get_value(variables[i])))
        return return_dict

    def compute_scores(self,fsm_1, fsm_2, k, matching_pairs):
        ''' Compute the scores for the different possible pairs '''

        solver_function = self.linear_equation_solver if current_solver == "umfpack" else self.linear_equation_solver_smt

        out_match_trans = self.matching_transitions(fsm_1,fsm_2,True)
        outcome_out = solver_function(out_match_trans, k, True, matching_pairs)

        in_match_trans = self.matching_transitions(fsm_1,fsm_2,False)
        outcome_in = solver_function(in_match_trans, k, False, matching_pairs)

        result_dict = {}
        for var in outcome_out.keys():
            result_dict[var] = (outcome_out[var] + outcome_in[var]) / 2
        if equation:
            print(result_dict)
        return result_dict

    def identify_landmarks(self, pairs_to_scores,t,r):
        '''
        Identify which state pairs can be a possible match

        parameters
        ----------
        pairs_to_scores: dict
            A dictionary with the state pairs as key and score as output
        t: float
            treshold value of the FSM_Diff algorithm
        r: float
            ratio value of the FSM_Diff algorithm
        matching_pair: (str,str), optional
            a set of pairs that must be matched

        returns
        -------
        set of k_pairs (landmarks)
        '''
        filtered_dict = {}
        vars = []
        for var in pairs_to_scores:
            vars.append(var)
            if pairs_to_scores[var] >= t:
                filtered_dict[var] = pairs_to_scores[var]
        landmarks = set()
        for var in vars:
            filtered_vars = list(filter(lambda v: v[0] ==var[0] and not v == var, vars))
            is_landmark = True
            for f_var in filtered_vars:
                if not (pairs_to_scores[var] >= (pairs_to_scores[f_var] * r) and var in filtered_dict):
                    is_landmark = False
            if is_landmark:
                landmarks.add(var)
        return landmarks


    def surrounding_pairs(self, fsm_1,fsm_2,pair):
        '''
        From a matced pair, calculate next pair of state which can be reached
        by a matched transition
        '''
        s1 = pair[0]
        s2 = pair[1]

        n_pair = set()
        out_matching = self.pair_matching_transition(fsm_1,fsm_2,s1,s2,True)
        for t_out1, t_out2 in out_matching.matching_trans:
            n_pair.add(  (t_out1[1] , t_out2[1]))
        in_matching = self.pair_matching_transition(fsm_1,fsm_2,s1,s2,False)
        for t_in1, t_in2 in in_matching.matching_trans:
            n_pair.add( (t_in1[0], t_in2[0]))
        return n_pair

    def pick_highest(self, n_pairs, pairs_to_scores):
        '''
        Pick the highest score from the set
        '''
        highest =  ("", -0.0)
        for pair in n_pairs:
            if pairs_to_scores[pair] >= highest[1]:
                highest = (pair, pairs_to_scores[pair])
        return highest[0]

    def remove_conflicts(self,n_pairs, pair):
        '''
        Prevent duplication in the list by removing a pair
        if one of the states is already matched
        '''
        new_n_pairs = set()
        for n_pair in n_pairs:
            if pair[0] != n_pair[0] and pair[1] != n_pair[1]:
                new_n_pairs.add(n_pair)
        return new_n_pairs

    def added_transitions(self, fsm_1, fsm_2, k_pairs):
        '''
        calculate the transitions that are added
        i.e that are not in fsm_1 but in fsm_2
        '''
        added_transitions = []
        for edge2 in fsm_2.edges.data():
            exists = False
            for edge1 in fsm_1.edges.data():
                if (edge1[0],edge2[0]) in k_pairs and (edge1[1],edge2[1]) in k_pairs and edge2[2]["label"] == edge1[2]["label"]:
                    exists = True
            if not exists:
                added_transitions.append(edge2)
        return added_transitions

    def removed_transitions(self, fsm_1, fsm_2, k_pairs):
        '''
        calculate the transitions that are removed
        i.e that are in fsm_1 but not in fsm_2
        '''
        removed_transitions = []
        for edge1 in fsm_1.edges.data():
            exists = False
            for edge2 in fsm_2.edges.data():
                if (edge1[0],edge2[0]) in k_pairs and (edge1[1],edge2[1]) in k_pairs and edge2[2]["label"] == edge1[2]["label"]:
                    exists = True
            if not exists:
                removed_transitions.append(edge1)
        return removed_transitions

    def fresh_var(self,index):
        '''Generate a fresh variable on basis of the given index'''
        letters = string.ascii_lowercase
        value = 1
        if index >= len(letters):
            value = int(index / len(letters)) + 1
            index = index % len(letters)
        return letters[index] * value


    def annotade_edges(self,graph,k_pairs,set_edges,color, index, nr_of_states):
        '''
        Annotade edges by a color
        Check if the state is already in the graph and otherwise create a new fresh node
        Return how many nodes there are already in the model
        '''
        added_dict = {}
        for add in set_edges:
            from_state = None
            for k in k_pairs:
                if k[index] == add[0]:
                    from_state = self.fresh_var(k_pairs.index(k))
            if from_state is None and add[0] in added_dict.keys():
                from_state = self.fresh_var(added_dict[add[0]])
            elif from_state is None:
                num = nr_of_states + len(added_dict)
                from_state = self.fresh_var(num)
                added_dict[add[0]] = num
                graph.add_node(from_state,color=color)

            to_state = None
            for k in k_pairs:
                if k[index] == add[1]:
                    to_state = self.fresh_var(k_pairs.index(k))
            if to_state is None and add[1] in added_dict.keys():
                to_state = self.fresh_var(added_dict[add[1]])
            elif to_state is None:
                num = nr_of_states + len(added_dict)
                to_state = self.fresh_var(num)
                added_dict[add[1]] = num
                graph.add_node(to_state,color=color)

            graph.add_edge(from_state,to_state,color=color,label=add[2]["label"])

        return nr_of_states + len(added_dict)

    def matched_k_pairs_transitions(self, fsm_1, fsm_2, k_pairs):
        '''
        Calculate the set of transitions of the k_pairs which are matched
        '''
        edges = []
        k_pairs = list(k_pairs)
        for edge1 in fsm_1.edges.data():
            for edge2 in fsm_2.edges.data():
                if (edge1[0],edge2[0]) in k_pairs and (edge1[1],edge2[1]) in k_pairs and edge2[2]["label"] == edge1[2]["label"]:
                    from_state = self.fresh_var(k_pairs.index((edge1[0],edge2[0])))
                    to_state = self.fresh_var(k_pairs.index((edge1[1],edge2[1])))
                    edges.append((from_state,to_state,edge2[2]["label"]))
        return edges

    def annotade_graph(self, k_pairs, added, removed, matched):
        '''
        Create a graph with the matched, added and removed transitions
        '''
        graph = nx.MultiDiGraph()
        k_pairs = list(k_pairs)
        for i in range(0,len(k_pairs)):
            graph.add_node(self.fresh_var(i))

        for i in matched:
            graph.add_edge(i[0],i[1], label=i[2])

        nr_of_states = self.annotade_edges(graph,k_pairs,added,"green",1,len(graph.nodes))
        self.annotade_edges(graph,k_pairs,removed,"red",0,nr_of_states)
        return graph

    def performance_matrix(self, fsm_1, FP, FN, perfomance_dict):
        '''
        Calcualte the performance matrix

        parameters
        ----------
        fsm_1: nx.MultiDiGraph
            The reference fsm
        FP: list(dict)
            False positive edges
        FN: list(dict)
            False negative edges
        '''
        TP = []
        for edge in fsm_1.edges.data():
            found = False
            for rem in FN:
                if edge[0] == rem[0] and edge[1] == rem[1] and edge[2] == rem[2]:
                    found = True
            if not found:
                TP.append(edge)

        perfomance_dict["precision"] = len(TP) / (len(TP) + len(FP)) # FP is guaranteed to be not in TP, so can just be added
        perfomance_dict["recall"] = len(TP) / (len(TP) + len(FN)) # FN is guarenteeed to be not in TP, so can just be added

        if perfomance_dict["recall"] == 0 and perfomance_dict["precision"] == 0: # if none of the transitions match, recall and precision are 0
            perfomance_dict["f-measure"] = 0
            warnings.warn("UndefinedMetricWarning: precision and recall are 0, f-measure can't be calculated (defaults to 0)", Warning)
        else:
            perfomance_dict["f-measure"] = (2 * perfomance_dict["precision"] * perfomance_dict["recall"]) / (perfomance_dict["precision"] + perfomance_dict["recall"])

    def statistics_graph(self, graph):
        ''' return basis statistics for the graph '''
        return {"States": len(graph.nodes), "Transitions": len(graph.edges)}

    def logging(self, fsm_1, fsm_2, added, removed, graph, log_dict):
        ''' add all log information in one dict '''
        self.performance_matrix(fsm_1,added,removed,log_dict)
        log_dict["Reference"] = self.statistics_graph(fsm_1)
        log_dict["Updated"] = self.statistics_graph(fsm_2)
        log_dict["Output"] = self.statistics_graph(graph)
        log_dict["Outgoing time"] = "%s" % self.out_time
        log_dict["Incoming time"] = "%s" % self.in_time
        log_dict["Solver"] = current_solver

    def algorithm(self, fsm_1, fsm_2, k, t, r, matching_pairs = None):
        '''
        Executes the FSM_Diff algorithm

        Parameters:
        ----------
        fsm_1: nx.MultiDiGraph
            actions marked as label in the graph
        fsm_2: nx.MultiDiGraph
            actions marked as label in the graph
        k: float
            the k-value of the algorithm
        t: float
            the t-value of the algorithm
        r: float
            the r-value of the algorithm
        matching_pair : (str,str), optional
            a set of pairs that must be considered as match in the result

        Returns
        -------
        nx.MultiDiGraph with added/removed transitions annotated in the graph
        '''
        if matching_pairs is not None:
            for matching_pair in matching_pairs:
                if (matching_pair[0] not in fsm_1.nodes or matching_pair[1] not in fsm_2.nodes):
                    print("pair: " + matching_pair[0] +  " " +  matching_pair[1] + " does not exists")
                    return nx.MultiDiGraph()

        # line 1
        pairs_to_scores = self.compute_scores(fsm_1,fsm_2,k, matching_pairs)

        # line 2
        k_pairs = self.identify_landmarks(pairs_to_scores,t,r)
        # line 3-5
        key = (list(fsm_1.nodes)[0], list(fsm_2.nodes)[0])
        if not k_pairs and pairs_to_scores[key] >= 0:
            k_pairs.add(key)
        # line 6
        n_pairs = set()
        for pair in k_pairs:
            n_pairs = n_pairs.union(self.surrounding_pairs(fsm_1,fsm_2,pair))
        for k_p in k_pairs:
            n_pairs = self.remove_conflicts(n_pairs,k_p)

        # line 7 - 14
        while n_pairs:
            while n_pairs:
                # line 9
                pair = self.pick_highest(n_pairs,pairs_to_scores)
                # line 10
                k_pairs.add(pair)
                # line 11
                n_pairs = self.remove_conflicts(n_pairs,pair)
            # line 13
            for pair in k_pairs:
                n_pairs = n_pairs.union(self.surrounding_pairs(fsm_1,fsm_2,pair))
            for k_p in k_pairs:
                n_pairs = self.remove_conflicts(n_pairs,k_p)

        if k_pairs_output:
            write_k_pairs_to_file(k_pairs, output_file)

        added = self.added_transitions(fsm_1,fsm_2,k_pairs)
        removed = self.removed_transitions(fsm_1,fsm_2,k_pairs)
        matched = self.matched_k_pairs_transitions(fsm_1,fsm_2,k_pairs)
        graph = self.annotade_graph(k_pairs,added,removed,matched)

        if logging:
            self.logging(fsm_1,fsm_2,added,removed,graph,graph.graph)

        if performance and logging:
            print(graph.graph)
        elif performance and not logging:
            log_dict = {}
            self.logging(fsm_1,fsm_2,added,removed,graph,log_dict)
            print (log_dict)


        return graph
