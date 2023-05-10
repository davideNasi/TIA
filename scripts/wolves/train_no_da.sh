#!/bin/bash

set -x
set -e

cd lib
python3.7 setup.py build develop
cd ..

CUDA_VISIBLE_DEVICES=0 python3.7 trainval_net.py --dataset wolves --net res101 --cuda --epochs 1