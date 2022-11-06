#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import h5py

file = h5py.File('../CharRecApi/weights/comnist_keras_ru.hdf5')

d = dict(file)

for i in d:
    if i is h5py.Group:
        print(i)

