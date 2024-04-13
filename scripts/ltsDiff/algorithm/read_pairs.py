''''Module for reading pairs from the command line'''
def read_pairs(file):
    '''Function for reading pairs from a file'''
    pairs = []
    with open(file, 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            if line[0] == "#":
                continue
            splitted = line.split(":")
            pairs.append((splitted[0],splitted[1]))
    return pairs