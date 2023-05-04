#!/bin/bash

set -x
set -e

cd lib
python3.7 setup.py build develop
cd ..

# 46.3(10)
CUDA_VISIBLE_DEVICES=0 python test_net.py --dataset wolves --net res101 --cuda \
--model_dir models/wolves/res101/TIA/da_faster_rcnn_wolves_12.pth