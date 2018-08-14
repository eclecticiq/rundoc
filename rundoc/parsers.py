"""
Tools for parsing markdown docs.
"""
from bs4 import BeautifulSoup
from collections import defaultdict
from rundoc.block import DocBlock
from rundoc.commander import DocCommander
import json
import markdown
import markdown_rundoc.rundoc_code
import operator
import re


def parse_doc(input, tags="", must_have_tags="", must_not_have_tags="",
    light=False, **kwargs):
    """Parse code blocks from markdown file and return DocCommander object.

    Args:
        input (file): Readable file-like object pointing to markdown file.
        tags (str): Hash (#) separated list of tags. Markdown code block that
            contain at least one of them will be used.
        must_have_tags (str): Like 'tags' but require markdown code block to
            contain all of them (order not important).
        must_not_have_tags (str): Like 'tags' but require markdown code block
            to contain non of them.
        light (bool): Will use light backgrond color theme if set to True.
            Defaults to False.

    Returns:
        DocCommander object.
    """
    mkd_data = input.read()
    html_data = markdown.markdown(
        mkd_data,
        extensions = [ 
            'markdown_rundoc.rundoc_code(tags={},must_have_tags={}, must_not_have_tags={})'.format(
                tags, must_have_tags, must_not_have_tags,
                )
            ]
        )
    soup = BeautifulSoup(html_data, 'html.parser')
    commander = DocCommander()

    # find blocks
    def is_runnable_block(tag):
        if tag.name != 'code':
            return False
        if 'rundoc_selected' not in tag.get('class', {}):
            return False
        return not bool({
            "env",
            "environ",
            "environment",
            "secret",
            "secrets",
            }.intersection(tag.get('class', {})))
    code_block_elements = soup.findAll(is_runnable_block)
    for element in code_block_elements:
        tags_list = element.get_attribute_list('class')
        tags_list = list(filter(bool, tags_list))
        if tags_list:
            tags_list.remove('rundoc_selected')
            commander.add(element.getText(), tags_list, light)

    # find environments
    def is_environment(tag):
        if tag.name != 'code':
            return False
        if 'rundoc_selected' not in tag.get('class', {}):
            return False
        return bool({'env','environ','environment'}.intersection(
            tag.get('class', {})))
    env_elements = soup.findAll(is_environment)
    env_string = "\n".join([ x.string or '' for x in env_elements ])
    commander.env.import_string(env_string)

    # find secrets
    def is_secret(tag):
        if tag.name != 'code':
            return False
        if 'rundoc_selected' not in tag.get('class', {}):
            return False
        return bool({'secret','secrets'}.intersection(tag.get('class', {})))
    secrets_elements = soup.findAll(is_secret)
    secrets_string = "\n".join([ x.string for x in secrets_elements ])
    commander.secrets.import_string(secrets_string)
    return commander

def parse_output(input, exact_timing=False, light=False, **kwargs):
    """Load json output, create and return DocCommander object.

    Each code block recorded in the otput will be parsed and only code from
    successful attempts will be turned into code blocks for new session. The
    goal is to use original or user modified inputs as a new script.

    Args:
        output (file): Readable file-like object.
        exact_timing (bool): NOT IMPLEMENTED YET!
            If True, a code block will be created for each run try
            and pause between blocks and tries will be calculated from the
            timestamps recorded in the file. The goal is to recreate all exact
            steps that users may have done. Defaults to False.
        light (bool): Will use light backgrond color theme if set to True.
            Defaults to False.

    Returns:
        DocCommander object.
    """
    output_data = input.read()
    data = json.loads(output_data)
    commander = DocCommander()
    for d in data['code_blocks']:
        doc_block = DocBlock(
            code=d['runs'][-1]['user_code'],
            tags=d['tags'],
            light=light,
            )
        commander.doc_blocks.append(doc_block)
    return commander

def get_tags(input):
    tag_dict = defaultdict(int)
    mkd_data = input.read()
    html_data = markdown.markdown(
        mkd_data,
        extensions = [ 'markdown_rundoc.rundoc_code' ]
        )
    soup = BeautifulSoup(html_data, 'html.parser')
    match = re.compile("^.+$")
    code_block_elements = soup.findAll(name='code', attrs={"class":match,})
    for element in code_block_elements:
        class_name = element.get_attribute_list('class')[0]
        if class_name:
            for tag in class_name.split('#'):
                tag_dict[tag] += 1
    sorted_tag_dict = sorted(tag_dict.items(), key=operator.itemgetter(1),
        reverse=True)
    return sorted_tag_dict

def print_blocks(input, tags="", must_have_tags="", must_not_have_tags="",
    light=False, pretty=False):
    commander = parse_doc(input, tags, must_have_tags, must_not_have_tags,
        light)
    if pretty:
        step = 0
        for block in commander.doc_blocks:
            step += 1
            print("{}. [{}] {}".format(step, block.interpreter, '#'.join(block.tags)))
            print("=================")
            print(block)
            print("")
    else:
        print(json.dumps(commander.get_dict(), sort_keys=True, indent=4))

def print_clean_doc(input):
    mkd_data = input.read()
    print(
        re.sub(
            '(\\n```[^#:]*).*?(\\n.*?```\\n)',
            '\\1\\2',
            mkd_data,
            flags=re.DOTALL
            )
        )

