"""
Main module for rundoc command line utility.
"""
from rundoc import BadEnv
from rundoc.doc_commander import parse_doc, parse_output 
import argcomplete
import argparse
import logging
import rundoc
import sys

def __parse_args():
    """Parse command line arguments and return an argparse object."""
    parser = argparse.ArgumentParser(
        prog = "rundoc",
        description="Run code from markdown code blocks in controlled manner",
        )
    parser.add_argument(
        "-v", "--version", action="store_true",
        help="Show version info and exit."
        )
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="Enable debug mode with output of each action in the log."
        )
    subparsers = parser.add_subparsers(
        description="(use each command with -h for more help)",
        dest="cmd",
        )

    parser_run = subparsers.add_parser(
        "run",
        description="Run markdown as a script."
        )
    parser_run.add_argument(
        "mkd_file_path", type=str, action="store",
        help="Markdown file path."
        )
    parser_run.add_argument(
        "-t", "--tags", action="store",
        help='''Coma-separated list of tags (e.g. -t
            bash,bash_proj-2,python3_proj2). Part of tag until first underscore
            will be used as selected interpreter for that code. If no tags are
            provided, all code blocks will be used. Untagged code blocks will
            use bash as default interpreter.'''
        )
    parser_run.add_argument(
        "-p", "--pause", type=int, action="store",
        help='''Used in combination with -y. Pause N seconds before each code
                block. Defaults to 0.'''
        )
    parser_run.add_argument(
        "-s", "--step", type=int, action="store",
        help="Start at step STEP. Defaults to 1."
        )
    parser_run.add_argument(
        "-o", "--output", type=str, action="store",
        help='''Output file. All codes, modifications and output of execution
            will be saved here. This file can be later used as an argument to
            'rerun' command which will execute all steps without any user
            interaction.'''
        )
    parser_run.add_argument(
        "--light", action="store_true",
        help="Light terminal background."
        )
    parser_run.add_argument(
        "-y", "--yes", action="store_true",
        help="Confirm all steps with no user interaction."
        )
    parser_run.set_defaults(
        tags="",
        pause=0,
        step=1,
        output=None,
        )

    parser_rerun = subparsers.add_parser(
        "rerun",
        description="Run codes saved as json output by 'run' command."
        )
    parser_rerun.add_argument(
        "saved_output_path", type=str, action="store",
        help="Path of saved output file from 'run' or 'rerun' command."
        )
    parser_rerun.add_argument(
        "-s", "--step", type=int, action="store",
        help="Start at step STEP. Defaults to 1."
        )
    parser_rerun.add_argument(
        "-o", "--output", type=str, action="store",
        help='''Output file. All codes, modifications and output of execution
            will be saved here. This file can be later used as an input
            argument to 'rerun' command.'''
        )
    parser_rerun.set_defaults(
        step=1,
        output=None,
        )

    argcomplete.autocomplete(parser)
    return parser.parse_args()

def main():
    args = __parse_args()
    logging.basicConfig(
        format = '%(asctime)s.%(msecs)03d, %(levelname)s: %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = None,
        level = logging.DEBUG if args.debug else logging.CRITICAL,
        )
    if args.version:
        print("rundoc {} - Copyright {} {} <{}>".format(
            rundoc.__version__,
            rundoc.__year__,
            rundoc.__author__,
            rundoc.__author_email__,
            ))
        sys.exit(0)
    output = ""

    if args.cmd == 'run':
        try:
            darkbg = not args.light
            commander = parse_doc(args.mkd_file_path, args.tags, darkbg=darkbg)
        except BadEnv as e:
            print("{}{}{}".format(clr.red, e, clr.end))
            sys.exit(1)
        try:
            output = commander.run(
                step=args.step, yes=args.yes, pause=args.pause)
        except KeyboardInterrupt:
            commander.die_with_grace()
        except BadEnv as e:
            print("{}{}{}".format(clr.red, e, clr.end))
            sys.exit(1)
    if args.cmd == 'rerun':
        commander = parse_output(args.saved_output_path)
        try:
            output = commander.run(step=args.step, yes=True)
        except KeyboardInterrupt:
            commander.die_with_grace()
        except BadEnv as e:
            print("{}{}{}".format(clr.red, e, clr.end))
            sys.exit(1)
    if args.cmd in ('rerun', 'run') and args.output:
        with open(args.output, 'w+') as f:
            f.write(output)

if __name__ == '__main__':
    main()

