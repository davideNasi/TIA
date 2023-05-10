#!/bin/bash

set -x
set -e

cd lib
python3.7 setup.py build develop
cd ..

# 46.3(10)
CUDA_VISIBLE_DEVICES=0 python3.7 test_net_no_da.py --dataset wolves --net res101 --cuda \
--model_dir models/res101/wolves/faster_rcnn_1_1_4265.pth