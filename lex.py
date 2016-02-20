#!/usr/bin/python

"""
################################################################################
#                                                                              #
# lex: log events X                                                            #
#                                                                              #
################################################################################
#                                                                              #
# LICENCE INFORMATION                                                          #
#                                                                              #
# The program lex logs X events.                                               #
#                                                                              #
# copyright (C) 2015 William Breaden Madden                                    #
#                                                                              #
# This software is released under the terms of the GNU General Public License  #
# version 3 (GPLv3).                                                           #
#                                                                              #
# This program is free software: you can redistribute it and/or modify it      #
# under the terms of the GNU General Public License as published by the Free   #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# This program is distributed in the hope that it will be useful, but WITHOUT  #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or        #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for     #
# more details.                                                                #
#                                                                              #
# For a copy of the GNU General Public License, see                            #
# <http://www.gnu.org/licenses/>.                                              #
#                                                                              #
################################################################################

The configuration (file) should feature a Markdown list of the following form:

- event-execution-map
   - <event, e.g. shift-left>
      - description: <natural language description, e.g. say hello world>
      - command: <command, e.g. echo "hello world" | festival --tts>

Usage:
    lex.py [options]

Options:
    -h, --help               display help message
    --version                display version and exit
    -v, --verbose            verbose logging
    -s, --silent             silent
    -u, --username=USERNAME  username
"""

name    = "lex"
version = "2016-02-20T0918Z"
logo    = None

import os
import sys
import time
import ctypes
import ctypes.util
import docopt
import shijian
import propyte
import pyprel

def main(options):

    global program
    program = propyte.Program(
        options = options,
        name    = name,
        version = version,
        logo    = logo
        )
    global log
    from propyte import log

    log.info("")

    keyboard = Keyboard()
    keyboard.log_loop()

class Keyboard:

    def __init__(
        self,
        parent = None
        ):
        # X11 interface
        self.X11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
        self.display_X11 = self.X11.XOpenDisplay(None)
        # keyboard
        # Store the keyboard state, which is characterised by 32 bytes, with
        # each bit representing the state of a single key.
        self.keyboard_state = (ctypes.c_char * 32)()
        self.state_caps_lock = 0
        # Define special keys (byte, byte value).
        self.shift_keys = ((6, 4), (7, 64))
        self.modifiers = {
            "left shift":  (6,   4),
            "right shift": (7,  64),
            "left ctrl":   (4,  32),
            "right ctrl":  (13,  2),
            "left alt":    (8,   1),
            "right alt":   (13, 16)
        }
        self.last_pressed          = set()
        self.last_pressed_adjusted = set()
        self.state_ast_modifier    = {}
        # Define a dictionary of key byte numbers and key values.
        self.key_mapping = {
            1: {
                0b00000010: "<esc>",
                0b00000100: ("1", "!"),
                0b00001000: ("2", "@"),
                0b00010000: ("3", "#"),
                0b00100000: ("4", "$"),
                0b01000000: ("5", "%"),
                0b10000000: ("6", "^"),
            },
            2: {
                0b00000001: ("7", "&"),
                0b00000010: ("8", "*"),
                0b00000100: ("9", "("),
                0b00001000: ("0", ")"),
                0b00010000: ("-", "_"),
                0b00100000: ("=", "+"),
                0b01000000: "<backspace>",
                0b10000000: "<tab>",
            },
            3: {
                0b00000001: ("q", "Q"),
                0b00000010: ("w", "W"),
                0b00000100: ("e", "E"),
                0b00001000: ("r", "R"),
                0b00010000: ("t", "T"),
                0b00100000: ("y", "Y"),
                0b01000000: ("u", "U"),
                0b10000000: ("i", "I"),
            },
            4: {
                0b00000001: ("o", "O"),
                0b00000010: ("p", "P"),
                0b00000100: ("[", "{"),
                0b00001000: ("]", "}"),
                0b00010000: "<enter>",
                0b00100000: "<left ctrl>",
                0b01000000: ("a", "A"),
                0b10000000: ("s", "S"),
            },
            5: {
                0b00000001: ("d", "D"),
                0b00000010: ("f", "F"),
                0b00000100: ("g", "G"),
                0b00001000: ("h", "H"),
                0b00010000: ("j", "J"),
                0b00100000: ("k", "K"),
                0b01000000: ("l", "L"),
                0b10000000: (";", ":"),
            },
            6: {
                0b00000001: ("'", "\""),
                0b00000010: ("`", "~"),
                0b00000100: "<left shift>",
                0b00001000: ("\\", "|"),
                0b00010000: ("z", "Z"),
                0b00100000: ("x", "X"),
                0b01000000: ("c", "C"),
                0b10000000: ("v", "V"),
            },
            7: {
                0b00000001: ("b", "B"),
                0b00000010: ("n", "N"),
                0b00000100: ("m", "M"),
                0b00001000: (",", "<"),
                0b00010000: (".", ">"),
                0b00100000: ("/", "?"),
                0b01000000: "<right shift>",
            },
            8: {
                0b00000001: "<left alt>",
                0b00000010: "<space>",
                0b00000100: "<caps lock>",
            },
            9: {
                0b00000001: ("F6", "shift-F6"),
                0b00000010: ("F7", "shift-F7"),
                0b00000100: ("F8", "shift-F8"),
                0b00001000: ("F9", "shift-F9"),
            },
            13: {
                0b00000010: "<right ctrl>",
                0b00010000: "<right alt>",
                0b10000000: ("<up>", "shift-up")
            },
            14: {
                0b00000001: ("<pageup>",   "shift-pageup"),
                0b00000010: ("<left>",     "shift-left"),
                0b00000100: ("<right>",    "shift-right"),
                0b00001000: ("<end>",      "shift-end"),
                0b00010000: ("<down>",     "shift-down"),
                0b00100000: ("<pagedown>", "shift-PgDn"),
                0b01000000: ("<insert>",   "shift-insert")
            },
        }

    def access_keys(self):
        # Access raw keypresses.
        # The function XQueryKeymap returns a bit vector for the logical state
        # of the keyboard for each bit set to 1 indicates that the corresponding
        # key is pressed down currently. The vector is represented by 32 bytes.
        self.X11.XQueryKeymap(self.display_X11, self.keyboard_state)
        raw_leypresses = self.keyboard_state
        # Check the states of key modifiers (Ctrl, Alt, Shift).
        state_modifier = {}
        for modifier, (i, byte) in self.modifiers.iteritems():
            state_modifier[modifier] = bool(ord(raw_leypresses[i]) & byte)
        # Detect Shift.
        shift = 0
        for i, byte in self.shift_keys:
            if ord(raw_leypresses[i]) & byte:
                shift = 1
                break
        # Detect Caps Lock.
        if ord(raw_leypresses[8]) & 4:
            self.state_caps_lock = int(not self.state_caps_lock)
        # Aggregate pressed keys.
        pressed_keys = []
        for i, k in enumerate(raw_leypresses):
            o = ord(k)
            if o:
                time.sleep(0.1)
                #log.info("\ndetected keystroke code: {i}, {o}".format(
                #    i = i,
                #    o = o
                #))
                for byte, key in self.key_mapping.get(i, {}).iteritems():
                    if byte & o:
                        if isinstance(key, tuple):
                            key = key[shift or self.state_caps_lock]
                        pressed_keys.append(key)
        tmp = pressed_keys
        pressed_keys = list(set(pressed_keys).difference(self.last_pressed))
        state_changed = tmp != self.last_pressed and (pressed_keys or self.last_pressed_adjusted)
        self.last_pressed = tmp
        self.last_pressed_adjusted = pressed_keys
        if pressed_keys:
            pressed_keys = pressed_keys[0]
        else:
            pressed_keys = None
        state_changed = self.state_ast_modifier and (state_changed or state_modifier != self.state_ast_modifier)
        self.state_ast_modifier = state_modifier
        # state_changed: Boolean
        # state_modifier: dictionary of status of available modifiers, e.g.:
        # {
        #     'left shift':  True,
        #     'right alt':   False,
        #     'right shift': False,
        #     'left alt':    False,
        #     'left ctrl':   False,
        #     'right ctrl':  False
        # }
        # pressed_keys: string of key detected, e.g. e.
        return (state_changed, state_modifier, pressed_keys)

    def log_loop(self):

        log_filename = "/home/{username}/.lexlog.txt".format(
            username = program.username
        )
        
        while True:
            time.sleep(0.005)
            state_changed, state_modifier, pressed_keys = self.access_keys()
            if state_changed and pressed_keys is not None:
                #log.info("detected keystroke: {key}".format(
                #    key = pressed_keys
                #))
                #print(pressed_keys, end = "")
                print pressed_keys,
                with open(log_filename, "a") as logFile:
                    logFile.write(pressed_keys)



if __name__ == "__main__":
    options = docopt.docopt(__doc__)
    if options["--version"]:
        print(version)
        exit()
    main(options)
