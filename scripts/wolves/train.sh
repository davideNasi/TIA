#!/bin/bash

set -x
set -e

cd lib
python3.7 setup.py build develop
cd ..

CUDA_VISIBLE_DEVICES=0 python3.7 trainval_net.py --dataset wolves --net res101 --cuda \
--epochs 15 --gamma 5.0 --warmup --context --lr 0.0001 \
--alpha1 1.0 --alpha2 1.0 --alpha3 1.0 \
--lamda1 1.0 --lamda2 1.0 --lamda3 0.01 \
--num_aux1 2 --num_aux2 4 --desp 'TIA'