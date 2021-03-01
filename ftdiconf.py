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

import enum, urwid, argparse
import configparser, io
import pyftdi.ftdi
import pyftdi.usbtools
import pyftdi.eeprom
import pyftdi

# enum of usb module hex dumps to base configs on
# this is a temporary solution until pyftdi supports more properties
class ModuleBaseRAW(enum.Enum):
    FACTORY = (enum.auto(), "0808030410600007a04b080011119a0aa426ca1200000000560000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0346005400440049002603460054003200320033003200480020004d0069006e0069004d006f00640075006c0065001203460054003400510046004e0044004e00020300000000000000000000000000000000000000000000000000000000000000003961")
    TUNER = (enum.auto(), "0001030410600007c000080033339a0aa424c81200000000560000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a034600540044004900240355005300420020003c002d003e0020004e0049004d002000740075006e006500720012034400410034004d00470045005a004b000000000000000000000000000000000000000000000000000000000000000000000000004a42")

    def __init__(self, enum, raw):
        self._raw = raw
    
    @property
    def baselineIni(self):
        config = configparser.ConfigParser()
        config.add_section('raw')
        config.set('raw','@00',self._raw)
        configIO = io.StringIO()
        config.write(configIO)
        configIO.seek(0)
        return configIO

# enum of known module configs
class ModuleConfigs(enum.Enum):
    UNKNOWN = (enum.auto(), frozenset(), False, False, False, None)
    GENERAL = (enum.auto(), frozenset([
        ('channel_a_type', 'UART'),
        ('chip', 86),
        ('group_0_drive', True),
        ('group_0_schmitt', False),
        ('group_0_slew', False),
        ('group_1_drive', True),
        ('group_1_schmitt', False),
        ('group_1_slew', False),
        ('group_2_drive', True),
        ('group_2_schmitt', False),
        ('group_2_slew', False),
        ('group_3_drive', True),
        ('group_3_schmitt', False),
        ('group_3_slew', False),
        ('has_serial', True),
        ('in_isochronous', False),
        ('out_isochronous', False),
        ('product_id', 24592),
        ('suspend_dbus7', pyftdi.eeprom.FtdiEeprom.CFG1(0)),
        ('suspend_pull_down', False),
        ('type', 1792),
        ('vendor_id', 1027)
    ]), False, False, False, None)
    TUNER = (enum.auto(), GENERAL[1] | frozenset([
        ('channel_a_driver', 'D2XX'),
        ('channel_b_type', 'FIFO'),
        ('remote_wakeup', False),
        ('self_powered', True),
        ('channel_b_driver', 'D2XX'),
        ('usb_version', 13107),
        ('power_max', 0)
    ]), False, False, False, ModuleBaseRAW.TUNER)
    FACTORY = (enum.auto(), GENERAL[1] | frozenset([
        ('channel_a_driver', 'VCP'),
        ('channel_b_driver', 'VCP'),
        ('channel_b_type', 'UART'),
        ('power_max', 150),
        ('product', 'FT2232H MiniModule'),
        ('remote_wakeup', True),
        ('self_powered', False),
        ('usb_version', 4369),
    ]), True, False, True, ModuleBaseRAW.FACTORY)
    MINITIOUNER = (enum.auto(), TUNER[1] | frozenset([
        ('product', 'USB <-> NIM tuner'),
    ]), True, True, True, ModuleBaseRAW.TUNER)
    MINITIOUNEREXPRESS = (enum.auto(), TUNER[1] | frozenset([
        ('product', 'MiniTiouner-Express'),
    ]), True, False, False, ModuleBaseRAW.TUNER)
    KNUCKER = (enum.auto(), TUNER[1] | frozenset([
        ('product', 'CombiTuner-Express'),
    ]), True, True, True, ModuleBaseRAW.TUNER)
    
    def __init__(self, enum, configset, canIdentify, flashableConfig, flashableDevice, rawBaseline):
        self._configset = configset
        self._canIdentify = canIdentify
        self._flashableConfig = flashableConfig
        self._flashableDevice = flashableDevice
        self._rawBaseline = rawBaseline

    @property
    def configSet(self):
        return self._configset

    @property
    def canIdentify(self):
        return self._canIdentify

    @property
    def flashableConfig(self):
        return self._flashableConfig

    @property
    def flashableDevice(self):
        return self._flashableDevice

    @property
    def rawBaseline(self):
        return self._rawBaseline

# urwid check box but also holds a device id and a current config
class ModuleCheckBox(urwid.CheckBox):
    def __init__(self, label, device, config):
        self._device = device
        self._config = config
        super().__init__(label)

    @property
    def device(self):
        return self._device

    @property
    def config(self):
        return self._config

# urwid text box for displaying unidentified modules but is compatible with the check box
class ModuleTextBox(urwid.Text):
    def __init__(self, label, device, config):
        self._device = device
        self._config = config
        super().__init__(label)

    @property
    def device(self):
        return self._device

    @property
    def config(self):
        return self._config

# urwid module that pops up a simple message box over the top level widget
class MessagePopUp(urwid.Overlay):
    def __init__(self, loop, messageText = "", messageTitle = None):
        self.loop = loop
        okButton = urwid.Button('OK', self.handleOk)

        self.contentlist = urwid.Pile([])
        if messageTitle is not None:
            self.contentlist.contents.append((urwid.Text(('heading', messageTitle), align="center"), self.contentlist.options('pack')))
        self.contentlist.contents.append((urwid.Text(messageText), self.contentlist.options('pack')))
        self.buttonBox = urwid.GridFlow([okButton], 7, 1, 1, 'center')
        self.contentlist.contents.append((self.buttonBox, self.contentlist.options('pack')))
        self.contentlist.set_focus(len(self.contentlist.contents)-1)
        self.mainBox = urwid.LineBox(self.contentlist)
    
    def open(self, button=None):
        self.buttonBox.focus_position = 0
        urwid.Overlay.__init__(self, self.mainBox, self.loop.widget,
				align='center', width=('relative', 50),
				valign='middle', height='pack',
				min_width=20, min_height=5)
        self.loop.widget = self

    def close(self, button=None):
        self.loop.widget = self.bottom_w

    def handleOk(self, button):
        self.close(None)

# urwid module that pops up a simple confirmation box over the top level widget
class ConfirmPopUp(urwid.Overlay):
    def __init__(self, loop, messageText = "", messageTitle = None, callback = None, userData = None):
        self.loop = loop
        self.callback = callback
        self.userData = userData
        yesButton = urwid.Button('Yes', self.handleYes)
        noButton = urwid.Button('No', self.handleNo)

        self.contentlist = urwid.Pile([])
        if messageTitle is not None:
            self.contentlist.contents.append((urwid.Text(('heading', messageTitle), align="center"), self.contentlist.options('pack')))
        self.contentlist.contents.append((urwid.Text(messageText), self.contentlist.options('pack')))
        self.buttonBox = urwid.GridFlow([noButton, yesButton], 7, 10, 1, 'center')
        self.contentlist.contents.append((self.buttonBox, self.contentlist.options('pack')))
        self.contentlist.set_focus(len(self.contentlist.contents)-1)
        self.mainBox = urwid.LineBox(self.contentlist)
    
    def open(self, button=None):
        self.buttonBox.focus_position = 0
        urwid.Overlay.__init__(self, self.mainBox, self.loop.widget,
				align='center', width=('relative', 50),
				valign='middle', height='pack',
				min_width=20, min_height=5)
        self.loop.widget = self

    def close(self, button=None):
        self.loop.widget = self.bottom_w

    def handleYes(self, button):
        self.close(None)
        if self.callback is not None:
            self.callback(self.loop, self.userData)

    def handleNo(self, button):
        self.close(None)

# urwid module that pops up a progress bar box over the top level widget
class ProgressPopUp(urwid.Overlay):
    def __init__(self, loop, callback = None, userData = None):
        self.loop = loop
        self.callback = callback
        self.userData = userData
        self.progressBar = urwid.ProgressBar('ProgressBack', 'ProgressFore')
        self.contentlist = urwid.Pile([])
        self.mainBox = urwid.LineBox(self.contentlist)
    
    def open(self, title, doneValue):
        self.progressBar.done = doneValue
        self.contentlist.contents[:] = [(urwid.Text(('heading',title), align='center'), self.contentlist.options('pack')), (self.progressBar, self.contentlist.options('pack'))]
        urwid.Overlay.__init__(self, self.mainBox, self.loop.widget,
				align='center', width=('relative', 50),
				valign='middle', height='pack',
				min_width=20, min_height=5)
        self.loop.widget = self

    def close(self, button):
        self.loop.widget = self.bottom_w
        if self.callback is not None:
            self.callback(button, self.userData)

    def setProgress(self, newProgress):
        self.progressBar.set_completion(newProgress)

    def setDone(self):
        self.progressBar.set_completion(self.progressBar.done)
        closeButton = urwid.Button('Close', self.close)
        buttonBox = urwid.GridFlow([closeButton], 9, 1, 1, 'center')
        self.contentlist.contents.append((buttonBox, self.contentlist.options('pack')))
        self.contentlist.set_focus(len(self.contentlist.contents)-1)

    def draw(self):
        self.loop.draw_screen()

# medium level interface to pyftdi
class ModulesInterface(object):
    def __init__(self, dryRun=True):
        self.dryRun = dryRun
    
    # returns dict of mapping between all found device identifiers and sets of tuples of config name/values pairs
    def fetchDevices(self):
        pyftdi.usbtools.UsbTools.flush_cache()
        foundDevices = pyftdi.ftdi.Ftdi.list_devices("ftdi://ftdi:2232h/1")
        devices = {}
        for deviceDesc in foundDevices:
            device = pyftdi.usbtools.UsbTools.get_device(deviceDesc[0])
            eeprom = pyftdi.eeprom.FtdiEeprom()
            eeprom.open(device)
            signature = []
            for prop in sorted(list(eeprom.properties)+['product']):
                signature.append((prop,getattr(eeprom, prop)))
            devices[deviceDesc]=frozenset(signature)
            eeprom.close()
            pyftdi.usbtools.UsbTools.release_device(device)
        return devices

    # programs a device with a config out of the config enum
    def programModule(self, deviceDesc, config):
        device = pyftdi.usbtools.UsbTools.get_device(deviceDesc[0])
        eeprom = pyftdi.eeprom.FtdiEeprom()
        eeprom.open(device)
        # hack #1 load closeish eeprom image as not all properties are configrarable
        configIO = config.rawBaseline.baselineIni
        eeprom.load_config(configIO, 'raw')
        eeprom.sync()
        varStringMap ={
                'manufacturer': eeprom.set_manufacturer_name,
                'product': eeprom.set_product_name,
                'serial': eeprom.set_serial_number
                }
        toRetry = {}
        for (prop, value) in config.configSet:
            if getattr(eeprom, prop) != value:
                if prop in varStringMap:
                    varStringMap[prop](value)
                else:
                    try:
                        eeprom.set_property(prop, value)
                    except NotImplementedError:
                        toRetry[prop]= value
        # hack #2 the data doesn't get reparsed when loaded as a raw, retry failed properties at the end as something is likely to have caused it to get repared in the meantime
        eeprom.sync()
        for prop, value in toRetry.items():
            if getattr(eeprom, prop) != value:
                eeprom.set_property(prop, value)
        result = eeprom.commit(self.dryRun)
        eeprom.close()
        return result

# UI widget that displays a list of found modules and manages their selection
class ModuleListWidget(urwid.WidgetWrap):
    def __init__(self, ftdiInterface, attemptIdentUnknown):
        self.ftdiInterface = ftdiInterface
        self.attemptIdentUnknown = attemptIdentUnknown
        self.walker = urwid.SimpleListWalker([])
        self.updateModuleCheckBoxes(None)
        urwid.WidgetWrap.__init__(self, urwid.ListBox(self.walker))

    def updateModuleCheckBoxes(self, button, userData = None):
        devices = self.ftdiInterface.fetchDevices()
        buttons = []
        for device in devices:
            nameStr = str(device[0].sn)+"("+str(device[0].bus)+":"+str(device[0].address)+")"
            configType = ModuleConfigs.UNKNOWN
            for config in ModuleConfigs:
                if devices[device] == config.configSet and config.canIdentify:
                    configType = config
            checkBox = None
            for oldCheckBox in self.walker.contents:
                if oldCheckBox.device == device and oldCheckBox.config == configType:
                    checkBox = oldCheckBox
                    break
            if checkBox is None:
                if configType is not ModuleConfigs.UNKNOWN and configType.flashableDevice:
                    checkBox = ModuleCheckBox(nameStr+":"+configType.name, device, configType)
                else:
                    if self.attemptIdentUnknown and configType is ModuleConfigs.UNKNOWN:
                        # attempt partial idenfication of module
                        # find stored config with largest intersection with this module
                        identString = "partial("
                        closestModule = ModuleConfigs.UNKNOWN
                        closestInCommon = set()
                        for config in ModuleConfigs:
                            inCommon = devices[device] & config.configSet
                            if len(inCommon) > len(closestInCommon):
                                closestInCommon = inCommon
                                closestModule = config
                        identString += closestModule.name+"+{"
                        settingPairStrings = []
                        # print difference between module and closest config
                        for settingPair in (devices[device]-closestInCommon):
                            settingPairStrings.append(settingPair[0]+":"+repr(settingPair[1]))
                        identString += ','.join(settingPairStrings)
                        identString += "})"
                    else:
                        identString = configType.name
                    checkBox = ModuleTextBox(nameStr+":"+identString, device, configType)

            buttons.append(checkBox)
        self.walker[:]=buttons

    def selectAll(self, button, config=None):
        for checkBox in self.walker.contents:
            if isinstance(checkBox, urwid.CheckBox):
                if config is None or checkBox.config is config:
                    checkBox.set_state(True)

    def deSelectAll(self, button):
        for checkBox in self.walker.contents:
            if isinstance(checkBox, urwid.CheckBox):
                checkBox.set_state(False)

    def invertSelection(self, button):
        for checkBox in self.walker.contents:
            if isinstance(checkBox, urwid.CheckBox):
                checkBox.toggle_state()

    def getSelectedDevices(self, config):
        devices = []
        for checkBox in self.walker.contents:
            if isinstance(checkBox, urwid.CheckBox) and checkBox.get_state() and checkBox.config != config:
                devices.append(checkBox.device)
        return devices

# UI widget that displays the command menu
class CommandListWidget(urwid.WidgetWrap):
    def __init__(self, ftdiInterface, moduleList, loop, allowAllConfigs, dryRun):
        self.ftdiInterface = ftdiInterface
        self.moduleList = moduleList
        self.loop = loop
        self.dryRun = dryRun
        if dryRun:
            dryRunText = "Dry Run "
        else:
            dryRunText = ""
        walker = urwid.SimpleListWalker([])
        for config in ModuleConfigs:
            if config.canIdentify and config.flashableDevice:
                walker.contents.append(urwid.Button('Select all '+config.name, on_press=self.moduleList.selectAll, user_data=config))
        
        selectGroupButtons = [
                urwid.Button('Select all', on_press=self.moduleList.selectAll),
                urwid.Button('Deselect all', on_press=self.moduleList.deSelectAll),
                urwid.Button('Invert selection', on_press=self.moduleList.invertSelection),
                urwid.Divider('-'),
                ]
        walker.contents.extend(selectGroupButtons)

        for config in ModuleConfigs:
            if (config.flashableConfig or (allowAllConfigs and config.canIdentify)) and config.flashableDevice:
                walker.contents.append(urwid.Button(dryRunText+'Program as '+config.name, on_press=self.scanAndConfirmProgram, user_data=config ))

        genButtons = [
                urwid.Divider('-'),
                urwid.Button('Rescan', on_press=self.moduleList.updateModuleCheckBoxes),
                urwid.Button('Quit', on_press=self.quitApp)
            ]
        walker.contents.extend(genButtons)
        urwid.WidgetWrap.__init__(self, urwid.ListBox(walker))

    def quitApp(self, button=None):
        raise urwid.ExitMainLoop()

    def programSelected(self, loop, userData):
        (config, devices) = userData
        programmingPopup = ProgressPopUp(self.loop, self.moduleList.updateModuleCheckBoxes)
        boxTitle = ""
        if self.dryRun:
            boxTitle += "DRY RUN: NOT "
        boxTitle += "Programming {0} modules with {1}".format(len(devices),config.name)
        programmingPopup.open(boxTitle, len(devices))
        programmingPopup.draw() 
        programmingPopup.setProgress(0)
        for device in devices:
            self.ftdiInterface.programModule(device, config)
            programmingPopup.setProgress(devices.index(device)+1)
            programmingPopup.draw()
        programmingPopup.setDone()

    def scanAndConfirmProgram(self, button, config):
        devices = self.moduleList.getSelectedDevices(config)
        if len(devices)<1:
            errorPopup = MessagePopUp(self.loop, "Either no modules are selected or they are all already programmed as {0}.\nPlease select some modules and try again.".format(config.name), "None Selected?")
            errorPopup.open()
        else:
            confirmPopup = ConfirmPopUp(self.loop, "Are you sure you want to flash {0} modules with {1}?".format(len(devices), config.name), "Program Module?", self.programSelected, (config, devices))
            confirmPopup.open()


class TunerFTDIConfigUtil(object):
    def __init__(self, dryRun=True, allowAllConfigs=False, attemptIdentUnknown=False):
        colsBox = urwid.Columns([], 1)
        titlebox = urwid.AttrMap(urwid.Text('Tuner FTDI module configuration utility', align='center'), 'title')
        footerbox = urwid.AttrMap(urwid.Text(["To navigate use the keyboard or the mouse on compatible consoles"]), 'footer')

        main = urwid.Frame(colsBox, titlebox, footerbox)
        background = urwid.AttrMap(urwid.SolidFill(), 'bg')
        top = urwid.Overlay(main, background,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=20, min_height=5)

        # urwid colour pallette
        pallette = [
            ('ProgressBack', 'white', 'dark blue'),
            ('ProgressFore', 'white', 'dark red'),
            ('bg', 'black', 'dark blue'),
            ('title', 'white, bold', 'dark red'),
            ('heading', 'white, bold', 'default'),
            ('footer', 'black', 'light gray'),
            ('highlight', 'light blue', 'light gray'),
            ('reversed', 'standout', '')
        ]

        self.loop = urwid.MainLoop(top, palette=pallette)

        ftdiInterface = ModulesInterface(dryRun)
        moduleList = ModuleListWidget(ftdiInterface, attemptIdentUnknown)

        commandList = CommandListWidget(ftdiInterface, moduleList, self.loop, allowAllConfigs, dryRun)

        colsBox.contents.append((urwid.LineBox(commandList, title="Commands"), colsBox.options()))
        colsBox.contents.append((urwid.LineBox(moduleList, title="Modules"), colsBox.options()))

    def run(self):
        self.loop.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tuner FTDI module configuration utility")
    parser.add_argument("-u", "--update", action="store_true", help="Enable actual updates")
    parser.add_argument("-x", "--extra-configs", action="store_true", help="Allow flashing of all identifyable configs")
    parser.add_argument("-i", "--attempt-ident-unknown", action="store_true", help="Attempt to partially identify unknown modules")
    args = parser.parse_args()
    ftdiUI = TunerFTDIConfigUtil(not args.update, args.extra_configs, args.attempt_ident_unknown)
    ftdiUI.run()
