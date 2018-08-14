<a-intro>

<p>
As part of a recent migration away from angular I decided to develop an entirely static website which only depended on bootstrap and jQuery.
</p>

</a-intro>

<h3>General Design</h3>

<p>Split my website into static files (css / images / js), template files (article template, index template), and article files (HTML fragments with accompanying JSON used as a description of the article), with each getting their own folder. Lists will be automatically inferred from the articles.</p>

Design goals:
<ul>
    <li>Easy article addition</li>
    <li>Lists of articles based on tags</li>
    <li>Static site generation during deployment</li>
</ul>  

Ignored for now:
<ul>
    <li>Pagination</li>
    <li>Search</li>
</ul>

<h3>Implementation</h3>

<p>
For this project we will be using Python to create a blog compiler capable of taking the files laid out in these directories and constructing a static compiled version of the website. Grab the list of articles from articles/*.json. Create a list of lists from tags on the articles. Then construct a final compiled output by copying resources to a new directory and writing articles and lists using the template files provided.
</p>


<p>To start I settled on the general folder structure:</p>

<ul>
    <li>resources/</li>
    <li>templates/</li>
    <li>articles/</li>
    <li>scripts/</li>
</ul>

<p>
where the resources folder is used to store css, images, fonts and JavaScript for the website. The templates folder stores templates for articles and list files. The articles folder contains each of the articles that will be listed on the blog along with metadata that decides how it is presented in lists and the scripts folder is used for the blog compiler. Initially, lets start with the skeleton program:
</p>

<pre><code>#!/usr/bin/env python3
import re
import time
import json
import glob
import os
from shutil import rmtree, copyfile, copytree

OUT_PATH="./bin/"
ARTICLES_PATH=OUT_PATH + 'articles/';
LISTS_PATH=OUT_PATH + 'lists/';
</code></pre>

<b>Resource Files</b>

<p>Files in the resources folder are to be copied verbatim as the base of our compiled site. We can do this using the script:</p>

<pre><code>#Delete the output directory if it already exists
if os.path.isdir(OUT_PATH):
    print("Removed existing bin")
    rmtree(OUT_PATH)

#Construct the initial state of the output path
copytree("resources/", OUT_PATH)</code></pre>

<b>Article Generation</b>

<p>Now search through the articles list. Find articles using: </p>

<pre><code>articles = []
tag_dict = {};
                       
for file in glob.glob("articles/*.json"):
    with open(file) as f:
        data = json.load(f)
        data["human_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(float(data['create_date']))) #Human readable timestamp
        articles.append([data, file.replace(".json", ".html")])
</code></pre>

<p>We can then compile it into a single file by writing:</p>

<pre><code>for article in articles:
    print("Compiling", article[0]["title"], article[0]["tags"])
    write_article_from_template(article)
    article[0]["desc"] = extract_intro(article)
    if article[0].get("hidden", False) == False:
        for tag in article[0]["tags"]:
            this_tag = tag_dict.get(tag, [])
            this_tag.append(article[0])
            tag_dict[tag] = this_tag

print("Compiled all articles")</code></pre>

<p>Where we write the article using its template, extract a short description for the article (marked by the article-info tag) and then building a tag dictionary. We write the template by: </p>

<pre><code>def write_article_from_template(article):
    final_path = ARTICLES_PATH + article[0]["id"] + ".html";
    with open(article[1], 'r') as article_file:
        article_data = article_file.read()
        final_data = ARTICLE_TEMPLATE;
        final_data = final_data.replace('{{A_CONTENT}}}', article_data)
        final_data = final_data.replace('{{A_TITLE}}}', article[0]["title"])
        final_data = final_data.replace('{{A_TAGS}}}', ', '.join(article[0]["tags"]))
        final_data = final_data.replace('{{A_TIME}}}', article[0]["human_time"])

        with open(final_path, 'w') as output_file:
            output_file.write(final_data)</code></pre>


<b>List Generation</b>

<p>Run through the articles and build a list of all the tags and which articles reference them. For each of these tags we generate a template file.</p>

<b>Index Generation</b>

<p>In the fashion of KISS we can create an entirely static index page (index.html) by adding it to resources. We can use our knowledge of how lists and articles will be generated to create hotlinks using /article/id and /lists/tagname as links.</p>

<h3>Conclusion</h3>

Looks nice, simple to modify, cheap to serve. Your currently viewing the end result. Source code available.
