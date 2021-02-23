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

## Tuner FTDI module configuration utility
This utility allows FTDI FT2232H modules to be configured to the various configurations required for the Ryde receiver.
### Install

Install packaged dependencies:

```sudo apt-get install python3-urwid```

Install pip dependencies:

```pip install pyftdi```

### Usage

```
usage: python3 ftdiconf.py [-h] [-u] [-x]

Tuner FTDI module configuration utility

optional arguments:
  -h, --help           show this help message and exit
  -u, --update         Enable actual updates
  -x, --extra-configs  Allow flashing of all identifyable configs
```

### Interface

All navigation can be done with the keyboard arrow keys as well as a mouse on some platforms.

Modules can be selected either individually from the list or by using the various multi select options.

By default all programming operations are dry runs and no changes are saved to the flash, the -u option at startup is required to enable live updates.

The -x option allows all identifyable complete configs to be flashed rather than just the expected targets, this allows modules to be reverted to a factory setting if required.

## License

Ryde Utils provides a set of useful utilities for the Ryde Receiver project.

Copyright (C) 2021  Tim Clark

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses/.
