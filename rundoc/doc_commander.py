"""
Classes and tools for parsing markdown docs and manipulating their execution.
"""
from bs4 import BeautifulSoup
from collections import OrderedDict
from prompt_toolkit import prompt
from rundoc import BadEnv
from rundoc.doc_code import DocCode
from time import sleep
import json
import markdown
import os
import re
import sys

class clr:
    ''' 
    ANSI colors for pretty output.
    '''
    red = '\033[91m'
    green = '\033[92m'
    blue = '\033[94m'
    yellow = '\033[93m'
    bold = '\033[1m'
    underline = '\033[4m'
    end = '\033[0m'

class OrderedEnv(OrderedDict):
    """Dictionary of environment variables.

    Preserves order of variables as found in string. Lets you load a string of
    variable definitions (new line separated var=value pairs).
    You can append (variable, value) pairs and extend with objects of the same
    type.
    Can prompt user to modify variables. Let's you load variables into os.
    Functions append, extend and import_string contain  'collect_existing_env'
    argument. If you set it to True, then these functions will not overwrite
    existing and os variables in case you set them to empty values (assumes
    that giving empty string as value means you don't with to change those
    variables).
    """
    def __init__(self, title=None):
        super().__init__()
        self.title = title

    def __str__(self):
        return "\n".join([ var+"="+self[var] for var in self ])

    def append(self, var, val, collect_existing_env=True):
        if collect_existing_env:
            val = val or self.get(var) or os.environ.get(var, '')
        self[var] = val

    def extend(self, env, collect_existing_env=True):
        for var in env:
            self.append(var, env[var], collect_existing_env)

    def import_string(self, env_string, collect_existing_env=True):
        for line in env_string.strip().split('\n'):
            if not line: continue
            if '=' not in line:
                raise BadEnv("Bad environment line: {}".format(line))
            var, val = line.split('=', 1)
            var = var.strip()
            val = val.strip()
            if not var:
                raise BadEnv("Bad environment line: {}".format(line))
            self.append(var, val, collect_existing_env)

    def prompt(self):
        if not len(self):
            return
        print(self.title)
        msg = "{}\tConfirm/supply/modify environment variables."
        msg += "\n\tPress Return to finish.{}"
        msg = msg.format(clr.bold, clr.end)
        print(msg)
        env_string = str(self)
        env_string = prompt( '» ', default = env_string )
        self.clear()
        self.import_string(env_string, collect_existing_env=False)

    def prompt_missing(self):
        missing = self.__class__(self.title)
        for var in self:
            if not self[var]:
                missing.append(var, '')
        missing.prompt()
        self.extend(missing, collect_existing_env=False)

    def load(self):
        for var in self:
            os.environ[var] = self[var]


class DocCommander(object):
    """
    Manages environment and DocCode objects and executes them in succession.
    """
    def __init__(self):
        self.env = OrderedEnv(
            "\n{}==== env variables{}".format(clr.bold, clr.end)
            )
        self.secrets = OrderedEnv(
            "\n{}==== secrets{}".format(clr.bold, clr.end)
            )
        self.doc_codes = []
        self.running = False
        self.failed = False
        self.current_doc_code = None
        self.current_step = None

    def get_dict(self):
        return {
            'env': self.env,
            'code_blocks': [ x.get_dict() for x in self.doc_codes ]
        }

    def add(self, code, interpreter='bash', darkbg=True):
        if not interpreter:
            interpreter = 'bash'
        self.doc_codes.append(DocCode(code, interpreter, darkbg))

    def die_with_grace(self):
        if self.running:
            self.current_doc_code.kill()
            print("\n==== {}Quit at step {} with keyboard interrupt.{}\n".format(
                clr.red,
                self.current_step,
                clr.end,
                )
            )

    def run(self, step=1, yes=False, pause=0):
        """Run all the doc_codes one by one starting from `step`.

        Args:
            step (int): Number of step to start with. Defaults to 1. Steps
                start at 1.
            yes (bool): Auto-confirm all steps without user interaction.
                Defaults to False.
            pause (int): Add a delay in seconds before the start of each step.
                Makes sense only when 'yes' is set to True. Defaults to 0.

        Returns:
            JSON representation of code blocks and outputs.
        """
        assert self.running == False
        assert self.failed == False
        if yes:
            self.env.prompt_missing()
            self.secrets.prompt_missing()
        else:
            self.env.prompt()
            self.secrets.prompt()
        msg = "\n{}Running code blocks from supplied documentation."
        msg += "\nModify and/or confirm displayed code by pressing Return.{}"
        print(msg.format(clr.bold, clr.end))
        self.env.load()
        self.secrets.load()
        self.running = True
        for doc_code in self.doc_codes[step-1:]:
            self.current_step = step
            self.current_doc_code = doc_code
            prompt_text = "\n{}=== Step {} [{}]{}".format(
                clr.bold,
                step,
                doc_code.interpreter,
                clr.end,
                )
            print(prompt_text)
            if yes:
                print(doc_code)
                sleep(pause)
            else:
                doc_code.prompt_user()
            self.current_doc_code.run() # run in blocking manner
            if doc_code.output['retcode'] != 0:
                self.failed = True
            if self.failed:
                self.running = False
                print("==== {}Failed at step {} with exit code '{}'{}\n".format(
                    clr.red,
                    step,
                    doc_code.output['retcode'],
                    clr.end,
                    )
                )
                self.current_doc_code = None
                break
            self.current_doc_code = None
            print("{}==== Step {} done{}\n".format(clr.green, step, clr.end))
            step += 1
        return json.dumps(self.get_dict(), sort_keys=True, indent=4)

def parse_doc(mkd_file_path, tags="", darkbg=True):
    """Parse code blocks from markdown file and return DocCommander object.

    Args:
        mkd_file_path (str): Path to markdown file.
        tags (str): Code highlight specifier in markdown. We can use this to
            filter only certain code blocks. If it's set to empty string or
            None, all code blocks will be used. Defaults to "bash".

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
    # collect all elements with selected tags as classes
    classes = re.compile(
        "(^|_)({})(_|$)".format('|'.join(tags.split(','))) if tags else '^(?!(env|secret)).*'
        )
    code_block_elements = soup.findAll('code', attrs={"class":classes,})
    commander = DocCommander()
    for element in code_block_elements:
        class_name = element.get_attribute_list('class')[0]
        interpreter = None
        if class_name:
            interpreter = class_name.split("_")[0]
        commander.add(
            element.getText(),
            interpreter,
            darkbg
        )
    # get env blocks
    classes = re.compile("^env(iron(ment)?)?$")
    env_elements = soup.findAll('code', attrs={"class":classes,})
    env_string = "\n".join([ x.string for x in env_elements ])
    commander.env.import_string(env_string)
    # get secrets blocks
    classes = re.compile("^secrets?$")
    secrets_elements = soup.findAll('code', attrs={"class":classes,})
    secrets_string = "\n".join([ x.string for x in secrets_elements ])
    commander.secrets.import_string(secrets_string)
    return commander

def parse_output(output_file_path):
    """Load json output, create and return DocCommander object.

    Args:
        output_file_path (str): Path to saved output file.

    Returns:
        DocCommander object.
    """
    output_data = None
    with open(output_file_path, 'r') as f:
        output_data = f.read()
    data = json.loads(output_data)
    commander = DocCommander()
    for d in data:
        doc_code = DocCode(d['code'], d['interpreter'])
        doc_code.user_command = d['user_code']
        commander.doc_codes.append(doc_code)
    return commander

