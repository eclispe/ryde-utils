#    Ryde Utils provides a set of useful utilities for the Ryde Receiver project.
#    Copyright © 2021 Tim Clark
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import urwid, time, socket, json, functools, argparse

# Urwid widget that requires ctrl to be held to havigate ListBox
class ListBoxRekey(urwid.ListBox):
    def keypress( self, size, key):
        keymap = {
                "ctrl up":"up",
                "ctrl down":"down",
                "ctrl page up":"page up",
                "ctrl page down":"page down",
                "ctrl home":"home",
                "ctrl end":"end",
                }
        if key in keymap:
            super().keypress(size, keymap[key])
            return None
        elif key in keymap.values():
            return key
        else:
            return super().keypress(size, key)

# Urwid widget that captures some events, maps the names and passes them to a provided callback
class EventSnag(urwid.WidgetWrap):
    def __init__(self, widget, keymap = {}, callback = None):
        self.widget = widget
        self.keymap = keymap
        self.callback = callback
        urwid.WidgetWrap.__init__(self, self.widget)

    def keypress( self, size, key):
        if key in self.keymap:
            if self.callback is None:
                return key
            elif self.callback(self.keymap[key]):
                return None
            else:
                return key
        else:
            return self.widget.keypress( size, key)


# Urwid widget for capturing, logging and running a callback on mapped events, also provides a help box
class EventFrame(urwid.WidgetWrap):
    def __init__(self, keymap, publishEventCallback, instructions):
        # components for the help box
        popupHeader = urwid.AttrMap(urwid.Text("Help", align='center'), 'heading')
        popupButton = urwid.Button("Close", self.closetab)
        self.instructionsWalker = urwid.SimpleListWalker([urwid.Text(instructions), popupButton])
        instructionsBox = urwid.ListBox(self.instructionsWalker)
        popupBox = urwid.LineBox(urwid.Padding(urwid.Frame(instructionsBox, header=popupHeader), left=2, right=2))

        # event log list walker
        self.walker = urwid.SimpleFocusListWalker([])

        # main parent
        self.cols = urwid.Columns([urwid.Padding(EventSnag(ListBoxRekey(self.walker), keymap, functools.partial(publishEventCallback, self.appendTxt)), left=2, right=2)])
        self.coltuple = (popupBox, self.cols.options())
        urwid.WidgetWrap.__init__(self, self.cols)

    # append text to the event log box includeing a timestamp
    def appendTxt(self, txt):
        txtBox = urwid.AttrMap(urwid.Text(time.strftime('%H:%M:%S')+": "+txt), None, focus_map='reversed')
        self.walker.append(txtBox)
        nextEl = self.walker.get_next(self.walker.get_focus()[1])
        if nextEl[0] is txtBox:
            self.walker.set_focus(nextEl[1])

    def handletab(self):
        if self.coltuple not in self.cols.contents:
            self.cols.contents.append(self.coltuple)
            self.cols.focus_position = self.cols.contents.index(self.coltuple)
        else:
            self.cols.focus_position = (self.cols.focus_position+1)%len(self.cols.contents)

    def closetab(self, event):
        self.cols.contents.remove(self.coltuple)
        self.instructionsWalker.set_focus(0)

    def keypress(self, size, key):
        if key == 'tab':
            self.handletab()
            return None
        else:
            return self.cols.keypress(size, key)

class RydeConsoleHandset(object):
    def __init__(self, host = 'localhost', port = 8765):
        # map of urwid events to ryde events
        keymap = {
            'up': 'UP',
            'down': 'DOWN',
            'left': 'LEFT',
            'right': 'RIGHT',
            'enter': 'SELECT',
            'delete': 'BACK',
            'insert': 'MENU',
            'end': 'POWER',
            'home': 'MUTE',
            'page up': 'CHAN+',
            'page down': 'CHAN-',
            '0': 'ZERO',
            '1': 'ONE',
            '2': 'TWO',
            '3': 'THREE',
            '4': 'FOUR',
            '5': 'FIVE',
            '6': 'SIX',
            '7': 'SEVEN',
            '8': 'EIGHT',
            '9': 'NINE',
            }

        # list of instructions lines
        instructions = []
        instructions.append("Press tab or left to switch away from help without closing\n\n")
        instructions.append("All supported keys should usable from just the numpad by using NumLock\n\nSupported keys:\n")
        # auto create key map instructions
        specialkeys = ['up', 'down', 'left', 'right', 'enter', 'delete', 'insert', 'end', 'home', 'page up', 'page down']
        for keypress in specialkeys:
            instructions.append(keymap[keypress]+": "+keypress+"\n")
        instructions.append("\nNumber keys are also supported\n")
        
        # Visible UI components
        eventBox = EventFrame(keymap, self.publishEventCallback, instructions)
        titlebox = urwid.AttrMap(urwid.Text('Ryde Network Console Handset', align='center'), 'title')
        footerbox = urwid.AttrMap(urwid.Text(["Press ",("highlight", "esc")," to exit, ",("highlight", "tab")," to show help or hold ",("highlight", "ctrl"), " to navigate the log."]), 'footer')
        # main layout frames
        main = urwid.Frame(eventBox, titlebox, footerbox)
        background = urwid.AttrMap(urwid.SolidFill(), 'bg')
        top = urwid.Overlay(main, background,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=20, min_height=5)

        # urwid colour pallette
        pallette = [
                ('bg', 'black', 'dark blue'),
                ('title', 'white, bold', 'dark red'),
                ('heading', 'white, bold', 'default'),
                ('footer', 'black', 'light gray'),
                ('highlight', 'light blue', 'light gray'),
                ('reversed', 'standout', '')
            ]

        # main urwid loop
        self.loop = urwid.MainLoop(top, palette=pallette, unhandled_input=self.unhandledEvent)

        self.host = host
        self.port = port

    def unhandledEvent(self, key):
        if key == 'esc':
            raise urwid.ExitMainLoop()

    def publishEventCallback(self, appendTxt, event):
        appendTxt(event)
        # form network request
        sendEventReq = {'request':'sendEvent', 'event':event}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as eventSocket:
            eventRespRaw = None
            try:
                eventSocket.connect((self.host, self.port))
                eventSocket.sendall(bytes(json.dumps(sendEventReq), encoding="utf-8"))
                eventRespRaw = eventSocket.recv(1024)
                eventSocket.close()
            except Exception:
                appendTxt("Network error while sending event")
            if eventRespRaw is not None: # No network errors
                try:
                    eventResp = json.loads(eventRespRaw)
                except json.JSONDecodeError:
                    eventResp = None
                    appendTxt("Unexpected server response, invalid json")
                if isinstance(eventResp, dict) and 'success' in eventResp and isinstance(eventResp['success'], bool):
                    if not eventResp['success']:
                        if 'error' in eventResp and isinstance(eventResp['error'], str):
                            appendTxt("Server returned error: "+eventResp['error'])
                        else:
                            appendTxt("Server returned general error")
                else:
                    appendTxt("Unexpected server response, invalid format")
            else:
                appendTxt("Unexpected server response")
        return True

    def run(self):
        self.loop.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network console handset for Ryde receiver")
        
    parser.add_argument("-H", "--host", help="network host name or address of Ryde receiver", default="localhost")
    parser.add_argument("-P", "--port", help="network port of Ryde receiver", default=8765)
    args = parser.parse_args()
    consoleHandset = RydeConsoleHandset(host = args.host, port = args.port)
    consoleHandset.run()
