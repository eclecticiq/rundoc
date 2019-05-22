"""
Tools for parsing markdown docs.
"""
from bs4 import BeautifulSoup
from collections import defaultdict
from markdown_rundoc.rundoc_code import RundocCodeExtension
from rundoc.block import DocBlock, block_actions
from rundoc.commander import DocCommander
import json
import markdown
import operator
import re


def mkd_to_html(mkd, tags='', must_have_tags='', must_not_have_tags='',
        single_session='', selection_tag='rundoc_selected'):
    """Read markdown stream and return html string."""
    html_data = markdown.markdown(
        mkd,
        extensions = [ 
            RundocCodeExtension(
                tags=tags,
                must_have_tags=must_have_tags,
                must_not_have_tags=must_not_have_tags,
                single_session=single_session,
                selection_tag=selection_tag,
                )
            ]
        )
    return html_data

def parse_doc(input, tags="", must_have_tags="", must_not_have_tags="",
    single_session="", light=False, **kwargs):
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

    html_data = mkd_to_html(
        input.read(),
        tags,
        must_have_tags,
        must_not_have_tags,
        single_session,
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
    all_code = ""
    for element in code_block_elements:
        tags_list = element.get_attribute_list('class')
        tags_list = list(filter(bool, tags_list))
        if tags_list:
            tags_list.remove('rundoc_selected')
            if single_session:
                all_code += element.getText()
            else:
                commander.add(element.getText(), tags_list, light)
    if single_session:
        commander.add(all_code, [single_session], light)

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
        commander.env.extend(data['env'])
    return commander

def get_tags(input, **kwargs):
    """Read markdown file and return list of available tags."""
    tag_dict = defaultdict(int)
    html_data = mkd_to_html(input.read())
    soup = BeautifulSoup(html_data, 'html.parser')
    match = re.compile("^.+$")
    code_block_elements = soup.findAll(name='code', attrs={"class":match,})
    for element in code_block_elements:
        for class_name in element.get_attribute_list('class'):
            tag_dict[class_name] += 1
    if 'rundoc_selected' in tag_dict:
        del(tag_dict['rundoc_selected'])
    sorted_tag_dict = sorted(tag_dict.items(), key=operator.itemgetter(1),
        reverse=True)
    return sorted_tag_dict

def get_blocks(input, tags="", must_have_tags="", must_not_have_tags="",
    single_session="", light=False, pretty=False, **kwargs):
    commander = parse_doc(input, tags, must_have_tags, must_not_have_tags,
        single_session, light)
    blocks = ""
    if pretty:
        step = 0
        for block in commander.doc_blocks:
            step += 1
            blocks += "{}. [{}] {}".format(
                step, block.interpreter, '#'.join(block.tags))
            blocks += "\n=================\n"
            blocks += str(block)
            blocks += "\n"
    else:
        blocks = json.dumps(commander.get_dict(), sort_keys=True, indent=4)
    return blocks

def get_clean_doc(input):
    mkd_data = input.read()
    # clean all tags except the interpreter
    mkd_data = re.sub(
        '^(```[^#:]*).*$',
        '\\1',
        mkd_data,
        flags=re.MULTILINE
        )
    return mkd_data

