"""
Main module for rundoc command line utility.
"""
from rundoc import BadEnv, CodeFailed
from rundoc.commander import parse_doc, parse_output 
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
        "mkd_file", type=str, action="store",
        help="Markdown file path."
        )
    parser_run.add_argument(
        "-t", "--tags", action="store",
        help='''Hash (#) separated list of tags (e.g. -t bash#proj-2#test_3).
                Part of tag until first hash will be used as selected
                interpreter for that code. If no tags are provided, all code
                blocks will be used. Untagged code blocks will use bash as
                default interpreter.'''
        )
    parser_run.add_argument(
        "-i", "--inherit-env", action="store_true",
        help='''Override default env variable values with values from existing
                environment. Useful when you export variables before running
                rundoc and expect them to override default values that are set
                in the docs.'''
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
                will be saved here. This file can be later used as an argument
                to 'replay' command which will execute all steps without any
                user interaction.'''
        )
    parser_run.add_argument(
        "--light", action="store_true",
        help="Light terminal background."
        )
    parser_run.add_argument(
        "-y", "--yes", action="store_true",
        help="Confirm all steps with no user interaction."
        )
    parser_run.add_argument(
        "-r", "--retry", type=float, action="store",
        help='''Number of retries for failed code blocks when using -y option.
                Defaults to 0.'''
        )
    parser_run.add_argument(
        "-P", "--retry-pause", type=float, action="store",
        help='''Pause N seconds before retrying. Actual pause will be max value
                of --pause or --retry-pause. Defaults to 1.'''
        )
    parser_run.set_defaults(
        tags="",
        inherit_env=False,
        pause=0,
        step=1,
        retry=0,
        retry_pause=1,
        output=None,
        )

    parser_replay = subparsers.add_parser(
        "replay",
        description="Run codes saved as json output by 'run' command."
        )
    parser_replay.add_argument(
        "saved_output", type=str, action="store",
        help="Path of saved output file from 'run' or 'replay' command."
        )
    parser_replay.add_argument(
        "-p", "--pause", type=int, action="store",
        help="Pause N seconds before each code block. Defaults to 0."
        )
    parser_replay.add_argument(
        "-s", "--step", type=int, action="store",
        help="Start at step STEP. Defaults to 1."
        )
    parser_replay.add_argument(
        "-o", "--output", type=str, action="store",
        help='''Output file. All codes, modifications and output of execution
                will be saved here. This file can be later used as an input
                argument to 'replay' command.'''
        )
    parser_replay.add_argument(
        "--light", action="store_true",
        help="Light terminal background."
        )
    parser_replay.add_argument(
        "-r", "--retry", type=float, action="store",
        help="Number of retries for failed code blocks. Defaults to 0."
        )
    parser_replay.add_argument(
        "-P", "--retry-pause", type=float, action="store",
        help='''Pause N seconds before retrying. Actual pause will be max value
                of --pause or --retry-pause. Defaults to 1.'''
        )
    parser_replay.set_defaults(
        pause=0,
        step=1,
        retry=0,
        retry_pause=1,
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
        level = logging.DEBUG if args.debug else logging.WARNING,
        )
    if args.version:
        print("rundoc {} - Copyright {} {} <{}>".format(
            rundoc.__version__,
            rundoc.__year__,
            rundoc.__author__,
            rundoc.__author_email__,
            ))
        sys.exit(0)

    if args.cmd == 'run':
        try:
            darkbg = not args.light
            commander = parse_doc(args.mkd_file, args.tags, darkbg=darkbg)
        except BadEnv as e:
            print("{}{}{}".format(clr.red, e, clr.end))
            sys.exit(1)
        try:
            commander.run(
                step=args.step,
                yes=args.yes,
                inherit_env=args.inherit_env,
                pause=args.pause,
                retry=args.retry,
                retry_pause=args.retry_pause,
                output_file=args.output,
                )
        except KeyboardInterrupt:
            commander.die_with_grace()
            sys.exit(1)
        except BadEnv as e:
            print("{}{}{}".format(clr.red, e, clr.end))
            sys.exit(1)
        except CodeFailed as e:
            sys.exit(1)
    if args.cmd == 'replay':
        try:
            commander = parse_output(args.saved_output)
        except Exception as e:
            logger.error('Failed to parse file: {}'.format(e))
            sys.exit(1)
        try:
            commander.run(
                step=args.step,
                yes=True,
                inherit_env=False,
                pause=args.pause,
                retry=args.retry,
                retry_pause=args.retry_pause,
                output_file=args.output,
                )
        except KeyboardInterrupt:
            commander.die_with_grace()
            sys.exit(1)
        except BadEnv as e:
            print("{}{}{}".format(clr.red, e, clr.end))
            sys.exit(1)
        except CodeFailed as e:
            sys.exit(1)

if __name__ == '__main__':
    main()

