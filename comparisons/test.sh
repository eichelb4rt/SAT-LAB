#!/bin/bash
# SHEBANG

t=50
n=5
c=15
k=3
random_cnf_dir="../random-cnf"
random_cnf_tool="$random_cnf_dir/random-cnf.py"
out="$random_cnf_dir/out"
lingeling="./lingeling/lingeling"
two_sat="../2-SAT/two_sat.py"
dpll="../DPLL/dpll.py"
dpll_mf="../DPLL_MF/dpll_mf.py"
cdcl="../CDCL/cdcl.py"
solver="$cdcl"

"$random_cnf_tool" "$t" "$n" "$c" "$k" -o "$out" || exit 1

i=0
while [ "$i" -lt "$t" ]; do
    file="./$out/random_cnf_$i.txt"
    echo $(basename "$file")
    "$lingeling" "$file" | grep SATISFIABLE
    "$solver" "$file"
    ((++i))
    echo -e "\n"
done