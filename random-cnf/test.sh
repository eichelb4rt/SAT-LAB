#!/bin/bash
# SHEBANG

t=20
n=3
c=3
k=1
out="out"
lingeling="./lingeling/lingeling"

./random-cnf.py "$t" "$n" "$c" "$k" -o "$out" || exit 1

i=0
while [ "$i" -lt "$t" ]; do
    echo $(basename "./$out/random_cnf_$i.txt") 
    "$lingeling" "./$out/random_cnf_$i.txt" | grep SATIS
    ((++i))
done