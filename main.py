#!/usr/bin/python3

from pathlib import Path
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from database import Data, SubtitleInfo
from subprocess import check_output
from shlex import quote


DBusGMainLoop(set_as_default=True)

objpath = "/runner"
iface = "org.kde.krunner1"

actionTable: dict[str, SubtitleInfo] = {}
class Runner(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(
            self, dbus.service.BusName("org.kde.its_mypic", dbus.SessionBus()), objpath
        )
        self.data = Data()
        self.pluginPath = Path(__file__).parent.as_posix()
        self.counter = 0
        check_output(f"chmod +x {self.pluginPath}/clipper", shell=True)

    @dbus.service.method(iface, in_signature="s", out_signature="a(sssida{sv})")
    def Match(self, query: str):
        """This method is used to get the matches and it returns a list of tupels"""
        print("Match")
        prefix = query[:2]
        if prefix != 'go':
            return []
        if query.strip() == "go":
            query = ""
        else:
            query = query.split(" ", maxsplit=1)[1]
        result = self.data.query(query)
        ret = []
        for i in result:
            ret.append(i.to_result(self.pluginPath))
            if i.fileName not in actionTable:
                actionTable[i.fileName] = i
        return ret

    @dbus.service.method(iface, out_signature="a(sss)")
    def Actions(self):
        # id, text, icon
        return [("id", "Copy text", "edit-copy")]

    @dbus.service.method(iface, in_signature="ss")
    def Run(self, data: str, action_id: str):
        print(data, action_id)
        if data not in actionTable:
            print("Not found")
            return
        cmd = f'cat {self.pluginPath}/image/{quote(actionTable[data].fileName)} | ./clipper'
        print(cmd)
        check_output(cmd, shell=True, cwd=self.pluginPath)
        actionTable[data].usedcount += 1
        self.counter += 1
        if self.counter > 5:
            self.data.save()
            self.counter = 0


runner = Runner()
Gloop = GLib.MainLoop()
Gloop.run()
