"""
Tools for parsing markdown docs.
"""
from bs4 import BeautifulSoup
from collections import defaultdict
from rundoc.block import DocBlock
from rundoc.commander import DocCommander
import json
import markdown
import operator
import re

def generate_match_class(tags="", must_have_tags="", must_not_have_tags="",
    tag_separator="#", is_env=False, is_secret=False):
    """Generate match_class(class_name) function.

    Function match_class(class_name) is used to filter html classes that
    comply with tagging rules provided. Lists of tags are hash (#) separated
    strings. Example: "tag1#tag2#tag3".

    Args:
        tags (str): At least one tag must exist in class name.
        must_have_tags (str): All tags must exist in class name. Order is not
            important.
        must_not_have_tags (str): None of these tags may be found in the class
            name.
        is_env (bool): If set to True then match only class names that begin
            with environment tag, otherwise don't match them.
        is_secret (bool): If set to True then match only class names that begin
            with secret tag, otherwise don't match them.
    Returns:
        Function match_class(class_name).
    """
    def match_class(class_name):
        if not class_name: class_name = "" # avoid working with None
        if is_env and is_secret:
            raise Exception("Block can't be both env and secret.")
        only_env = re.compile("^env(iron(ment)?)?($|{}).*$".format(
            re.escape(tag_separator)))
        if is_env and not only_env.match(class_name):
            return False
        only_secrets = re.compile("^secrets?($|{}).*$".format(
            re.escape(tag_separator)))
        if is_secret and not only_secrets.match(class_name):
            return False
        code_block = re.compile("^(?!(env(iron(ment)?)?|secrets?)).*$")
        if not (is_env or is_secret) and not code_block.match(class_name):
            return False
        match_tags = re.compile("^.*(^|{s})({tags})({s}|$).*$".format(
            tags = '|'.join(list(filter(bool, tags.split(tag_separator)))),
            s = re.escape(tag_separator)))
        if tags and not match_tags.match(class_name):
            return False
        match_all_tags = re.compile(
            "^{}.*$".format(''.join('(?=.*(^|{s}){tag}($|{s}))'.format(
                s = re.escape(tag_separator),
                tag = tag) for tag in list(
                    filter(bool, must_have_tags.split(tag_separator))))))
        if must_have_tags and not match_all_tags.match(class_name):
            return False
        not_match_tags = re.compile("^(?!.*(^|{s})({tags})($|{s})).*$".format(
            tags = '|'.join(list(filter(bool,
                must_not_have_tags.split(tag_separator)))),
            s = re.escape(tag_separator)))
        if must_not_have_tags and not not_match_tags.match(class_name):
            return False
        return True
    return match_class

def parse_doc(mkd_file_path, tags="", must_have_tags="", must_not_have_tags="",
    darkbg=True, tag_separator="#"):
    """Parse code blocks from markdown file and return DocCommander object.

    Args:
        mkd_file_path (str): Path to markdown file.
        tags (str): Hash (#) separated list of tags. Markdown code block that
            contain at least one of them will be used.
        must_have_tags (str): Like 'tags' but require markdown code block to
            contain all of them (order not important).
        must_not_have_tags (str): Like 'tags' but require markdown code block
            to contain non of them.
        darkbg (bool): Will use dark backgrond color theme if set to True.
            Defaults to True.
        tag_separator (str): Allows to use different tag separator. Defaults to
            hash symbol (#).

    Returns:
        DocCommander object.
    """
    mkd_data = ""
    with open(mkd_file_path, 'r') as f:
        mkd_data = f.read()
    html_data = markdown.markdown(
        mkd_data,
        extensions=['toc', 'tables', 'footnotes', 'fenced_code']
        )
    soup = BeautifulSoup(html_data, 'html.parser')
    commander = DocCommander()
    # collect all elements with selected tags as classes
    match = generate_match_class(tags, must_have_tags, must_not_have_tags,
        tag_separator=tag_separator)
    code_block_elements = soup.findAll(name='code', attrs={"class":match,})
    for element in code_block_elements:
        class_name = element.get_attribute_list('class')[0]
        if class_name:
            interpreter = class_name.split(tag_separator)[0]
            commander.add(element.getText(), interpreter, darkbg, class_name)
    # get env blocks
    match = generate_match_class(tags, must_have_tags, must_not_have_tags,
        is_env=True, tag_separator=tag_separator)
    env_elements = soup.findAll(name='code', attrs={"class":match,})
    env_string = "\n".join([ x.string for x in env_elements ])
    commander.env.import_string(env_string)
    # get secrets blocks
    match = generate_match_class(tags, must_have_tags, must_not_have_tags,
        is_secret=True, tag_separator=tag_separator)
    secrets_elements = soup.findAll(name='code', attrs={"class":match,})
    secrets_string = "\n".join([ x.string for x in secrets_elements ])
    commander.secrets.import_string(secrets_string)
    return commander

def parse_output(output_file, exact=False):
    """Load json output, create and return DocCommander object.

    Each code block recorded in the otput will be parsed and only code from
    successful attempts will be turned into code blocks for new session. The
    goal is to use original or user modified inputs as a new script.

    Args:
        output_file (str): Path to saved output file.
        exact (bool): NOT IMPLEMENTED YET!
            If True, a code block will be created for each run try
            and pause between blocks and tries will be calculated from the
            timestamps recorded in the file. The goal is to recreate all exact
            steps that users may have done. Defaults to False.

    Returns:
        DocCommander object.
    """
    output_data = None
    with open(output_file, 'r') as f:
        output_data = f.read()
    data = json.loads(output_data)
    commander = DocCommander()
    for d in data['code_blocks']:
        doc_block = DocBlock(d['runs'][-1]['user_code'], d['interpreter'],
            d['tags'])
        commander.doc_blocks.append(doc_block)
    return commander

def get_tags(mkd_file_path, tag_separator="#"):
    mkd_data = ""
    tag_dict = defaultdict(int)
    with open(mkd_file_path, 'r') as f:
        mkd_data = f.read()
    html_data = markdown.markdown(
        mkd_data,
        extensions=['toc', 'tables', 'footnotes', 'fenced_code']
        )
    soup = BeautifulSoup(html_data, 'html.parser')
    match = re.compile("^.+$")
    code_block_elements = soup.findAll(name='code', attrs={"class":match,})
    for element in code_block_elements:
        class_name = element.get_attribute_list('class')[0]
        if class_name:
            for tag in class_name.split(tag_separator):
                tag_dict[tag] += 1
    sorted_tag_dict = sorted(tag_dict.items(), key=operator.itemgetter(1),
        reverse=True)
    return sorted_tag_dict

def print_blocks(mkd_file_path, tags="", must_have_tags="",
    must_not_have_tags="", darkbg=True, tag_separator="#", pretty=False):
    commander = parse_doc(mkd_file_path, tags, must_have_tags,
        must_not_have_tags, darkbg, tag_separator)
    if pretty:
        step = 0
        for block in commander.doc_blocks:
            step += 1
            print("{}. [{}] {}".format(step, block.interpreter, block.tags))
            print("=================")
            print(block)
            print("")
    else:
        print(json.dumps(commander.get_dict(), sort_keys=True, indent=4))

