"""
Classes and tools for manipulating code block execution.
"""
from collections import OrderedDict
from prompt_toolkit import prompt
from rundoc import ansi, RundocException, BadEnv, CodeFailed, BadInterpreter
from rundoc.block import DocBlock
from time import sleep
import json
import logging
import os
import sys

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
        msg = msg.format(ansi.bold, ansi.end)
        print(msg)
        env_string = str(self)
        env_string = prompt( '[env]\n', default = env_string )
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
        """
        Set environment according to defined variables.
        """
        for var in self:
            os.environ[var] = self[var]

    def inherit_existing_env(self):
        """
        Override variable values with values from existing environment. Useful
        when you want "outside" environment to have authority over locally
        defined values.
        """
        for var in self:
            val = os.environ.get(var, '') or self.get(var)
            self[var] = val


class DocCommander(object):
    """
    Manages environment and DocBlock objects and executes them in succession.
    """
    def __init__(self):
        self.env = OrderedEnv(
            "\n{}==== env variables{}".format(ansi.bold, ansi.end)
            )
        self.secrets = OrderedEnv(
            "\n{}==== secrets{}".format(ansi.bold, ansi.end)
            )
        self.doc_blocks = []
        self.running = False
        self.step = None
        self.output = None

    @property
    def doc_block(self):
        """Current doc_block."""
        if self.step:
            return self.doc_blocks[self.step-1]
            # step-1 because steps start at 0 but are refered to as if they
            # start with 1
        else:
            return None

    def get_dict(self):
        return {
            'env': self.env,
            'code_blocks': [ x.get_dict() for x in self.doc_blocks ]
        }

    def add(self, code, tags, light=False):
        try:
            self.doc_blocks.append(
                DocBlock(
                    code=code,
                    tags=tags,
                    light=light,
                    )
                )
        except RundocException as re:
            logging.error(str(re))
            if self.running:
                self.doc_block.kill()
            sys.exit(1)

    def die_with_grace(self):
        if self.running:
            self.doc_block.kill()
            print("\n==== {}Quit at step {} with keyboard interrupt.{}\n".format(
                ansi.red,
                self.step,
                ansi.end,
                )
            )
        if self.output:
            self.output.write(
                json.dumps(self.get_dict(), sort_keys=True, indent=4))

    def write_output(self):
        if self.output:
            self.output.write(
                json.dumps(self.get_dict(), sort_keys=True, indent=4))
            print("Output written to: {}".format(self.output.name))

    def run(self,
        step=1, ask=False, breakpoint=[], inherit_env=False, pause=0, retry=0,
        retry_pause=1, output=None, **kwargs):
        """Run all the doc_blocks one by one starting from `step`.

        Args:
            step (int): Number of step to start with. Steps start at 1.
            ask (bool): Ask user to confirm each step.
            breakpoint (list): List of integers representing steps that are
                breakpoints. Rundoc will always prompt user on these steps no
                matter what value `ask` is set to.
            inherit_env (bool): Override env defaults in docs with exported
                values from outside env (for those that exist).
            pause (float): A delay in seconds before the start of each step.
            retry (int): Number of times a step will retry to execute before
                giving up and failing.
            retry_pause (float): Additional pause before retrying same step.
            output (file): Writable file-like object.
        """
        assert self.running == False
        if output is not None:
            self.output = output
        if inherit_env:
            self.env.inherit_existing_env()
            self.secrets.inherit_existing_env()
        if ask>=1:
            self.env.prompt()
            self.secrets.prompt()
        else:
            self.env.prompt_missing()
            self.secrets.prompt_missing()
        msg = "\n{}Running code blocks from supplied documentation."
        msg += "\nModify and/or confirm displayed code by pressing Return.{}"
        print(msg.format(ansi.bold, ansi.end))
        self.env.load()
        self.secrets.load()
        self.running = True
        self.step = step
        ask_for_prompt_once = False
        while self.step in range(step, len(self.doc_blocks)+1):
            prompt_this_time = \
                ask>=3 or ask_for_prompt_once or self.step in breakpoint
            tags = '[{}] '.format(self.doc_block.interpreter)
            tags += ' '.join(self.doc_block.tags[1:])
            prompt_text = "\n{}=== Step {} {}{}".format(
                ansi.bold, self.step, tags, ansi.end)
            print(prompt_text)
            if not prompt_this_time:
                print(self.doc_block)
                sleep(pause)
            self.doc_block.run(prompt = prompt_this_time)
            ask_for_prompt_once = False
            if self.doc_block.last_run['retcode'] == 0:
                print("{}==== Step {} done{}\n".format(
                    ansi.green, self.step, ansi.end))
                self.step += 1
                continue
            # in case it failed:
            self.running = False
            print("==== {}Failed at step {} with exit code '{}'{}\n".format(
                ansi.red, self.step, self.doc_block.last_run['retcode'], ansi.end))
            if ask>=2:
                msg = "{}{}Press RETURN to try again at step {}.\n"
                msg += "Ctrl+C to quit.{}"
                print(msg.format(ansi.red, ansi.bold, self.step, ansi.end))
                input()
                ask_for_prompt_once = True
                continue
            if len(self.doc_block.runs) > retry:
                self.write_output()
                raise CodeFailed("Failed at step {} with exit code '{}'".format(
                        self.step, self.doc_block.last_run['retcode']))
            print("{}Retry number {}.".format(
                ansi.bold, len(self.doc_block.runs), ansi.end), end="")
            sleep(retry_pause)
        self.step = 0
        self.write_output()

