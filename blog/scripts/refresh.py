#!/usr/bin/env python3

import json
import glob
import os
import time
from shutil import rmtree, copyfile, copytree

id_field = input("ID: ")

with open('articles/' + id_field + '.json', 'r') as in_file:
    data = json.load(in_file)
    data["create_date"] = time.time()
    with open('articles/' + id_field + '.json', "w") as out_file:
        json.dump(data, out_file)
