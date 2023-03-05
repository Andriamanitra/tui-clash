# TUI Clash

Play Clash of Code style problems directly in terminal.

The system is not designed to be safe against cheating in any way whatsoever so only play with trustworthy people, mmmkay?

## How does it work?

The server is written in [Crystal-lang](https://crystal-lang.org/) – if you wish to host a game you will need to install that and compile `server.cr`.

The client is written in Python, its only external dependency being [Textual](https://textual.textualize.io/) framework for building graphical terminal user interfaces.

The two components communicate with each other through TCP sockets. The server is rather "dumb" – its only responsibilities are
* Sending puzzles to clients when a new round starts
* Receiving submissions from clients, and making sure they have the required format (JSON with keys "author", "command", and "code")
* Sending submissions received during a round to all clients when a round ends

The clients are responsible for handling testing and validating the code (all of the code will run on the client side – this allows you to use ANY programming language whatsoever as long as you have it installed on your own computer).
Because all of the validation is done client-side it is rather easy to cheat the system, but don't do that, mmmmkay?

As a player you will see a puzzle in the terminal user interface (TUI). The interface has two text inputs, one for specifying a command
used to run the code, and one to specify the source code file (`$FILE` in the command gets replaced by the source code file string). The
default command is `python3 $FILE` but you can replace it with any language/executable you wish, the system does not care.
Have fun!

## TODO / known bugs / what's missing / planned

* There is currently no command-line interface to specify things like which server to connect to, username, etc. so have fun modifying the source code
* There is no setuptools configuration to make it easily `pip install`able yet
* The user interface does not immediately refresh when a round ends unless you interact with it (moving the mouse should be enough)



## Contributing

Feel free to fork, issues and pull requests are also welcome!
