#!/bin/bash

set -x
set -e

cd lib
python3.7 setup.py build develop
cd ..

# 46.3(10)
CUDA_VISIBLE_DEVICES=0 python3.7 test_net.py --dataset wolves_day_and_night --net res101 --cuda \
--model_dir models/wolves_day_and_night/res101/TIA/da_faster_rcnn_wolves_12.pth