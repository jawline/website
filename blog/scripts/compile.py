#!/usr/bin/env python3

import re
import time
import json
import glob
import os
import subprocess
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

#Handle converting the markdown to HTML and extracting the intro
def get_article_html(filename):
	#MD2HT converts our articles from markdown
	return subprocess.check_output("./scripts/gen_html " + filename, shell=True).decode('utf-8')

intro_regex = re.compile('<a-intro>(.*)</a-intro>', re.DOTALL);

#Extract the info from the HTML portion
def extract_intro(article):
	article_data = get_article_html(article[1])
	matched = intro_regex.search(article_data)
	if matched == None:
			print("No match in" + article_data)
			return ''
	else:
			return matched.group(1)

def write_article_from_template(article):
  final_path = ARTICLES_PATH + article[0]["id"] + ".html";
  article_data = get_article_html(article[1])
		
  final_data = ARTICLE_TEMPLATE;
  final_data = final_data.replace('{{{ARTICLE_CONTENT}}}', article_data)
  final_data = final_data.replace('{{{ARTICLE_TITLE}}}', article[0]["title"])
  final_data = final_data.replace('{{{ARTICLE_TAGS}}}', ', '.join(article[0]["tags"]))
  final_data = final_data.replace('{{{ARTICLE_TIME}}}', article[0]["human_time"])

  with open(final_path, 'w') as output_file:
    output_file.write(final_data)                        

for file in glob.glob("articles/*.json"):
    with open(file) as f:
        data = json.load(f)
        data["human_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(float(data['create_date'])))
        articles.append([data, file.replace(".json", ".md")])

os.mkdir(ARTICLES_PATH)

for article in articles:
    print("Compiling", article[0]["title"], article[0]["tags"])
    write_article_from_template(article)
    article[0]["desc"] = extract_intro(article)
    if article[0].get("hidden", False) == False:
        for tag in article[0]["tags"]:
            this_tag = tag_dict.get(tag, [])
            this_tag.append(article[0])
            tag_dict[tag] = this_tag

print("Compiled all articles")
#End of articles block

# Responsible for list construction
print("Beginning list construction")

os.mkdir(LISTS_PATH)

def write_tag(tag):

    list_entries = '';
    
    tag_dict[tag].sort(key=lambda x: float(x["create_date"]), reverse=True)
    
    for tag_item in tag_dict[tag]:
        list_entries += LIST_ITEM_TEMPLATE.replace('{{{LI_TARGET}}}', '/articles/' + tag_item["id"]).replace('{{{LI_NAME}}}', tag_item["title"]).replace('{{{LI_TAGS}}}', ", ".join(tag_item["tags"])).replace('{{{LI_DESCRIPTION}}}', tag_item["desc"]).replace('{{{LI_TIME}}}', tag_item["human_time"])

    final_out = LISTS_TEMPLATE.replace('{{{LIST_TITLE}}}', tag.capitalize()).replace('{{{LIST_CONTENT}}}', list_entries)

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
