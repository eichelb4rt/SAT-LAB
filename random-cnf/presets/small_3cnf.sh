t=10
n=5
c=25
k=3

random_cnf_dir=".."
random_cnf_tool="$random_cnf_dir/random-cnf.py"
out="$random_cnf_dir/out"

cd $(dirname "$0")

if [ -d "$out" ]; then rm -r "$out"; fi
"$random_cnf_tool" "$t" "$n" "$c" "$k" -o "$out" || exit 1