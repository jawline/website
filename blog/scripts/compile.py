#!/usr/bin/env python3

import json
import glob
import os
from shutil import rmtree, copyfile, copytree

OUT_PATH="./bin/"
ARTICLES_PATH=OUT_PATH + 'articles/';
LISTS_PATH=OUT_PATH + 'lists/';

print("Blog compiler started")

#SETUP GLOBAL TEMPLATES

NAV_TEMPLATE = '';

with open('templates/nav.html', 'r') as template_file:
    NAV_TEMPLATE = template_file.read()

def rtemp(file):
    with open(file, 'r') as template_file:
        return template_file.read().replace('{{{NAV_BAR_CONTENT}}}', NAV_TEMPLATE)

ARTICLE_TEMPLATE = rtemp('templates/article.html')
INDEX_TEMPLATE = rtemp('templates/index.html')
LISTS_TEMPLATE = rtemp('templates/list.html')
LIST_ITEM_TEMPLATE = rtemp('templates/list_item.html')

#END GLOBAL TEMPLATES

if os.path.isdir(OUT_PATH):
    print("Removed existing bin")
    rmtree(OUT_PATH)

#Construct the initial state of the output path
copytree("resources/", OUT_PATH)

#Keep track of articles and tags
articles = []
tag_dict = {};

def write_article_from_template(article):
    final_path = ARTICLES_PATH + article[0]["id"] + ".html";
    with open(article[1], 'r') as article_file:
        article_data = article_file.read()
        final_data = ARTICLE_TEMPLATE;
        final_data = final_data.replace('{{{ARTICLE_CONTENT}}}', article_data)
        final_data = final_data.replace('{{{ARTICLE_TITLE}}}', article[0]["title"])
        final_data = final_data.replace('{{{ARTICLE_DATE}}}', article[0]["date"])
        final_data = final_data.replace('{{{ARTICLE_TAGS}}}', ', '.join(article[0]["tags"]))

        with open(final_path, 'w') as output_file:
            output_file.write(final_data) 
                

for file in glob.glob("articles/*.json"):
    with open(file) as f:
        data = json.load(f)
        articles.append([data, file.replace(".json", ".html")])

os.mkdir(ARTICLES_PATH)

for article in articles:
    print("Compiling", article[0]["title"], article[0]["tags"])
    write_article_from_template(article)
    for tag in article[0]["tags"]:
        this_tag = tag_dict.get(tag, [])
        this_tag.append(article[0])
        tag_dict[tag] = this_tag

print("Compiled all articles")

# Responsible for list construction
print("Beginning list construction")

os.mkdir(LISTS_PATH)

def write_tag(tag):
    final_out = LISTS_TEMPLATE.replace('{{{LIST_TITLE}}}', tag)
    with open(LISTS_PATH + tag + '.html', 'w') as out_file:
        out_file.write(final_out)

for tag in tag_dict.keys():
    print("Writing list", tag)
    with open(LISTS_PATH + tag + '.json', 'w') as f:
        json.dump(tag_dict[tag], f)
    write_tag(tag)

#End of lists construction

print("Generating index")

with open(OUT_PATH + 'global.json', 'w') as f:
    json.dump({ "articles": articles, "tags": tag_dict }, f)

with open(OUT_PATH + 'index.html', 'w') as f:
    f.write(INDEX_TEMPLATE)
