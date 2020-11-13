#!/bin/python3
# SHEBANG

import os
import random
import argparse
import numpy as np
from typing import List

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        metavar = 't',
        dest = 't',
        type = int,
        help = 'Number of CNFs'
    )
    parser.add_argument(
        metavar = 'n',
        dest = 'n',
        type = int,
        help = 'Number of variables'
    )
    parser.add_argument(
        metavar = 'c',
        dest = 'c',
        type = int,
        help = 'Number of clauses'
    )
    parser.add_argument(
        metavar = 'k',
        dest = 'k',
        type = int,
        help = 'Clause width'
    )
    parser.add_argument(
        '-o',
        '--output',
        metavar = 'output_dir',
        dest = 'output',
        default = 'out',
        help = 'Directory that the CNFs are written to'
    )
    args = parser.parse_args()
    # make the output directory if not existent
    try:
        os.mkdir(args.output)
    except FileExistsError:
        pass
    except Exception:
        print(f"unable to make directory {args.output}")
    
    # write t random CNFs
    for i in range(args.t):
        with open(f"{args.output}/random_cnf_{i}.txt", "w") as f:   # e.g.: out/random_cnf_0.txts
            cnf = gen_cnf(args.n, args.c, args.k)   # generate cnf
            encoded_cnf = encode_cnf(args.n, args.c, args.k, cnf)   # encode it
            f.write(encoded_cnf)    # write it

def encode_cnf(n: int, c: int, k: int, cnf: List[List[int]]) -> str:
    """
    Encodes a given cnf in DIMACS.

    Parameters
    ----------
    n : int
        Number of variables.
    
    c : int
        Number of clauses.

    k : int
        Clause width.
    
    cnf : List[List[int]]

    Returns
    -------
    str
        Returns a DIMACS encoded cnf.
    """

    encoded_cnf = f"c random cnf\np cnf {n} {c}\n"
    encoded_cnf += "".join([f"{encode_clause(clause)}\n" for clause in cnf])
    return encoded_cnf

def encode_clause(clause: List[int]) -> str:
    """
    Encodes a given clause for DIMACS.

    Paramaters
    ----------
    clause : List[int]
        Clause to be encoded.
    
    Returns
    -------
    str
        Returns the encoded clause.
    """

    #print("".join([f"{literal} " for literal in clause]) + "0")
    return "".join([f"{literal} " for literal in clause]) + "0"   # add a space after aech literal and finish with a 0

def gen_cnf(n: int, c: int, k: int) -> List[List[int]]:
    """
    Generate a list of random clauses.

    Parameters
    ----------
    n : int
        Number of variables.
    c : int
        Number of clauses.
    k : int
        Clause width.

    Returns
    -------
    List[List[int]]
        Returns a list of c unique (n,k) clauses.
    """

    cnf = []
    for i in range(c):
        # add unique clause
        new_clause = gen_clause(n, k)
        while duplicate_clause_exists(cnf, new_clause):
            new_clause = gen_clause(n, k)
        cnf.append(new_clause)
    return cnf

def duplicate_clause_exists(clauses: List[List[int]], new_clause: List[int]) -> bool:
    """
    Check if a duplicate there is already a clause similar to the new clause added.

    Parameters
    ----------
    clauses : List[List[int]]
        Array with all the clauses.
    new_clause : List[int]
        Clause to be checked.

    Returns
    -------
    bool
        True if duplicate clause found, False otherwise.
    """

    for old_clause in clauses:
        if (new_clause == old_clause).all():    # true if all the values inside the np array are equal
            return True
    return False

def gen_clause(n: int, k: int) -> List[int]:
    """
    Generate a random clause.

    Parameters
    ----------
    n : int
        Number of variables.
    k : int
        Clause width.

    Returns
    -------
    List[int]
        Returns a random clause (n,k) clause.
    """

    variables = random.sample(range(1, n+1), k) # choose k from n possible variables
    variables = np.sort(variables)  # sort them (turns into np array)
    for i, var in enumerate(variables):
        negate = random.randrange(-1, 2, 2) # negate the var with a chance of 50%   (negate = 1 in 50%, -1 in 50%)
        variables[i] = negate * var
    return variables

if __name__ == "__main__":
    main()