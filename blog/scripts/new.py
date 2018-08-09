#!/usr/bin/env python3

import json
import glob
import os
import time
from shutil import rmtree, copyfile, copytree

id_field = input("ID: ")
title = input("Title: ")
date = input("Date: ")

tags = []

while True:
    next_tag = input("Tag: ")
    if next_tag.strip() == "":
        break
    else:
        tags.append(next_tag)

print(id_field)
print(title)
print(tags)

with open('articles/' + id_field + '.json', 'w') as out_file:
    json.dump({
        "id": id_field,
        "title": title,
        "date": date,
        "create_date": time.time(),
        "tags": tags
    }, out_file)

open('articles/' + id_field + '.html', 'w')
