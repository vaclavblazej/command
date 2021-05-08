## TODOs

* investigate over-escaping, e.g. in 'proot' test command
* improve search (not only one whole regex)
* think of possible project configuration variables
* (seems hard) copy the command into command line instead of executing it

## Bugs from testing 

* unknown command gives help which says 'cmd --help' even if the command has alias c

## Done since the last release (to be moved to the CHANGELOG)

* help for arguments
* completion for arguments
* arguments for --save command
* Refactor global variables to classes
* Set default editor when EDITOR variable is not set
* --edit opens project or global command file in accordance to context and flags
