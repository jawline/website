#!/usr/bin/env python3

import json
import glob
import os
from shutil import rmtree, copyfile

OUT_PATH="./bin/"
ARTICLES_PATH=OUT_PATH + 'articles/';

print("Blog compiler started")

if os.path.isdir(OUT_PATH):
    print("Removed existing bin")
    rmtree(OUT_PATH)

articles = []
tag_dict = {};

for file in glob.glob("articles/*.json"):
    with open(file) as f:
        data = json.load(f)
        articles.append([data, file.replace(".json", ".html")])

os.mkdir(OUT_PATH)
os.mkdir(ARTICLES_PATH);

for article in articles:
    print("Compiling", article[0]["title"], article[0]["tags"])
    copyfile(article[1], ARTICLES_PATH + article[0]["id"] + ".html")

    for tag in article[0]["tags"]:
        this_tag = tag_dict.get(tag, [])
        this_tag.append(article[0])
        tag_dict[tag] = this_tag

print("Compiled all articles")

for tag in tag_dict.keys():
    print(tag, tag_dict[tag])
