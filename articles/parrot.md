!=!=! Uuid: 16cb63d9-dc73-4870-a401-d5d5e1fca2fd
!=!=! Title: Parrot - Lightweight functional static website generation
!=!=! Tags: Projects, Web
!=!=! Created: 1628955411

![Parrot](${{{img:parrot.png}}} =x300)

!=!=! Intro: Start
Parrot is an opinionated static website generator written in Ocaml. A static website is a website that requires no application server, it is just a series of HTML pages served by a HTTP file server with no special application logic. Parrot creates a static website from a series of markdown articles and a website template, producing a website artifact that can be deployed to almost any HTTP server. The website template does not need to include any JavaScript or CSS dependencies, and is particularly well suited to lightweight blog generation. Parrot is used to create my personal website.
!=!=! Intro: End

### Overview

Parrot splits the structure of a website into four types of file:
- **Static**: Resources that are entirely static and do not change on build. These files are just copied into the build artifact and do not have access to the template engine. Typically used for CSS resources.
- **Image**: We treat images as a special type of static resource so that files can be processed during build and referenced symbolically using the templating engine. This allows for straightforward web optimization and less painful reorganization.
- **Article**: Bodies of content written in Markdown and rendered into HTML by Parrot before being placed in the build artifact. Every article includes a title, date, a set of tags and an optional introduction. These allow for it to be seamlessly transposed into a HTML artifact. Articles can be referenced by other templated pages and are organized into browsable lists through a set of tags. When presented in a list, the article introduction is presented alongside the title to give the reader an idea of the content.
- **Lists**: Browsable sets of articles systematically generated from tags. These can be linked to from the navigation bar or any other templated page. Lists form the foundation of discoverability on a Parrot website.

In addition to these components we require a template for the index file, the first page displayed when you visit the website. This is a special case and can include any content.

To link all of these components together Parrot includes a templating engine. The templating engine can resolve symbolic references to images, articles, lists. It is easily extended programmatically. By referencing pages symbolically we allow the website creator to focus on creating content without worrying about costly refactoring after making a change.

### Website Generation

When launching Parrot you supply a website source folder. This folder should have the layout:
- /articles/: A set of .md files with the content for the website.
- /templates/: index.html, article.html, nav.html, list.html, list_item.html
- /images/: Images used on the website.
- /static/: Any static resources such as CSS or JavaScript.

To render the website first Parrot prepares it's template engine and loads each of the template files into memory. Next, it will load each of the article markdown files, parse the markdown, render the article into HTML using the article template and then write the rendered articles to the build artifact. Next, lists of articles are constructed using the tags supplied in the article metadata. These lists are then rendered into HTML fragments for each article using the list item template. The list items are constructed with access to the template engine so can include additional content. The list of HTML fragments is then rendered into a HTML list using the list template and emitted to the build artifact.

After that, the index template is rendered and written to the artifact. Finally, images referenced in rendered files and the website static content are copied into the build artifact.

The resulting build artifact contains a complete website with relative URLs for all articles, lists and images.

### Article Structure

A typical is article is structured like:
```
\!=!=! Title: Test Page
\!=!=! Created: 1533832112.37042
\!=!=! Tags: Work

\!=!=! Intro: Start
Article introductory text.
\!=!=! Intro: End

The main body of content for the article.
```

The !=!=! segments are used to encode metadata into the markdown pages. The title is a string, created is either a numeric value in epoch time or a date, tags is a comma separated list of the lists that this article should belong to, and `Intro: Start` to `Intro: End` denote the content that should appear when presenting a text fragment of the article in list items.

### Template Strings

Principally Parrot operates by systematically substituting template strings,
constant or dynamic lookups from the website state, into templates in order to
construct HTML webpages for all of the articles, and lists of the website, as
well as the landing page. Content is substituted into templates and articles
through template strings in the form `${{{string}}}`. Template strings can
be constants, such as `${{{ARTICLE_CONTENT}}}` in the article template, or
dynamic, such as `${{{img:expose.png}}}` which instructs Parrot to generate
a web-optimized version of expose.png.

#### Index Template

The index template is used to construct the website index (or landing)
page, the first page users will see when visiting a site. The index template
is largely left to the developer, but supports image template strings and
`${{{NAV_BAR_CONTENT}}}`.

#### Article Template

The article template is used as the skeleton for each article, and template strings are used to include the content as each article is generated. The supported template strings are:
- `NAV_BAR_CONTENT`: For the navigation bar.
- `ARTICLE_TITLE`: The title of the article being rendered.
- `ARTICLE_CONTENT`: The converted content of the article markdown file.
- `ARTICLE_TAGS`: The lists to which this article belongs, extracted from the markdown metadata.
- `ARTICLE_TIME`: The time when this article was created, extracted from the markdown metadata.

#### List Template

List templates form the skeleton of the article lists, which allow viewers to browse through lists of similar content and can be linked to. List templates are split into two components, the overall list template and the list item template.

The overall list template is responsible for the list page theme and the placement of list items within it. It supports the following template strings:
- `NAV_BAR_CONTENT`: The content of the navigation bar.
- `LIST_TITLE`: The title of the list being viewed.
- `LIST_CONTENT`: Each item included in this list will be rendered into a list_item template and then included in the `LIST_CONTENT`.

The list item is the skeleton HTML for a single entry into the list. It includes the following template strings:
- `LI_NAME`: The name of the article being referenced.
- `LI_DESCRIPTION`: The short description of the article extracted from the article metadata.
- `LI_TAGS`: The list of tags (lists) that this article belongs to, extracted from the article metadata.
- `LI_DATE`: The time that this article was created, which is extracted from the article metadata.

#### Linking to lists

Template strings can be used to create links to lists, avoiding the need
for embedding absolute paths which may change. To use a template string to
refer to a link use `${{{list:list_name}}}` in either a template or article
and it will be automatically resolved to a relative link to that list in the
website artifact. To use this in a markdown article you would use a markdown
link, for example `[Click here to find out more](${{{list:mylist}}})`. When
embedding a link in a HTML fragment, such as a template, you would use an
`<a>` tag, for example `<a href="${{{link:mylist}}}">click here for more!</a>`.

#### Linking to articles

Like lists, articles can be referenced in content using template strings. The
template string format for articles is `${{{article:Article Uuid}}}` and
these templates can be used in the same places as list template strings.

#### Images

Parrot can automatically images requested through template strings to desired sizes while building a website. Image template strings come in the form `${{{img:image_name.filetype}}}` and the image is expected to be in a subdirectory of the `images/` path of the source site.

### Source Code

The project is completely open source and available on [Github](https://github.com/jawline/Parrot2/).
