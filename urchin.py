from configparser import ConfigParser
# from mischiefparsing import MisParsing
from subprocess import Popen, PIPE
from typing import Tuple
from rich import print
from rich.console import Console


# ==================================================
# filename: urchin.py
# coding style: yapf
# ==================================================

version = "0.0.1"

"""It will read the config file and get the command,
then execute the command and report the message to
the server module.
Because the function is awkward and imperfect compared to
Make,so it is called a little urchin.
"""


# the flag of kill subthread
#   True:   kill the thread and stop execute surplus commands
#   False:  nothing to do
kill_flag = False


def getCommands() -> dict:
    # TODO:read mischief
    """Read config file and get all available commands.
    available commands means that the option in the
    section whom name is same with the section.The
    function will return the available commands
    dictionary,which the key of the commands dictionary
    is the command name,and the value is the command itself.
    """

    # available commands
    commands = {}

    config = ConfigParser()
    # read the config file
    config.read("urchinmake.conf", encoding="UTF-8")
    # get the sections list
    sections = config.sections()
    # find the option in the section whom name is same
    # with the section.
    for section in sections:
        options = config.options(section)
        if "ctl_ignore" in options:
            ign_err = config.getboolean(section, "ctl_ignore")
        else:
            ign_err = False

        if section in options:
            commands[section] = (config.get(section, section), ign_err)

    return commands


def executeCommand(
        command: str,
        commandname: str) -> Tuple[bool, str]:
    """Run the command and return weather the command
    executed successfully.
    If not ,then return the type of error at the same
    time.
    """

    global kill_flag

    # ==================================================
    # ---------------------ATTTION!---------------------
    # Please do not arbitrarily modify the encoding
    # format in Popen.
    # In Windows CMD,Chinese characters use GBK encoding;
    # but in Linux Bash,Chinese characters use UTF-8
    # encoding.
    # The server module will running on linux, so if you
    # have modified it for debugging on windows, please
    # make sure to change it to UTF-8 before releasing the
    # official version!
    # ==================================================
    # use popen execute the command and return weather it
    # success
    # TODO:auto change the paras by system
    p = Popen(
        command, shell=True, stdout=PIPE, stderr=PIPE, encoding="UTF-8")
    # ==================================================
    # ---------------------ATTTION!---------------------
    # Use IS NOT when single step debugging if you need
    # observe the implementation results.Please use IS
    # when publishing the official version.
    # Because when single step debugging,the execution
    # speed of the program is faster than that of the
    # debugger.
    # ==================================================
    while p.poll() is None:
        if kill_flag:
            # DONE:kill the subthread
            p.kill()
        # ==================================================
        # ---------------------ATTTION!---------------------
        # Please do not arbitrarily modify the judgment
        # donditions here.
        # In Windows,return 0 means successful exection;
        # but in Linux,return 1 means successfull exection.
        # The server module will running on linux, so if you
        # have modified it for debugging on windows, please
        # make sure to change it to NOT EQUAL before releasing
        # the official version!
        # ==================================================
        else:
            if p.wait() != 0:
                print("[red]" + commandname + " execute failed!")
                return (False, p.stderr.read())
            else:
                print("[green]" + commandname + " execute successed!")
                return (True, p.stdout.read())


# DONE:add ignore mode:form client and conf file
# DONE:add kill command
# DONE:sustain delivering the arguments
# software control
def sftwrCtrl(
        command: str,
        subargs: dict,
        ignmode: bool = False) -> Tuple[bool, str]:
    """Receive the command and judge that weather it belongs to
    the available commands and excuting it.
    Use ignmode to control whether to ignore errors globally.

    When the function get a string,it will be judged weather it
    belongs to the available commands,if it is an available commands,
    then the function will check if the subcommands in it also
    belongs to an available commands,until the subcommands is not
    a available command,then try to exectute it.

    args:
    ==========
    command: the command name.
    subargs: the replenish of commands,the key is the command name,
    the value is replenish of commands.
    ignmode: ignore the errors.
    """

    def commandDisassembly(
            command: str,
            subargs: dict,
            ignmode: bool = False,
            exec_is_success: bool = True) -> Tuple[bool, bool, str, bool]:
        """In order to realize the requirement of function, it is
        necessary to distinguish the first judgment from other
        judgments. This function defines the situation of other
        judgments.
        """

        global kill_flag

        # record log when ignore mode
        log = ""

        continue_flag = True
        ign_err = False

        for subcommand in commands[command][0].split(" && "):
            continue_flag = not kill_flag
            if continue_flag:
                if (subcommand in commands):
                    exec_is_success, continue_flag, info, _ = \
                        commandDisassembly(
                            subcommand, subargs, ignmode, exec_is_success)
                    log += info
                    continue_flag = not kill_flag
                else:
                    # is the command has subarg?
                    try:
                        subarg = subargs[command]
                    except KeyError:
                        subarg = ""

                    continue_flag, info = executeCommand(
                        commands[command][0] + subarg, command)
                    log += info
                    ign_err = commands[command][1]
                    # for multy-step commands, must judge whether
                    # each step is executed successfully
                    exec_is_success = exec_is_success and continue_flag
                    # if kill subthread
                    if kill_flag:
                        print("[yellow]stop by user...")
                        continue_flag = False
                    else:
                        # if ignore the command error
                        # or enable the ignore mode globally
                        if continue_flag:
                            pass
                        elif ign_err or ignmode or continue_flag:
                            print("[yellow]Ignore error,continue execution...")
                            continue_flag = True
                        else:
                            continue_flag = False
            else:
                break

        return exec_is_success, continue_flag, log, ign_err

    # Use rich.Console to make the output more colorful
    # and readable
    console = Console()

    commands = getCommands()
    # TODO:print out the available commands
    if command in commands:
        console.rule("[yellow]" + command)
        is_success, _, log, ign_err = commandDisassembly(
            command, subargs, ignmode)
        if kill_flag:
            console.rule("[red]stop by user...")
            return False, log + "\nstop by user\n"
        else:
            if is_success:
                console.rule("[green]success!")
                return True, log + "\nsuccess\n"
            elif ign_err or ignmode or is_success:
                console.rule("[red]ignore fail...")
                return True, log + "\nignore fail\n"
            else:
                console.rule("[red]fail!")
                return False, log + "\nfail\n"
    else:
        print("Looks like your input is not supported command.")
        print("You can change or add support commands by")
        print("editing [bold]Mischief[/bold].")
        print("Listed below are currently supported commands:")
        for key in commands:
            print(key)
        print("Please modify your command!")
        return False, "command not in config file"


def killSubprocess(killflag: bool = False):
    """Receive control commands and perform operations according to
    the control commands.

    If a control commands is recieved during execution,the control
    command will be excuted first.
    If ignmode is enabled,all errors will be ignored during execution.
    """
    global kill_flag

    kill_flag = killflag


# only for debug
# if __name__ == "__main__":
    # print(sftwrCtrl("all", True)[1])
