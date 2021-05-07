**DISCLAIMER (WORK IN PROGRESS):**
As of Feb 2021 this project is still work in progress.

It **IS** designed to

* make a clear overview of custom-made commands
* provide a common user interface for the commands
* provide a clear way to setup commands which work well with this tool

It **IS NOT** designed to

* provide standard functions or libraries to be used in the custom-made commands
* check correctness or analyse the commands

## Installation

To install Shell command manager run

```sh
pip3 install shcmdmgr
```

## Basic usage

Use `cmd -s` (or `cmd --save`) to catalogue a command. For example `lsb_release -a`.

```sh
$ lsb_release -a
Distributor ID:	Ubuntu
Description:	Ubuntu 20.04 LTS
Release:	20.04
Codename:	focal

$ cmd --save
The command to be saved: lsb_release -a   % note that this was pre-filled from history
Alias: sysversion
Short description: Shows the system version
```

Run the command either by invoking the alias.

```sh
$ cmd sysversion
Distributor ID:	Ubuntu
Description:	Ubuntu 20.04 LTS
Release:	20.04
Codename:	focal
```

To edit the command catalogue run `cmd --edit` (or `cmd -e`) which runs `$EDITOR ./<script_location>/commands.json` command or open and edit the catalogue file manually.

```sh
$ cmd --edit
% The "$EDITOR" opens the content similar to the following
[
    {
        "command": "lsb_release -a",
        "description": "Show the version number of the system",
        "alias": "sysversion",
        "creation_time": "2020-04-11 00:24:27"
    },
    {
        "command": "do-release-upgrade",
        "description": "Upgrades the system to the newest released version",
        "alias": "sysupgrade",
        "creation_time": "2020-04-11 00:25:08"
    }
]
```

### Enabling completion

Completion is supported in `bash` and `zsh` shells, but it must be enabled manually.
Installing the completion is the matter of adding source to your RC file.

The correct command can be emitted by invoking `--completion <shell>` command.

```sh
cmd --completion bash >> ~/.bashrc    # for bash
cmd --completion zsh >> ~/.zshrc      # for zsh
```

---

## Advanced (work in progress)

### Installation

To get the latest (non-stable) development version run the following.

```sh
pip3 install git+https://github.com/vaclavblazej/shell-command-manager.git
```

For development setup you may fork the repository, clone it, and create a symlink.

```sh
git clone git@github.com:vaclavblazej/shell-command-manager.git
ln -s "$PWD/shell-command-manager/bin/cmd.sh" ~/bin/cmd
```

### Parts

We manage custom scripts, their help, and completion.

* execution
* help
* completion

One function for all three because they have too much in common.
Flags used to determine what we want to return.

All three variants are delegated lower (into arguments) and in the lowest level, we return (or do) the wanted result.
In execution, we perform the task.
In help and completion, we set the result into the relevant location.

### Execution

The custom script should be an executable file.

### Help

Help is invoked by calling `script --help <arguments>` where arguments are in the precise form as they would have been without the `--help` argument.
It prints a string to standard output which describes what our current command does, and if there are any expected arguments.

### Completion

Completion is invoked by calling `script --complete <arguments>` and prints out the list of words which are sensible arguments in the next places.
The last argument is considered as *argument prefix* and is used to filter out possible words.
If no filtering is wanted, the last argument should be empty-string.

