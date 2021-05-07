''' Helping functions to handle sub-process creation '''
import os
import shlex
import subprocess
from string import Template

from shcmdmgr.command import Command

def run_command(command_with_arguments):
    return subprocess.getoutput(command_with_arguments)

def run_script(command_with_arguments, formatter):
    try:
        process = subprocess.Popen(command_with_arguments)
        try:
            process.wait()
        except subprocess.TimeoutExpired as ex:
            process.kill()
            raise ex
    except PermissionError:
        formatter.print_str('Script: ' + str(command_with_arguments))
        formatter.print_str('could not be run, because the file is not executable')
    except KeyboardInterrupt:
        formatter.print_str()

def execute(logger, cmd: Command, args):
    if not args: args = []
    if isinstance(cmd.command, str):
        logger.verbose('running command: ' + cmd.command)
        cmd_subs = Template(cmd.command).substitute(os.environ)
        logger.debug('command with substituted variables: %s', str(cmd_subs))
        cmd_split = shlex.split(cmd_subs)
        logger.debug('command splitted into arguments: %s', str(cmd_split))
        subprocess.run(cmd_split + args, check=False)
    else:
        cmd.command(args)
