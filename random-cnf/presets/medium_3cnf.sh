t=20
n=20
c=100
k=3

random_cnf_dir=".."
random_cnf_tool="$random_cnf_dir/random-cnf.py"
out="$random_cnf_dir/out"

"$random_cnf_tool" "$t" "$n" "$c" "$k" -o "$out" || exit 1