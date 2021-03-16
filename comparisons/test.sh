#!/bin/bash
# SHEBANG

random_cnf_dir="../random-cnf"
random_cnf_tool="$random_cnf_dir/random-cnf.py"
out="$random_cnf_dir/out"

lingeling="./lingeling/lingeling"
two_sat="../2-SAT/two_sat.py"
dpll="../DPLL/dpll.py"
dpll_mf="../DPLL_MF/dpll_mf.py"
cdcl="../CDCL/cdcl.py"

solver="$cdcl"
preset="medium_4cnf"

preset_folder="$random_cnf_dir/presets"
preset_executable="$preset_folder/$preset.sh"
bash "$preset_executable"

satisfiable_count=0
unsatisfiable_count=0
mistakes=0
for file in $(ls "$out"); do
    echo $(basename "$file")
    path_to_file="$out/$file"
    # get the results for lingeling and our solver
    result_lingeling=$("$lingeling" "$path_to_file" | grep SATISFIABLE)
    result_solver=$("$solver" "$path_to_file")
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
    echo -e "$result_lingeling\t(lingeling)"
    echo -e "$result_solver\t(my solver)\n"
done
echo -e "Satisfiable: $satisfiable_count\nUnsatisfiable: $unsatisfiable_count\nMistakes: $mistakes"