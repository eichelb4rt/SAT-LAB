#!/bin/bash
# SHEBANG

t=200
n=5
c=31
k=5
out="out"
lingeling="./lingeling/lingeling"

./random-cnf.py "$t" "$n" "$c" "$k" -o "$out" || exit 1

i=0
while [ "$i" -lt "$t" ]; do
    echo $(basename "./$out/random_cnf_$i.txt") 
    "$lingeling" "./$out/random_cnf_$i.txt" | grep SATIS
    ((++i))
done