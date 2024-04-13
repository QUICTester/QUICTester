import time

from aalpy.base import SUL, Oracle
from aalpy.learning_algs.non_deterministic.OnfsmObservationTable import NonDetObservationTable
from aalpy.learning_algs.non_deterministic.TraceTree import SULWrapper
from aalpy.utils.HelperFunctions import extend_set, print_learning_info, print_observation_table, \
    get_available_oracles_and_err_msg

print_options = [0, 1, 2, 3]

available_oracles, available_oracles_error_msg = get_available_oracles_and_err_msg()


def run_non_det_Lstar(alphabet: list, sul: SUL, eq_oracle: Oracle, n_sampling=20, trace_tree=True,
                      max_learning_rounds=None, custom_oracle=False, return_data=False, print_level=2,
                      ):
    """
    Based on ''Learning Finite State Models of Observable Nondeterministic Systems in a Testing Context '' from Fakih
    et al. Relies on the all-weather assumption. (By sampling we will obtain all possible non-deterministic outputs.
    With table-shrinking we mitigate the undesired consequences of the all-weather assumption.

    Args:

        alphabet: input alphabet

        sul: system under learning

        eq_oracle: equivalence oracle

        n_sampling: number of times that each cell has to be updated. If this number is to low, all-weather condition
            will not hold and learning will not converge to the correct model. (Default value = 50)

        trace_tree: removes limitation of all-weather assumption by dynamically keeping the observation table updated
                    with respect to observations

        max_learning_rounds: if max_learning_rounds is reached, learning will stop (Default value = None)

        custom_oracle: if True, warning about oracle type will be removed and custom oracle can be used

        return_data: if True, map containing all information like number of queries... will be returned
            (Default value = False)

        print_level: 0 - None, 1 - just results, 2 - current round and hypothesis size, 3 - educational/debug
            (Default value = 2)

    Returns:
        learned ONFSM

    """
    print('Starting learning with an all-weather assumption.\n'
          'See run_Lstar_ONFSM documentation for more details about possible non-convergence.')

    if not custom_oracle and type(eq_oracle) not in available_oracles:
        raise SystemExit(available_oracles_error_msg)

    start_time = time.time()
    eq_query_time = 0
    learning_rounds = 0
    hypothesis = None

    sul = SULWrapper(sul)
    eq_oracle.sul = sul

    # setting test_cells_again=TRUE seems to work better for larger onfsm and worse for smaller onfsm
    observation_table = NonDetObservationTable(alphabet, sul, n_sampling, trace_tree, test_cells_again=False)

    # We fist query the initial row. Then based on output in its cells, we generate new rows in the extended S set,
    # and then we perform membership/input queries for them.
    observation_table.update_obs_table()
    new_rows = observation_table.update_extended_S(observation_table.S[0])
    observation_table.update_obs_table(s_set=new_rows)

    while True:
        learning_rounds += 1
        if max_learning_rounds and learning_rounds - 1 == max_learning_rounds:
            break

        # Close observation table
        row_to_close = observation_table.get_row_to_close()
        while row_to_close is not None:
            # First we add new rows to the extended S set. They are added based on the values in the cells of the
            # rows that is to be closed. Once those rows are created, they are populated and closedness is checked
            # once again.
            extended_rows = observation_table.update_extended_S(row_to_close)
            observation_table.update_obs_table(s_set=extended_rows)
            row_to_close = observation_table.get_row_to_close()

        observation_table.clean_obs_table()

        # Generate hypothesis
        hypothesis = observation_table.gen_hypothesis()

        if print_level > 1:
            print(f'Hypothesis {learning_rounds}: {len(hypothesis.states)} states.')

        if print_level == 3:
            print_observation_table(observation_table, 'non-det')

        # Find counterexample
        eq_query_start = time.time()
        cex = eq_oracle.find_cex(hypothesis)
        eq_query_time += time.time() - eq_query_start

        # If no counterexample is found, return the hypothesis
        if cex is None:
            break

        if print_level == 3:
            print('Counterexample', cex)

        # Process counterexample -> Extract suffix to be added to E set
        cex_suffixes = observation_table.cex_processing(cex)
        # Add all suffixes to the E set and ask membership/input queries.
        added_suffixes = extend_set(observation_table.E, cex_suffixes)
        observation_table.update_obs_table(e_set=added_suffixes)

    total_time = round(time.time() - start_time, 2)
    eq_query_time = round(eq_query_time, 2)
    learning_time = round(total_time - eq_query_time, 2)

    info = {
        'learning_rounds': learning_rounds,
        'automaton_size': len(hypothesis.states),
        'queries_learning': sul.num_queries,
        'steps_learning': sul.num_steps,
        'queries_eq_oracle': eq_oracle.num_queries,
        'steps_eq_oracle': eq_oracle.num_steps,
        'learning_time': learning_time,
        'eq_oracle_time': eq_query_time,
        'total_time': total_time
    }

    if print_level > 0:
        print_learning_info(info)

    if return_data:
        return hypothesis, info

    return hypothesis
