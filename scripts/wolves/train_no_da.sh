#!/bin/bash

set -x
set -e

cd lib
python3.7 setup.py build develop
cd ..

CUDA_VISIBLE_DEVICES=0 python3.7 train_no_da.py --dataset wolves --net res101 --cuda --net res101 --epochs 12 \
--load_dir models/res101/wolves/faster_rcnn_1_12_4265.pth