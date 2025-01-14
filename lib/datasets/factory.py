# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""Factory method for easily getting imdbs by name."""
from __future__ import absolute_import, division, print_function

import numpy as np
from datasets.pascal_voc import pascal_voc
from datasets.imagenet import imagenet
from datasets.cityscape import cityscape
from datasets.cityscape_car import cityscape_car
from datasets.clipart import clipart
from datasets.kitti_car import kitti_car
from datasets.wolves import park1, park2, park2_test, park1_camera1, park1_camera2, park2_day, park2_night

__sets = {}


# Set up voc_<year>_<split>
for split in ['train']:
    name = "park1_" + split
    __sets[name] = lambda split=split : park1(split)

for split in ['train']:
    name = "park2_" + split
    __sets[name] = lambda split=split : park2(split)

for split in ['test']:
    name = "park2_" + split
    __sets[name] = lambda split=split : park2_test(split)

for split in ['train']:
    name = "park1_camera1_" + split
    __sets[name] = lambda split=split : park1_camera1(split)

for split in ['train']:
    name = "park1_camera2_" + split
    __sets[name] = lambda split=split : park1_camera2(split)
for split in ['train']:
    name = "park2_day_" + split
    __sets[name] = lambda split=split : park2_day(split)
for split in ['train']:
    name = "park2_night_" + split
    __sets[name] = lambda split=split : park2_night(split)

for year in ['2007', '2012']:
    for split in ['train', 'val', 'trainval', 'trainval_aug', 'test']:
        name = 'voc_{}_{}'.format(year, split)
        __sets[name] = (lambda split=split, year=year: pascal_voc(split, year))

for year in ["2007"]:
    for split in ["trainval", "train", "test"]:
        name = "clipart_{}".format(split)
        __sets[name] = lambda split=split: clipart(split, year)

for year in ['2012']:
    for split in ["train", "train_aug"]:
        name = "kitti_car_{}_{}".format(year, split)
        __sets[name] = lambda split=split, year=year: kitti_car(split, year)

for year in ["2007"]:
    for split in ["train_s", "train_aug", "train_t", "test"]:
        name = "cityscape_{}_{}".format(year, split)
        __sets[name] = lambda split=split, year=year: cityscape(split, year)

for year in ["2007"]:
    for split in ["train_s", "train_t", "test_s", "test_t", "train_aug"]:
        name = "cityscape_car_{}_{}".format(year, split)
        __sets[name] = lambda split=split, year=year: cityscape_car(split, year)

def get_imdb(name):
    """Get an imdb (image database) by name."""
    if name not in __sets:
        raise KeyError("Unknown dataset: {}".format(name))
    return __sets[name]()


def list_imdbs():
    """List all registered imdbs."""
    return list(__sets.keys())