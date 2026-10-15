#!/usr/bin/env python3
"""Real GUI/helper/APT experiment; ONLY for the disposable pardus-update-lab VM.

The warning fixture installs one marker file and deliberately refuses removal.
Reinstall cleanup.deb afterwards to replace that script, then purge the fixture.
No package operations, subprocess results or package caches are mocked here.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if os.uname().nodename != "pardus-update-lab":
    raise SystemExit("Requires the isolated pardus-update-lab VM")
mode = sys.argv[1]
assert mode in ("before", "after")
root = Path.home() / "package-installer-result-lab"
output = root / mode
output.mkdir(parents=True, exist_ok=True)
fixture = root / "private/warning.deb"
sys.path.insert(0, "/usr/share/pardus/pardus-package-installer/src")
sys.argv = [sys.argv[0], str(fixture)]
from MainWindow import MainWindow
from gi.repository import Gtk, GLib, Gdk, Gio

app = Gtk.Application(application_id="tr.org.pardus.installerresultlab",
                      flags=Gio.ApplicationFlags.NON_UNIQUE)
app.register(None)
window = MainWindow(app, Gio.File.new_for_path(str(fixture)))
events = []
started = time.monotonic()
phase = "startup"
action = "install_warning"
finished = None
outcome = 0

def record(event, **data):
    row = {"event": event, "time": time.time(), **data}
    events.append(row)
    print("LAB " + json.dumps(row, ensure_ascii=False), flush=True)
    (output / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=2))

def screenshot(name):
    surface = window.window.get_window()
    pixbuf = Gdk.pixbuf_get_from_window(surface, 0, 0, surface.get_width(), surface.get_height())
    pixbuf.savev(str(output / (name + ".png")), "png", [], [])

original_exit = window.on_process_exit
def on_exit(pid, status):
    global finished
    original_exit(pid, status)
    state = subprocess.run(["dpkg-query", "-W", "-f=${db:Status-Status} ${Version}",
                            "pardus-install-result-test"], capture_output=True, text=True)
    record("finished", action=action, wait_status=status,
           page=window.progstack.get_visible_child_name(),
           message=window.doneinfolabel.get_text(),
           notification=window.notificationstate,
           version_comparison=window.status,
           installed=state.stdout.strip(), query_status=state.returncode)
    if not window.detailsrevealer.get_reveal_child():
        window.detailsbutton.emit("clicked")
    window.outputSW.get_parent().set_visible_child_name("output")
    finished = time.monotonic()
window.on_process_exit = on_exit

actions = [("install_warning", "warning.deb", "install"),
           ("failed_remove", None, "remove")]
if mode == "after":
    actions.extend([("reinstall", "cleanup.deb", "install"),
                    ("upgrade", "upgrade.deb", "install"),
                    ("downgrade", "cleanup.deb", "install"),
                    ("remove", None, "remove")])
index = 0

def tick():
    global phase, action, finished, index, outcome
    if time.monotonic() - started > 240:
        record("timeout", phase=phase, action=action)
        outcome = 1
        Gtk.main_quit()
        return False
    if phase == "startup":
        if window.mainstack.get_visible_child_name() == "package" and window.button1.get_sensitive():
            phase = "launch"
    elif phase == "launch":
        action, filename, operation = actions[index]
        if filename:
            window.from_file(str(root / "private" / filename))
        record("starting", action=action, label=window.button1.get_label())
        finished = None
        (window.button2 if operation == "remove" else window.button1).emit("clicked")
        phase = "running"
    elif phase == "running" and finished and time.monotonic() - finished > 0.5:
        screenshot(action)
        buffer = window.textview.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        (output / (action + ".log")).write_text(text)
        index += 1
        if index == len(actions):
            record("complete")
            Gtk.main_quit()
            return False
        phase = "launch"
    return True

GLib.timeout_add(100, tick)
Gtk.main()
raise SystemExit(outcome)
