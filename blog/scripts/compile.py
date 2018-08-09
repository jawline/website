#!/usr/bin/env python3

import glob, os

for file in glob.glob("articles/*.json"):
    print(file)
