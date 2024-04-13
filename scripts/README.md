# Scripts 
## Automated Analysis
### Installation
The installation script is included in [setup.py](../setup.sh).
1. Install key dependencies ```sudo apt install cmake libgmp3-dev swig graphviz graphviz-dev swig3.0 gperf autoconf```
2. Install python3.8 modules ```python -m pip install pygraphviz cython==0.29.23 scipy networkx pysmt pydot```
3. Install the SMT-solvers ```pysmt-install --all```

### Automated Analysis on models originating from the same target (server) and configuration but in different timeout settings.
1. Categorise the results into 3 different directories in the ../results/*Models
    - CS-short for short timeout results
    - CS-long for long timeout results
    - CS-temporal for mixed (short and long) timeout results
2. Run ```./compareTemporal.sh```
3. The result will be saved as a .dot file in the respective directory.

### Automated Cross Check Analysis on models.
1. Categorise the results into 3 different directories in the ../results/*Models
    - CS-short for short timeout results
    - CS-long for long timeout results
    - CS-temporal for mixed (short and long) timeout results
2. Run ```./crossCheck.sh```
3. The deviating state transitions will be saved in [results/](../results)&lt;SUT_name&gt;Models/crossCheckResults/1_&lt;config&gt;_deviating_state_trans.txt.

### Automated Analysis on all unique models and the reference models.
1. Categorise the results into 3 different directories in the ../results/*Models
    - CS-short for short timeout results
    - CS-long for long timeout results
    - CS-temporal for mixed (short and long) timeout results
2. Run ```./compareModel.sh```
3. The result will be saved as a .dot file in the respective directory.

### Automated Analysis on 2 specific models.
1. Run ```./compareTwoModels.sh <path/to/model_1> <path/to/model_2>```
2. The result will be saved as a tempResult.dot file in this directory.
