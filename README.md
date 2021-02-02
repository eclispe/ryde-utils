# Ryde Utils

This is a set of utilities for use with the Ryde Player. The main application is at https://github.com/eclispe/rydeplayer/

The software is designed and tested on a Raspberry Pi 4 although they will likely run on other operating systems that support the dependancies.

## Ryde Network Console Handset
This utility allows buttons to be pushed on a Ryde receiver using a console application over a network.
### Install

Install packaged dependencies:

```sudo apt-get install python3-urwid```

### Usage

```
usage: python3 consolehandset.py [-h] [-H HOST] [-P PORT]

Network console handset for Ryde receiver

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  network host name or address of Ryde receiver
  -P PORT, --port PORT  network port of Ryde receiver
```

### Interface

In the application press ```esc``` to quit and ```tab``` to view the in app help.

To navigate the event log hold ```ctrl``` while it is focus and use the ```Up```, ```Down```, ```Page Up```, ```Page Down```, ```Home``` and ```End``` keys. If you are scrolled to the bottom of the event log it will auto scroll to keep up with new events.

All supported events should be accessible from the numpad by utilising numlock to acess the numbers, the other events are mapped to keys as below:

| Ryde Button | Keyboard Key |
| ----------- | ------------ |
| UP          | up arrow     |
| DOWN        | down arrow   |
| LEFT        | left arrow   |
| RIGHT       | right arrow  |
| SELECT      | enter        |
| BACK        | delete       |
| MENU        | insert       |
| POWER       | end          |
| MUTE        | home         |
| CHAN+       | page up      |
| CHAN-       | page down    |

## License

Ryde Utils provides a set of useful utilities for the Ryde Receiver project.

Copyright (C) 2021  Tim Clark

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses/.