#!/bin/bash
# SHEBANG

t=200
n=4
c=16
k=4
out="out"

./random-cnf.py "$t" "$n" "$c" "$k" -o "$out" &&

i=0
while [ "$i" -lt "$t" ]; do
    ./lingeling/lingeling "./$out/random_cnf_$i.txt" | grep SATIS
    ((++i))
done