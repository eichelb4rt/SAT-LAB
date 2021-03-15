#!/bin/bash
# SHEBANG

t=20
n=20
c=100
k=3
random_cnf_dir="../random-cnf"
random_cnf_tool="$random_cnf_dir/random-cnf.py"
out="$random_cnf_dir/out"
lingeling="./lingeling/lingeling"
two_sat="../2-SAT/two_sat.py"
dpll="../DPLL/dpll.py"
dpll_mf="../DPLL_MF/dpll_mf.py"
cdcl="../CDCL/cdcl.py"

"$random_cnf_tool" "$t" "$n" "$c" "$k" -o "$out" || exit 1

solver="$cdcl"
i=0
satisfiable_count=0
unsatisfiable_count=0
mistakes=0
while [ "$i" -lt "$t" ]; do
    file="./$out/random_cnf_$i.txt"
    echo $(basename "$file")
    # get the results for lingeling and our solver
    result_lingeling=$("$lingeling" "$file" | grep SATISFIABLE)
    result_solver=$("$solver" "$file")
    # make them fit each others format
    if [ "$result_lingeling" == "s SATISFIABLE" ]; then
        result_lingeling="Satisfiable"
        ((++satisfiable_count))
    else
        result_lingeling="Unsatisfiable"
        ((++unsatisfiable_count))
    fi
    if [ "$result_lingeling" != "$result_solver" ]; then ((++mistakes)); fi
    # print them both
    echo "$result_lingeling"
    echo "$result_solver"
    ((++i))
    echo -e "\n"
done
echo -e "Satisfiable: $satisfiable_count\nUnsatisfiable: $unsatisfiable_count\nMistakes: $mistakes"