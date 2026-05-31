#!/usr/bin/env python3
# JS8Spotter v3.0.8 (053126). Visit https://kf7mix.com/js8spotter.html for information
# Special thanks to KE0DHO, KF0HHR, N0GES, N6CYB, KQ4DRG, NK8O, N0YJ, KI6ESH, N4FWD, KQ4HQD, KE0VCD, KN4AM, and everyone else who has contributed (see changelogs for more info)
#
# MIT License, Copyright 2026 Joseph D Lyman KF7MIX -- Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software. The Software IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Modifications Copyright 2026 Andy van Tol WM8Q -- MIT License

import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkinter.ttk import Treeview, Style, Combobox
from tkinter.messagebox import askyesno
from PIL import ImageTk, Image
from threading import Event, Thread
from io import StringIO
import time
import datetime
import random
import socket
import select
import json
import sqlite3
import re
import os
import requests

## Attempt to load an optional sound module (first tkSnack, then simpleaudio) 0=tksnack, 1=none, 2=simpleaudio
nosound = 0
try:
    import tkSnack # For Linux SRC users
except ImportError:
    nosound = 2
    try:
        import simpleaudio as sa # For Windows build users
    except ImportError:
        nosound = 1

### Globals
swname = "JS8Spotter"
fromtext = "de KF7MIX"
displayversion = "3.0.8" # User-facing release version (window title, About, error messages)
swversion = "1.19"       # Internal DB-compatibility version (only used by the DB version check)
dbminver = "1.17"        # Oldest DB version still accepted without warning (matches upstream v1.19)

dbfile = 'js8spotter.db'
conn = sqlite3.connect(dbfile)
c = conn.cursor()

atx_limit = 12
current_profile_id = 0
search_strings = []
bgsearch_strings = {}
expects = []
auto_txes = []
last_auto_tx=0
forms = {}
forms_focus = {}
totals = {}
reported_speed = 0
speedmod_timeout = 0
speedmod_oldspeed = 0

speeds = {"0":"Normal", "1":"Fast", "2":"JS8 40", "4":"Slow", "8":"JS8 60", "16":"Subspace"}
wfbandshz = ["3578000","7078000","10130000","14078000","18104000","21078000","24922000","28078000"]

## Available WAV notification files in program folder
wavs_unsorted={}
for wavfile in os.scandir('./'):
    if wavfile.path.endswith('wav'):
        wavname=os.path.basename(wavfile)
        wavs_unsorted[wavname]=wavname
wavs=[]
wavs.append("None")
for wav in sorted(wavs_unsorted.keys()):
    wavs.append(wav)

## Grid translations For maps, 0=North America, 1=Europe, 2=Australia, 3=Indonesia
## More grid translations may be added below if additional maps images are added
map_loc = 0
map_zoom = 0
maplocs = ["North America", "Europe", "Australia", "Indonesia", "Northern Africa", "Southern Africa"]
gridmultiplier = [
    {
        "CO":[0,3], "DO":[1,3], "EO":[2,3], "FO":[3,3],
        "CN":[0,2], "DN":[1,2], "EN":[2,2], "FN":[3,2],
        "CM":[0,1], "DM":[1,1], "EM":[2,1], "FM":[3,1],
        "CL":[0,0], "DL":[1,0], "EL":[2,0], "FL":[3,0],
    },
    {
        "IP":[0,3], "JP":[1,3], "KP":[2,3], "LP":[3,3],
        "IO":[0,2], "JO":[1,2], "KO":[2,2], "LO":[3,2],
        "IN":[0,1], "JN":[1,1], "KN":[2,1], "LN":[3,1],
        "IM":[0,0], "JM":[1,0], "KM":[2,0], "LM":[3,0],
    },
    {
        "OH":[0,3], "PH":[1,3], "QH":[2,3], "RH":[3,3],
        "OG":[0,2], "PG":[1,2], "QG":[2,2], "RG":[3,2],
        "OF":[0,1], "PF":[1,1], "QF":[2,1], "RF":[3,1],
        "OE":[0,0], "PE":[1,0], "QE":[2,0], "RE":[3,0],
    },
    {
        "OL":[0,3], "PL":[1,3], "QL":[2,3], "RL":[3,3],
        "OK":[0,2], "PK":[1,2], "QK":[2,2], "RK":[3,2],
        "OJ":[0,1], "PJ":[1,1], "QJ":[2,1], "RJ":[3,1],
        "OI":[0,0], "PI":[1,0], "QI":[2,0], "RI":[3,0],
    },
    {
        "IM":[0,3], "JM":[1,3], "KM":[2,3], "LM":[3,3],
        "IL":[0,2], "JL":[1,2], "KL":[2,2], "LL":[3,2],
        "IK":[0,1], "JK":[1,1], "KK":[2,1], "LK":[3,1],
        "IJ":[0,0], "JJ":[1,0], "KJ":[2,0], "LJ":[3,0],
    },
    {
        "II":[0,3], "JI":[1,3], "KI":[2,3], "LI":[3,3],
        "IH":[0,2], "JH":[1,2], "KH":[2,2], "LH":[3,2],
        "IG":[0,1], "JG":[1,1], "KG":[2,1], "LG":[3,1],
        "IF":[0,0], "JF":[1,0], "KF":[2,0], "LF":[3,0],
    },
]

# Map marker palette
palfile = open("maps/maps.pal", "r")
mappal = palfile.read().split("\n")
palfile.close()

### Database work
## Clean-up tables

# signal table only needs data for 24hrs, remove older entries
c.execute("DELETE FROM signal WHERE sig_timestamp < DATETIME('now', '-24 hour')")
conn.commit()

# sqlite VACUUM defragment database
c.execute("VACUUM")
conn.commit()

## Settings table
c.execute("SELECT * FROM setting")
dbsettings = c.fetchall()

## Rebuild database settings if any are missing (this INSERT won't overwrite existing values but will add missing ones)
if len(dbsettings)<28:
    svals = "('udp_ip','127.0.0.1'),"
    svals+= "('udp_port','2242'),"
    svals+= "('tcp_ip','127.0.0.1'),"
    svals+= "('tcp_port','2442'),"
    svals+= "('hide_heartbeat','0'),"
    svals+= "('dark_theme','0'),"
    svals+= "('marker_index','0'),"
    svals+= "('marker_hlmode','0'),"
    svals+= "('wfband_index','0'),"
    svals+= "('wftime_index','0'),"
    svals+= "('callsign','FILL'),"
    svals+= "('grid','FILL'),"
    svals+= "('hide_spot','0'),"
    svals+= "('forms_gateway',''),"
    svals+= "('forms_focus','F!103,F!104,F!304'),"
    svals+= "('hide_activity','0'),"
    svals+= "('hide_directed','0'),"
    svals+= "('pause_expect','0'),"
    svals+= "('pause_autotx','0'),"
    svals+= "('expect_blocklist',''),"
    svals+= "('expect_lastsentto',''),"
    svals+= "('highlight_new','0'),"
    svals+= "('disable_sounds','0'),"
    svals+= "('dbver','0'),"
    svals+= "('statrepgrp',''),"
    svals+= "('exp_def_allow','*'),"
    svals+= "('view_mode','Last 100'),"
    svals+= "('win_geometry','')"
    c.execute("INSERT INTO setting(name,value) VALUES "+svals)
    conn.commit()
    c.execute("SELECT * FROM setting")
    dbsettings.clear()
    dbsettings = c.fetchall()

## Setup settings dictionary
settings = {}
for setting in dbsettings:
    settings[setting[1]]=setting[2]

## Notifications table(s)
# (profile trigger sound = type 1)
c.execute("SELECT * FROM notify WHERE type = '1'")
dbnotify = c.fetchall()
notifyProfile = {}
for nfy in dbnotify:
    notifyProfile[nfy[2]]=nfy[3]

## Setup statusbar totals tracking
totals[0]=0 # for grid, not currently reported in statusbar
totals[1]=0 # for expect
totals[2]=0 # for forms
totals[3]=0 # for statreps
totals[4]=0 # for autotx

## For inter-thread comms
event = Event()
speedmod = Event()
js8close = Event()

### Thread for processing output of JS8Call over socket
class TCP_RX(Thread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.keep_running = True

    def stop(self):
        self.keep_running = False

    def get_tx_time(self, speed, words):
        if speed==0: wpm,frame=16,15
        if speed==1: wpm,frame=24,10
        if speed==2: wpm,frame=40,6
        if speed==4: wpm,frame=8,30
        if speed==8: wpm,frame=60,4
        if speed==16: wpm,frame=60,4 # "subspace" mode

        tts = (words/wpm)*60
        if tts<frame: tts=frame
        tts+=(frame*2)
        # returning approx number of seconds to send, plus two frames (one to account for start, one for after) in seconds
        return tts

    def run(self):
        global reported_speed, speedmod_timeout, speedmod_oldspeed
        conn1 = sqlite3.connect(dbfile) # we need our own db connection in this thread
        c1 = conn1.cursor()

        track_types = {"RX.ACTIVITY", "RX.DIRECTED", "RX.SPOT"} # we're only tracking certain API activity types

        while self.keep_running:
            rfds, _wfds, _xfds = select.select([self.sock], [], [], 0.5) # check every 0.5 seconds
            if self.sock in rfds:
                try:
                    iodata = self.sock.recv(4096)

                    try:
                        json_lines = StringIO(str(iodata,'UTF-8'))
                    except:
                        print("JSON error")
                        json_lines = ""

                    for data in json_lines:
                        try:
                            data_json = json.loads(data)
                        except ValueError as error:
                            data_json = {'type':'error'}

                        # For API json print to console debug (uncomment next two lines)
                        #printable_json_output = json.dumps(data_json, indent=4)
                        #print(printable_json_output)

                        if data_json['type']=="MODE.SPEED":
                            # print("REPORTED MODE.SPEED:"+str(data_json))
                            # API _SPEED setting from expect, 0=normal, 1=fast, 2=JS8 40, 4=slow, 8=JS8 60, 16=Subspace
                            reported_speed = data_json['params']['SPEED']

                        if data_json['type']=="STATION.CLOSING":
                            closing_reason = data_json['params']['REASON']; # not sure we'll ever use this value, but who knows
                            js8close.set()

                        if data_json['type'] in track_types:
                            # gather basic elements of this record
                            msg_call = data_json['params']['FROM'] if "FROM" in data_json['params'] else ""
                            msg_dial = data_json['params']['DIAL'] if "DIAL" in data_json['params'] else ""
                            msg_freq = data_json['params']['FREQ'] if "FREQ" in data_json['params'] else ""
                            msg_offset = data_json['params']['OFFSET'] if "OFFSET" in data_json['params'] else ""
                            msg_speed = data_json['params']['SPEED'] if "SPEED" in data_json['params'] else "" # 0=Normal, 1=Fast, 2=JS8 40, 4=Slow, 8=JS8 60, 16=Subspace
                            msg_snr = data_json['params']['SNR'] if "SNR" in data_json['params'] else ""
                            msg_value = data_json['value']

                            # before scans, save grid info (from CQ, spot, hb, msg) and signal info for wf visual
                            msg_grid = data_json['params']['GRID'].strip() if "GRID" in data_json['params'] else ""
                            if msg_grid != "":
                                gridsql = "INSERT INTO grid(grid_callsign,grid_grid,grid_dial,grid_type,grid_snr,grid_timestamp) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP)"
                                c1.execute(gridsql, [msg_call, msg_grid, msg_dial, data_json['type'], msg_snr])
                                conn1.commit()
                                event.set()

                            if msg_call!="" and msg_offset!="" and msg_speed!="" and msg_freq!="":
                                sigsql = "INSERT INTO signal(sig_callsign,sig_dial,sig_freq,sig_offset,sig_speed,sig_snr,sig_timestamp) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP)"
                                c1.execute(sigsql, [msg_call, msg_dial, msg_freq, msg_offset,msg_speed, msg_snr])
                                conn1.commit()
                                event.set()

                            ## Multiple Choice Forms (MCF) subsystem. Check for prefix "F!<form code> <form response> <msg> <datecode>" in any incoming data
                            # add \/?\-?[A-Z0-9]? to callsign detection, for /P and other tactical calls
                            # also captures forms stored as messages on 3rd party systems
# API output for an MCform (msg) 5/27/26
#{"params":{"CMD":" MSG","DIAL":7078000,"EXTRA":"","FREQ":7079851,"FROM":"K1YE","GRID":"","OFFSET":1851,"SNR":-18,"SPEED":0,"TDRIFT":0.18000000715255737,"TEXT":"KF7MIX MSG F!101 50333A286  #E0LE ♢ ","TO":"KF7MIX","UTC":1779894536796,"_ID":-1},"type":"RX.DIRECTED","value":"KF7MIX MSG F!101 50333A286  #E0LE ♢ "}


                            # to test manually set msg_value="AB1CD: KF7MIX  F!101 46333B251  #JUQM"

                            # older versions of the program sent the FROM in the value, newer ones do not
                            # scan_forms = re.search(r"([A-Z0-9]+)\/?\-?[A-Z0-9]?:\s+?(@?[A-Z0-9]+)\/?\-?[A-Z0-9]?\s+?(.*\s+)?(F\![A-Z0-9]+)\s+?([A-Z0-9]+)\s+?(.*?)(\#[A-Z0-9]+)(\ FROM)?(\ [A-Z0-9]+)?",msg_value) # from, to, <optional E? or MSG etc. group not used>, form ID, form responses, msg, timestamp
                            scan_forms = re.search(r"(@?[A-Z0-9]+)\/?\-?[A-Z0-9]?\s+?(.*\s+)?(F\![A-Z0-9]+)\s+?([A-Z0-9]+)\s+?(.*?)(\#[A-Z0-9]+)(\ FROM)?(\ [A-Z0-9]+)?",msg_value) # to, <optional E? or MSG etc. group not used>, form ID, form responses, msg, timestamp

                            if scan_forms:
                                # determine from/to for standard or stored forms
                                if scan_forms[7]==" FROM":
                                    form_from = scan_forms[8].strip()
                                    form_to = scan_forms[1]
                                else:
                                    #form_from = scan_forms[1] # deprecated, no longer in API "values"
                                    form_from = msg_call
                                    form_to = scan_forms[1]

                                # forward to gateway if user has one configured
                                rstat=""
                                if settings['forms_gateway']!='':
                                    formobj = {'fromcall':form_from, 'tocall':form_to, 'typeid':scan_forms[3], 'responses':scan_forms[4], 'msgtxt':scan_forms[5], 'timesig':scan_forms[6]}
                                    try:
                                        rstat = requests.post(settings['forms_gateway'], data = formobj)
                                    except requests.exceptions.RequestException as e:
                                        rstat = ""

                                # found a form in the stream, save it. No need for it to be directed to us, we want to save all forms we find.
                                sql = "INSERT INTO forms(fromcall,tocall,typeid,responses,msgtxt,timesig,lm,gwtx) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP,?)"
                                c1.execute(sql, [form_from,form_to,scan_forms[3],scan_forms[4],scan_forms[5],scan_forms[6],str(rstat)])
                                conn1.commit()
                                event.set()

                            # removed FROM in values
                            scan_formsrelay = re.search(r"(@?[A-Z0-9>]+)\/?\-?[A-Z0-9]?\s+?(.*\s+)?(F\![A-Z0-9]+)\s+?([A-Z0-9]+)\s+?(.*?)(\#[A-Z0-9]+)\s+?\*DE\*\s+?([A-Z0-9]+)\/?\-?[A-Z0-9]?",msg_value)
                            if scan_formsrelay:
                                # forward to gateway if user has one configured
                                rstat=""
                                if settings['forms_gateway']!='':
                                    formobj = {'fromcall':scan_formsrelay[7], 'tocall':scan_formsrelay[1], 'typeid':scan_formsrelay[3], 'responses':scan_formsrelay[4], 'msgtxt':scan_formsrelay[5], 'timesig':scan_formsrelay[6]}
                                    try:
                                        rstat = requests.post(settings['forms_gateway'], data = formobj)
                                    except requests.exceptions.RequestException as e:
                                        rstat = ""

                                # found a relayed form, save it. Doesn't matter who it is to/from, we want to save all forms we find.
                                sql = "INSERT INTO forms(fromcall,tocall,typeid,responses,msgtxt,timesig,lm,gwtx) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP,?)"
                                c1.execute(sql, [scan_formsrelay[7],scan_formsrelay[1],scan_formsrelay[3],scan_formsrelay[4],scan_formsrelay[5],scan_formsrelay[6],str(rstat)])
                                conn1.commit()
                                event.set()

                            ## Expect subsystem. Check for expect prefix "<from>: <to> E? <expect>" and process. Relayed form "<relay>: <to>> E? <expect> *DE* <from>"
                            reply_to = ""
                            ex_reply = ""
                            ex_expect = ""
                            ex_relay = ""

                            # scan for direct request expect
                            # to test manually set msg_value="AB1CD: KF7MIX  E? TEST"

                            # removed FROM in values
                            # scan_expect = re.search(r"([A-Z0-9]+)\/?\-?[A-Z0-9]?:\s+?(@?[A-Z0-9]+)\/?\-?[A-Z0-9]?\s+?E\?\s+?([A-Z0-9!]+)",msg_value) # from, to, expect
                            scan_expect = re.search(r"(@?[A-Z0-9]+)\/?\-?[A-Z0-9]?\s+?E\?\s+?([A-Z0-9!]+)",msg_value) # to, expect
                            if scan_expect:
                                # ex_from = scan_expect.group(1)
                                ex_from = msg_call
                                ex_to = scan_expect.group(1)
                                ex_expect = scan_expect.group(2)
                            else:
                                # scan for relayed request expect
                                # removed FROM in values
                                scan_expect = re.search(r"([A-Z0-9]+)\/?\-?[A-Z0-9]?\>?\s+?E\?\s+?([A-Z0-9!]+)\s+?\*DE\*?\s+?([A-Z0-9]+)\/?\-?[A-Z0-9]?",msg_value) # to, expect, from
                                if scan_expect:
#                                    ex_relay = scan_expect.group(1)
                                    ex_relay = msg_call
                                    ex_to = scan_expect.group(1)
                                    ex_expect = scan_expect.group(2)
                                    ex_from = scan_expect.group(3)

                            if ex_expect and settings['callsign']!="FILL" and settings['pause_expect']=="0":
                                # check if expect is in database
                                c1.execute("SELECT * FROM expect WHERE expect = ?", [ex_expect])
                                ex_exists = c1.fetchone()
                                if ex_exists:
                                    # found expect command. Check if requestor is in allowed list, or * for any station
                                    for allow in ex_exists[2].split(","):
                                        allow = allow.replace(" ", "")
                                        if allow[0]=="@":
                                            if ex_to == allow: reply_to = ex_from
                                        else:
                                            if ex_from==allow and ex_to==settings['callsign']: reply_to = ex_from
                                    for allowall in ex_exists[2].split(","):
                                        if allowall=="*" and ex_to==settings['callsign'] and reply_to=="": reply_to = ex_from

                                    # make sure requester isn't in the expect blocklist
                                    for blockcall in settings['expect_blocklist'].split(","):
                                        if ex_from == blockcall: reply_to = ""

                                    if reply_to:
                                        # make sure that txmax hasn't been exceeded (99=inf)
                                        reply_count=len(ex_exists[3].split(","))-1
                                        if reply_count<int(ex_exists[4]) or int(ex_exists[4])==99:
                                            # formulate reply, relay or regular
                                            if ex_relay:
                                                ex_reply = settings['callsign']+": "+ex_relay+"> "+reply_to+" "+ex_exists[1]
                                                time.sleep(120) # ugly last-ditch workaround relay ACK delays
                                            else:
                                                ex_reply = settings['callsign']+": "+reply_to+" "+ex_exists[1]

                                            # API _SPEED setting from expect, store old setting, and set new JS8Call TX speed/mode with API call
                                            # MODE.GET_SPEED / MODE.SET_SPEED, 0=normal, 1=fast, 2=JS8 40, 4=slow, 8=JS8 60, 16=Subspace
                                            # "Current" / None means leave JS8Call's current speed alone (don't send SET_SPEED)
                                            if ex_exists[6] not in (None, "Current"):
                                                old_speed = reported_speed
                                                new_speed = 0
                                                if ex_exists[6]=="Normal": new_speed=0
                                                if ex_exists[6]=="Fast":   new_speed=1
                                                if ex_exists[6]=="JS8 40":  new_speed=2
                                                if ex_exists[6]=="Slow":   new_speed=4

                                                if ex_exists[6]=="JS8 60":   new_speed=8
                                                if ex_exists[6]=="Subspace":   new_speed=16


                                                tx_content = json.dumps({"params":{"SPEED":new_speed},"type":"MODE.SET_SPEED"})
                                                self.sock.send(bytes(tx_content + '\n','utf-8'))
                                                time.sleep(0.25)

                                                # as of v2.4.0, we must estimate when to set the speed back
                                                sent_words = len(ex_reply.split())
                                                speedmod_timeout = int(self.get_tx_time(new_speed,sent_words))
                                                speedmod_oldspeed = old_speed
                                                speedmod.set()

                                            # make sure the message pane is empty
                                            tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
                                            self.sock.send(bytes(tx_content + '\n','utf-8'))
                                            time.sleep(0.33)

                                            # send to JS8Call API
                                            tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":ex_reply})
                                            self.sock.send(bytes(tx_content + '\n','utf-8'))
                                            time.sleep(0.25)

#                                            if ex_exists[6]!=None:
#                                                tx_content = json.dumps({"params":{"SPEED":old_speed},"type":"MODE.SET_SPEED"})
#                                                self.sock.send(bytes(tx_content + '\n','utf-8'))
#                                                time.sleep(0.25)

                                            # append database txlist
                                            if ex_exists[3] == "":
                                                sql = "UPDATE expect SET txlist = '"+reply_to+",' WHERE expect = ?"
                                            else:
                                                sql = "UPDATE expect SET txlist = txlist || '"+reply_to+" "+datetime.datetime.now().strftime("%x %X")+",' WHERE expect = ?"
                                            c1.execute(sql,[ex_expect])
                                            conn1.commit()
                                            event.set()

                            ## CommStat Statreps: if the user has a CommStat group set, we'll capture statreps we see on the air
                            ## Based on specs from v1.0.5 (but using no code), see: https://github.com/W5DMH/commstatone
                            if settings['statrepgrp']!="":
                                # capture direct statrep

                                # FROM no longer in "values" in API
                                # scan_statrep = re.search(r"([A-Z0-9]+)\/?\-?[A-Z0-9]?:\s+?(.*?),(.*?)\,(.*?)\,(.*?)\,(.*?)\,(.*?)\,\{\&\%\}",msg_value) # example: KF7MIX: @AMRRON  ,EM48,1,501,111111111111,Test,{&%}
                                scan_statrep = re.search(r"(.*?),(.*?)\,(.*?)\,(.*?)\,(.*?)\,(.*?)\,\{\&\%\}",msg_value) # example: KF7MIX: @AMRRON  ,EM48,1,501,111111111111,Test,{&%}

                                if scan_statrep:
                                    if (scan_statrep[1].strip() == settings['statrepgrp']) or (settings['statrepgrp']=="*"):
                                        sql = "INSERT INTO csstatrep(cssr_from,cssr_group,cssr_grid,cssr_prio,cssr_msgid,cssr_status,cssr_notes,cssr_timestamp) VALUES (?,?,?,?,?,?,?, CURRENT_TIMESTAMP)"
                                        c1.execute(sql, [msg_call,scan_statrep[1].strip(),scan_statrep[2],scan_statrep[3],scan_statrep[4],scan_statrep[5],scan_statrep[6]])
                                        conn1.commit()
                                        event.set()

                                # capture forwarded statrep
                                # FROM no longer in "values" in API
                                # scan_statrepfw = re.search(r"([A-Z0-9]+)\/?\-?[A-Z0-9]?:\s+?(.*?),(.*?)\,(.*?)\,(.*?)\,(.*?)\,(.*?)\,(.*?)\,\{F\%\}",msg_value) # example: AB1CD: @TST11  ,EM48,1,959,111111111111,NTR,KF7MIX,{F%}
                                scan_statrepfw = re.search(r"(.*?),(.*?)\,(.*?)\,(.*?)\,(.*?)\,(.*?)\,(.*?)\,\{F\%\}",msg_value) # example: AB1CD: @TST11  ,EM48,1,959,111111111111,NTR,KF7MIX,{F%}
                                if scan_statrepfw:
                                    if (scan_statrepfw[1].strip() == settings['statrepgrp']) or (settings['statrepgrp']=="*"):
                                        sql = "INSERT INTO csstatrep(cssr_from,cssr_group,cssr_grid,cssr_prio,cssr_msgid,cssr_status,cssr_notes,cssr_timestamp) VALUES (?,?,?,?,?,?,?, CURRENT_TIMESTAMP)"
                                        c1.execute(sql, [scan_statrepfw[7],scan_statrepfw[1].strip(),scan_statrepfw[2],scan_statrepfw[3],scan_statrepfw[4],scan_statrepfw[5],scan_statrepfw[6]])
                                        conn1.commit()
                                        event.set()

                            ## Scan for search terms
                            # if search term is in 'value' or 'call' then insert into db. Check visible profile terms, make copy in case other thread modifies dict
                            searchcheck = search_strings.copy()

                            for term in searchcheck:
                                if (term in msg_call) or (term in data_json['value']):
                                    sql = "UPDATE search SET last_seen = CURRENT_TIMESTAMP WHERE profile_id = ? AND keyword = ?"
                                    c1.execute(sql, [current_profile_id,term])
                                    sql = "INSERT INTO activity(profile_id,type,value,dial,snr,call,spotdate,freq,offset,speed) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP,?,?,?)"
                                    c1.execute(sql, [current_profile_id,data_json['type'],data_json['value'],msg_dial,msg_snr,msg_call,msg_freq,msg_offset,msg_speed])
                                    conn1.commit()
                                    event.set()

                            # check background scan profile terms. Make copy in case other thread modifies dict
                            bgcheck = bgsearch_strings.copy();
                            for term in bgcheck.keys():
                                term_profile = bgcheck.get(term)
                                if term_profile == current_profile_id:
                                    continue
                                if (term in msg_call) or (term in data_json['value']):
                                    sql = "UPDATE search SET last_seen = CURRENT_TIMESTAMP WHERE profile_id = ? AND keyword = ?"
                                    c1.execute(sql, [term_profile,term])
                                    sql = "INSERT INTO activity(profile_id,type,value,dial,snr,call,spotdate,freq,offset,speed) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP,?,?,?)"
                                    c1.execute(sql, [term_profile,data_json['type'],data_json['value'],msg_dial,msg_snr,msg_call,msg_freq,msg_offset,msg_speed])
                                    conn1.commit()
                                    event.set()

                except socket.error as err:
                    print("TCP error at receiving socket {}".format(err))
                    break

### Main program thread
class App(tk.Tk):
    def __init__(self, sock):
        #super().__init__()
        super().__init__(baseName="JS8Spotter", className="JS8Spotter")
        self.sock = sock
        self.sender = None
        self.receiver = None
        self.protocol("WM_DELETE_WINDOW", self.menu_bye)

        self.style = Style()
        self.call("source", "azure.tcl")
        self.create_gui()

        if not settings.get('win_geometry'):
            self.eval('tk::PlaceWindow . center')

        self.activate_theme()

        self.build_profilemenu()
        self.build_formsmenu()
        self.refresh_keyword_tree()
        self.refresh_activity_tree()
        self.update_statusbar()

        self.start_receiving()
        self.poll_activity()
        self.update()

        self.get_expects()

        # Universal cut/copy/paste right-click for all ttk.Entry widgets
        self.bind_class("TEntry", "<Button-3>", self.rcmenu_ccp)

        ## Manage startup errors & reports
        # check db version against program version
        dbver = next((item for item in dbsettings if 'dbver' in item),None)
        if dbver is None:
            dbversion = "older than "+swversion
        else:
            dbversion = str(dbver[2])

        if dbversion != swversion and dbversion != dbminver:
            messagebox.showinfo("Database Compatibility","Your database (version "+dbversion+") is not compatible with JS8Spotter-Subspace v"+displayversion+", which expects database version "+swversion+" (or "+dbminver+"). Please run the database tool to upgrade your database.")

        # check if sound module was loaded
        if nosound == 1:
            messagebox.showinfo("Sound Error","Audio not loaded. The application WILL function normally without audio. Linux users may install the TkSnack library.")
        else:
            if nosound == 0:
                tkSnack.initializeSnack(self)

        # report if TCP connect failed
        if self.sock == None:
            messagebox.showinfo("TCP Error","Can't connect to JS8Call. Make sure it is running, and check your TCP settings before restarting JS8Spotter.")

        if settings['callsign'] == "FILL" or settings['grid'] == "FILL":
            messagebox.showinfo("Settings Incomplete","Please specify your callsign and grid in the settings before using the application.")

        if settings['pause_expect'] == "1":
            messagebox.showinfo("Expect Replies Paused","Expect system replies are currently PAUSED, and no replies will be transmitted. To unpause, use the Tools menu.")

        if settings['pause_autotx'] == "1":
            messagebox.showinfo("Expect Auto TX Paused","Auto TX entires in Expect are currently PAUSED, and none will be transmitted. To unpause, use the Tools menu.")

    ## Setup main gui window
    def create_gui(self):
        self.title(swname+" "+fromtext+" (v"+displayversion+")")

        try:
            self._spot_icon = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "js8spotter.ico")))
            self.iconphoto(True, self._spot_icon)
        except Exception:
            try:
                self.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "js8spotter.ico"))
            except Exception:
                pass

        self.geometry(settings.get('win_geometry') or '950x450')
        self.minsize(950,450)
        self.resizable(width=True, height=True)

        self.columnconfigure(0, weight=12)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=12)
        self.columnconfigure(3, weight=1)

        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)
        self.rowconfigure(2,weight=24)
        self.rowconfigure(3,weight=1)
        self.rowconfigure(4,weight=1)

        # menus
        self.menubar = Menu(self)
        self.filemenu = Menu(self.menubar, tearoff = 0)
        self.profilemenu = Menu(self.menubar, tearoff = 0)
        self.highlightmenu = Menu(self.menubar, tearoff = 0)

        self.formsmenu = Menu(self.menubar, tearoff = 0)
        self.mcf100 = Menu(self.menubar, tearoff = 0)
        self.mcf300 = Menu(self.menubar, tearoff = 0)
        self.mcf500 = Menu(self.menubar, tearoff = 0)
        self.mcf700 = Menu(self.menubar, tearoff = 0)
        self.mcfother = Menu(self.menubar, tearoff = 0)

        self.filemenu.add_cascade(label = 'Switch Profile', menu = self.profilemenu)
        self.filemenu.add_separator()
        self.filemenu.add_command(label = 'New Profile', command = lambda: self.profile_edit("new"))
        self.filemenu.add_command(label = 'Edit Profile', command = lambda: self.profile_edit("edit"))
        self.filemenu.add_command(label = 'Remove Profile', command = self.menu_remove)
        self.filemenu.add_command(label = 'Sort Profiles', command = self.profile_sort)
        self.filemenu.add_separator()
        self.filemenu.add_command(label = 'Settings', command = self.settings_edit)
        self.filemenu.add_separator()
        self.filemenu.add_command(label = 'Exit', command = self.menu_bye)

        self.viewmenu = Menu(self.menubar, tearoff = 0)
        self.viewmenu.add_command(label = "Hide Heartbeats", command = self.toggle_view_hb)
        self.viewmenu.add_command(label = "Hide RX.SPOT", command = self.toggle_view_spot)
        self.viewmenu.add_command(label = "Hide RX.ACTIVITY", command = self.toggle_view_activity)
        self.viewmenu.add_command(label = "Hide RX.DIRECTED", command = self.toggle_view_directed)
        self.viewmenu.add_separator()
        self.viewmenu.add_command(label = "Dark Theme", command = self.toggle_theme)
        self.viewmenu.add_separator()
        self.viewmenu.add_cascade(label = 'Highlight Range', menu = self.highlightmenu)

        self.highlightmenu.add_command(label = "None", command = lambda: self.highlight_new("0"))
        self.highlightmenu.add_command(label = "Last 15 Minutes", command = lambda: self.highlight_new("15"))
        self.highlightmenu.add_command(label = "Last 30 Minutes", command = lambda: self.highlight_new("30"))
        self.highlightmenu.add_command(label = "Last 45 Minutes", command = lambda: self.highlight_new("45"))
        self.highlightmenu.add_command(label = "Last 1 Hour", command = lambda: self.highlight_new("60"))
        self.highlightmenu.add_command(label = "Last 2 Hours", command = lambda: self.highlight_new("120"))
        self.highlightmenu.add_command(label = "Last 4 Hours", command = lambda: self.highlight_new("240"))
        self.highlightmenu.add_command(label = "Last 8 Hours", command = lambda: self.highlight_new("480"))
        self.highlightmenu.add_command(label = "Last 24 Hours", command = lambda: self.highlight_new("1440"))

        self.toolsmenu = Menu(self.menubar, tearoff = 0)
        self.toolsmenu.add_command(label = 'Simple Offline Map', command = self.grid_map)
        self.toolsmenu.add_command(label = 'Visualize Waterfall', command = self.visualize_waterfall)
        self.toolsmenu.add_separator()
        self.toolsmenu.add_command(label = 'Expect System', command = self.expect)
        self.toolsmenu.add_command(label = 'Expect - Pause Replies', command = self.pause_expect)
        self.toolsmenu.add_command(label = 'Expect - Pause Auto TX', command = self.pause_autotx)
        self.toolsmenu.add_command(label = 'Expect - Blocklist', command = self.expect_blocklist)
        self.toolsmenu.add_separator()
        self.toolsmenu.add_cascade(label = 'MCForms - Forms', menu = self.formsmenu)
        self.toolsmenu.add_command(label = 'MCForms - Responses', command = self.form_responses)
        self.toolsmenu.add_command(label = 'Datecode Tool', command = self.datecode_tool)
        self.toolsmenu.add_separator()
        self.toolsmenu.add_command(label = 'CommStat - StatReps Received', command = self.commstat_rx)
        self.toolsmenu.add_command(label = 'CommStat - Send StatRep', command = self.commstat_tx)
        self.toolsmenu.add_command(label = 'CommStat - Send Checkin', command = self.commstat_checkin)
        self.toolsmenu.add_separator()

        self.aprsmenu = Menu(self.menubar, tearoff = 0)
        self.toolsmenu.add_cascade(label = 'APRS - Messages', menu = self.aprsmenu)
        self.aprsmenu.add_command(label = 'APRS - SMS Text', command = self.aprs_sms)
        self.aprsmenu.add_command(label = 'APRS - Email', command = self.aprs_email)
        self.aprsmenu.add_command(label = 'APRS - WhatsApp', command = self.aprs_wts)
        self.aprsmenu.add_command(label = 'APRS - Message', command = self.aprs_msg)

        self.toolsmenu.add_command(label = 'APRS - Report Grid', command = self.aprs_grid)
        self.toolsmenu.add_command(label = 'APRS - POTA Gateway', command = self.aprs_pota)
        self.toolsmenu.add_separator()
        self.toolsmenu.add_command(label = 'Database Search', command = self.database_search)
        self.toolsmenu.add_command(label = 'Database Trim', command = self.proc_dbtrim)
        self.toolsmenu.add_separator()
        self.toolsmenu.add_command(label = 'Disable Sounds', command = self.disable_sounds)

        self.helpmenu = Menu(self.menubar, tearoff = 0)
        self.helpmenu.add_command(label = 'Quick Help', command = self.showhelp)
        self.helpmenu.add_command(label = 'About', command = self.about)

        self.menubar.add_cascade(label = 'File', menu = self.filemenu)
        self.menubar.add_cascade(label = 'View', menu = self.viewmenu)
        self.menubar.add_cascade(label = 'Tools', menu = self.toolsmenu)
        self.menubar.add_cascade(label = 'Help', menu = self.helpmenu)
        self.config(menu = self.menubar)

        # profile title and select
        self.prframe = ttk.Frame(self)
        self.prframe.grid(row=0, column=0, columnspan=2, sticky='NSEW', padx=10, pady=(0,5))

        self.profilemark = ttk.Label(self.prframe, text='Profile:', font=("Segoe Ui Bold", 12))
        self.profilemark.grid(row=0, column = 0, sticky='W', padx=0, pady=(8,0))
        self.profilecombo = ttk.Combobox(self.prframe, values="", state='readonly')
        self.profilecombo.grid(row=0, column =1 , sticky='E', padx=8, pady=(8,0))
        self.profilecombo.bind('<<ComboboxSelected>>', self.profile_sel_combo)

        # view mode, quick filter title and entry
        self.qfframe = ttk.Frame(self)
        self.qfframe.grid(row=0, column=2, columnspan=2, sticky='NSE', padx=(0,0), pady=(0,5))

        self.vmodecombo = ttk.Combobox(self.qfframe, values=("Last 100","Last 1 Hour","Last 2 Hours","Last 4 Hours","Last 8 Hours","Last 24 Hours","Last 48 Hours","Last 72 Hours"), state='readonly')
        self.vmodecombo.grid(row=0, column=0 , sticky='E', padx=(0,16), pady=(8,0))
        self.vmodecombo.bind('<<ComboboxSelected>>', self.proc_viewmode)
        self.vmodecombo.set(settings["view_mode"])

        self.filtermark = ttk.Label(self.qfframe, text='Filter:')
        self.filtermark.grid(row=0, column=1, sticky='E', padx=0, pady=(8,0))
        self.filterword = ttk.Entry(self.qfframe, width = '10')
        self.filterword.grid(row=0, column=2, sticky='E', pady=(8,0))
        self.filterword.bind('<Return>', lambda ev: self.proc_filter())
        self.filterword.bind('<Escape>', lambda ev: self.proc_remfilter())

        self.filterbtn = ttk.Button(self.qfframe, text = 'Apply', command = self.proc_filter, width='6')
        self.filterbtn.grid(row=0, column=3, sticky='E', padx=(4,0), pady=(8,0))

        self.filterbtn2 = ttk.Button(self.qfframe, text = 'X', command = self.proc_remfilter, width='3')
        self.filterbtn2.grid(row=0, column=4, sticky='E', padx=(4,8), pady=(8,0))

        # background process checkbox
        self.current_profile_scan = IntVar()
        self.bgcheck = ttk.Checkbutton(self.prframe, text='Background Scan',variable=self.current_profile_scan, command=self.toggle_bg_scan)
        self.bgcheck.grid(row=0, column=2, sticky='W', pady=(8,0))

        # titles
        self.keywordmark = Label(self, text='Search Terms', fg='blue', font=("Segoe Ui", 12))
        self.keywordmark.grid(row=1, column = 0, sticky='W', padx=10)
        self.activitymark = Label(self, text="Matched Activity", fg='purple', font=("Segoe Ui", 12))
        self.activitymark.grid(row=1, column = 2, sticky='W', padx=10)

        # keyword treeview
        self.keywords = ttk.Treeview(self, show='headings', style='keywords.Treeview')
        self.keywords["columns"]=("search","comment","last_seen")

        self.keywords.column("search", width=95, minwidth=95)
        self.keywords.column("comment", width=95, minwidth=95, stretch=0)
        self.keywords.column("last_seen", width=140, minwidth=140, stretch=0)
        self.keywords.heading("search", text="Search", command=lambda c="search": self.sort_treeview(self.keywords, c, False))
        self.keywords.heading("comment", text="Comment", command=lambda c="comment": self.sort_treeview(self.keywords, c, False))
        self.keywords.heading("last_seen", text="Last Seen", command=lambda c="last_seen": self.sort_treeview(self.keywords, c, False))

        self.keywords.bind('<Double-1>', self.view_keyword_activity)
        self.keywords.bind('<Return>', lambda ev: self.view_keyword_activity(ev))
        self.keywords.grid(row=2, column=0, sticky='NSEW', padx=(10,0), pady=(0,10))
        self.kwscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.keywords.yview)
        self.keywords.configure(yscroll=self.kwscrollbar.set)
        self.kwscrollbar.grid(row=2, column=1, sticky='NS', padx=(0,0), pady=(0,10))

        # activity treeview
        self.activity = ttk.Treeview(self, show='headings', style='activity.Treeview', selectmode='browse')
        self.activity["columns"]=("type","value","stamp")

        self.activity.column("type", width=95, minwidth=95, stretch=0)
        self.activity.column("value", width=205, minwidth=205)
        self.activity.column("stamp", width=140, minwidth=140, stretch=0)
        self.activity.heading("type", text="Type")
        self.activity.heading("value", text="Activity")
        self.activity.heading("stamp", text="When")

        self.activity.bind('<Double-1>', self.view_activity)
        self.activity.bind('<Return>', lambda ev: self.view_activity(ev))
        self.activity.bind('<Button-3>', lambda ev: self.copy_activity(ev,"mact"))
        self.activity.grid(row=2, column=2, sticky='NSEW', padx=(10,0), pady=(0,10))
        self.acscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.activity.yview)
        self.activity.configure(yscroll=self.acscrollbar.set)
        self.acscrollbar.grid(row=2, column=3, sticky='NS', padx=(0,10), pady=(0,10))

        # add inputs and buttons below treeviews
        self.kwframe = Frame(self)
        self.kwframe.grid(row=3, column=0, columnspan=2, sticky='NSEW', padx=(10,0), pady=(0,10))

        self.addbat_button = ttk.Button(self.kwframe, text = 'Add', command = self.add_batch, width='5')
        self.addbat_button.grid(row=0, column = 0)
        self.removekw_button = ttk.Button(self.kwframe, text = 'Remove', command = self.proc_remkw, width='8')
        self.removekw_button.grid(row=0, column = 1, padx=8)

        self.expbat_button = ttk.Button(self.kwframe, text = 'Export All', command = self.proc_exportsearch, width='10')
        self.expbat_button.grid(row=0, column = 2, padx=(64,0))

        self.acframe = ttk.Frame(self)
        self.acframe.grid(row=3, column=2, columnspan=2, sticky='NWE')
        self.acframe.grid_columnconfigure(0, weight=1)

        self.expact_button = ttk.Button(self.acframe, text = 'Export Log', command = self.proc_exportlog)
        self.expact_button.grid(row=0, column=2, sticky='NE', padx=(0,8), pady=0)

        self.clearact_button = ttk.Button(self.acframe, text = 'Clear Log', command = self.proc_dellog)
        self.clearact_button.grid(row=0, column=3, sticky='NE', padx=(0,8), pady=0)

        # status bar
        self.statusbar = ttk.Label(self, text="Status: Waiting for TCP data... ", relief='sunken', anchor='w')
        self.statusbar.grid(row=4,column=0,columnspan=4, sticky='EW', padx=0, pady=(0,0))
        self.statusbar.bind("<Button-1>", lambda x: self.clear_statusbar())

    def toggle_theme(self):
        global settings
        if settings['dark_theme'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'dark_theme'")
            settings['dark_theme'] = "0"
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'dark_theme'")
            settings['dark_theme'] = "1"
        conn.commit()
        self.activate_theme()

    def activate_theme(self):
        if settings['dark_theme'] == "1":
            self.viewmenu.entryconfigure(5, label="\u2713 Dark Theme")
            self.call("set_theme", "dark")
            self.keywordmark.configure(fg='#6699FF')
            self.activitymark.configure(fg='#CC66FF')
            self.style.map('keywords.Treeview', background=[('selected', '#4477FF')])
            self.style.map('activity.Treeview', background=[('selected', '#AA44FF')])
            self.activity.tag_configure('oddrow', background='#777')
            self.activity.tag_configure('evenrow', background='#555')
            self.keywords.tag_configure('oddrow', background='#777')
            self.keywords.tag_configure('evenrow', background='#555')
            self.keywords.tag_configure('hlorow', background='#F66', foreground='#000')
            self.keywords.tag_configure('hlerow', background='#F33', foreground='#000')
        else:
            self.viewmenu.entryconfigure(5, label="Dark Theme")
            self.call("set_theme", "light")
            self.keywordmark.configure(fg='#4477FF')
            self.activitymark.configure(fg='#AA44FF')
            self.style.map('keywords.Treeview', background=[('selected', '#6699FF')])
            self.style.map('activity.Treeview', background=[('selected', '#CC66FF')])
            self.activity.tag_configure('oddrow', background='#EEE')
            self.activity.tag_configure('evenrow', background='#FFF')
            self.keywords.tag_configure('oddrow', background='#EEE')
            self.keywords.tag_configure('evenrow', background='#FFF')
            self.keywords.tag_configure('hlorow', background='#F66', foreground='#000')
            self.keywords.tag_configure('hlerow', background='#F33', foreground='#000')
        self.update()

    ## Process quick filter and apply to treeview
    def proc_filter(self):
        # stub in case anything more needs to be done beyond refresh
        self.refresh_activity_tree()

    def proc_remfilter(self):
        self.filterword.delete(0,END)
        self.refresh_activity_tree()

    ## Add keywords to a profile
    def add_batch(self):
        self.top = Toplevel(self)
        self.top.title("Add Search Terms")
        self.top.geometry('400x500')
        self.top.minsize(400,500)

        self.addbatmark = ttk.Label(self.top, text="Type or paste (ctrl+v) search terms (with optional tab+comment)\nFormat is \"search term<tab>comment\", one per line")
        self.addbatmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save button
        tlframe = ttk.Frame(self.top)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.save_button = ttk.Button(tlframe, text = 'Add Batch', command = self.proc_addbatch)
        self.save_button.pack(side=LEFT, padx=(0,10))

        # text window
        self.batch = Text(self.top, wrap=NONE)
        batch_scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.batch.yview)
        self.batch.configure(yscroll=batch_scrollbar.set)
        batch_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.batch.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Process new search terms (and optional comments)
    def proc_addbatch(self):
        batch_values = StringIO(self.batch.get('1.0','end'))
        for line in batch_values:
            new_entry=line.rstrip('\n').split("\t")
#            new_entry=line.rstrip().split("\t")
            new_kw=new_entry[0].upper()
            new_comment=""
            if len(new_entry)==2:
                new_comment=new_entry[1]

            if new_kw == "": continue
            c.execute("SELECT * FROM search WHERE profile_id = ? AND keyword = ?", [current_profile_id,new_kw])
            kw_exists = c.fetchone()
            if not kw_exists:
                c.execute("INSERT INTO search(profile_id,keyword,comment) VALUES (?,?,?)", [current_profile_id,new_kw,new_comment])
                conn.commit()
        self.top.destroy()
        self.refresh_keyword_tree()

    ## Export search terms
    def proc_exportsearch(self):
        self.top = Toplevel(self)
        self.top.title("Export Search Terms")
        self.top.geometry('400x500')
        self.top.minsize(400,500)

        self.exportmark = ttk.Label(self.top, text="Copy (ctrl+c) / Export Search Terms\nTab-delimited comments")
        self.exportmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save and copy buttons
        tlframe = ttk.Frame(self.top)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
        self.copy_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
        self.saveas_button.pack(side=RIGHT)

        # text export window
        self.export_text = Text(self.top, wrap=NONE)
        export_scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscroll=export_scrollbar.set)
        export_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        # right-click action
        self.rcmenu = Menu(self.top, tearoff = 0)
        self.rcmenu.add_command(label = 'Copy')
        self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

        c.execute("SELECT * FROM search WHERE profile_id = ? ORDER BY keyword ASC",[current_profile_id])
        export_kw_records = c.fetchall()

        for record in export_kw_records:
            insert_rec = record[2]
            if str(record[4])!="" and str(record[4])!="None": insert_rec = insert_rec + "\t" + str(record[4])
            insert_rec = insert_rec + "\n"
            self.export_text.insert(tk.END, insert_rec)

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Remove keyword from database/tree
    def proc_remkw(self):
        kwlist = ""
        for kwiid in self.keywords.selection():
            kwlist += str(self.keywords.item(kwiid)['values'][0])+"\n"

        if kwlist == "":
            messagebox.showwarning("Nothing selected","You must select one or more keywords to remove.")
            return

        msgtxt = "Remove the following search term(s)?\n"+kwlist
        answer = askyesno(title='Remove Search Term(s)?', message=msgtxt)
        if answer:
            for kwiid in self.keywords.selection():
                c.execute("DELETE FROM search WHERE id = ? AND profile_id = ?", [kwiid,current_profile_id])
            conn.commit()
            self.refresh_keyword_tree()

    ## Toggle Heartbeat Display in activity pane
    def toggle_view_hb(self):
        global settings
        if settings['hide_heartbeat'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'hide_heartbeat'")
            settings['hide_heartbeat'] = "0"
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'hide_heartbeat'")
            settings['hide_heartbeat'] = "1"
        conn.commit()
        self.refresh_activity_tree()

    ## Toggle RX.SPOT Display in activity pane
    def toggle_view_spot(self):
        global settings
        if settings['hide_spot'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'hide_spot'")
            settings['hide_spot'] = "0"
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'hide_spot'")
            settings['hide_spot'] = "1"
        conn.commit()
        self.refresh_activity_tree()

    ## Toggle RX.ACTIVITY Display in activity pane
    def toggle_view_activity(self):
        global settings
        if settings['hide_activity'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'hide_activity'")
            settings['hide_activity'] = "0"
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'hide_activity'")
            settings['hide_activity'] = "1"
        conn.commit()
        self.refresh_activity_tree()

    ## Toggle RX.DIRECTED Display in activity pane
    def toggle_view_directed(self):
        global settings
        if settings['hide_directed'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'hide_directed'")
            settings['hide_directed'] = "0"
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'hide_directed'")
            settings['hide_directed'] = "1"
        conn.commit()
        self.refresh_activity_tree()

    ## Toggle background scan setting for current profile
    def toggle_bg_scan(self):
        bg_setting = self.current_profile_scan.get()
        if bg_setting == 1:
            c.execute("UPDATE profile SET bgscan = 1 WHERE id = ?", [current_profile_id])
        else:
            c.execute("UPDATE profile SET bgscan = 0 WHERE id = ?", [current_profile_id])
        conn.commit()
        self.refresh_keyword_tree()

    ## User selectable highlight range (highlight search terms hit within n minutes)
    def highlight_new(self, hlrange):
        self.highlightmenu.entryconfigure(0, label="None")
        self.highlightmenu.entryconfigure(1, label="Last 15 Minutes")
        self.highlightmenu.entryconfigure(2, label="Last 30 Minutes")
        self.highlightmenu.entryconfigure(3, label="Last 45 Minutes")
        self.highlightmenu.entryconfigure(4, label="Last 1 Hour")
        self.highlightmenu.entryconfigure(5, label="Last 2 Hours ")
        self.highlightmenu.entryconfigure(6, label="Last 4 Hours")
        self.highlightmenu.entryconfigure(7, label="Last 8 Hours")
        self.highlightmenu.entryconfigure(8, label="Last 24 Hours")

        settings['highlight_new']=hlrange

        if hlrange=="0":  self.highlightmenu.entryconfigure(0, label="\u2713 None")
        if hlrange=="15": self.highlightmenu.entryconfigure(1, label="\u2713 Last 15 Minutes")
        if hlrange=="30": self.highlightmenu.entryconfigure(2, label="\u2713 Last 30 Minutes")
        if hlrange=="45": self.highlightmenu.entryconfigure(3, label="\u2713 Last 45 Minutes")
        if hlrange=="60": self.highlightmenu.entryconfigure(4, label="\u2713 Last 1 Hour")
        if hlrange=="120": self.highlightmenu.entryconfigure(5, label="\u2713 Last 2 Hours")
        if hlrange=="240": self.highlightmenu.entryconfigure(6, label="\u2713 Last 4 Hours")
        if hlrange=="480": self.highlightmenu.entryconfigure(7, label="\u2713 Last 8 Hours")
        if hlrange=="1440": self.highlightmenu.entryconfigure(8, label="\u2713 Last 24 Hours")

        c.execute("UPDATE setting SET value = ? WHERE name = 'highlight_new'", [hlrange])
        conn.commit()

        self.refresh_keyword_tree()

    ## Datecode encoder/decoder tool
    def datecode_tool(self):
        self.top = Toplevel(self)
        self.top.title("Datecode Tool")
        self.top.resizable(width=False, height=False)

        # we'll pre-populate the current date/time
        curtime=time.localtime(time.time())
        m=int(curtime[1])
        d=int(curtime[2])
        h=int(curtime[3])
        mi=int(curtime[4])

        # date input section
        dateinput = ttk.Frame(self.top)
        dateinput.grid(row=0, column=0,padx=10,pady=10)

        label_mon = ttk.Label(dateinput, text = "Month (1-12)")
        label_mon.grid(row = 0, column = 0)
        self.edit_mon = ttk.Entry(dateinput, width = '4')
        self.edit_mon.grid(row = 0, column = 1)
        self.edit_mon.insert(0, m)

        label_day = ttk.Label(dateinput, text = "Day (1-31)")
        label_day.grid(row = 1, column = 0)
        self.edit_day = ttk.Entry(dateinput, width = '4')
        self.edit_day.grid(row = 1, column = 1)
        self.edit_day.insert(0, d)

        label_hr = ttk.Label(dateinput, text = "Hour (0-23)")
        label_hr.grid(row = 2, column = 0)
        self.edit_hr = ttk.Entry(dateinput, width = '4')
        self.edit_hr.grid(row = 2, column = 1)
        self.edit_hr.insert(0, h)

        label_min = ttk.Label(dateinput, text = "Minute (0-59)")
        label_min.grid(row = 3, column = 0)
        self.edit_min = ttk.Entry(dateinput, width = '4')
        self.edit_min.grid(row = 3, column = 1)
        self.edit_min.insert(0, mi)

        # actions
        actions = ttk.Frame(self.top)
        actions.grid(row=0, column=1,padx=10,pady=10)

        button_encode = ttk.Button(actions, text = "Encode \u2192", command = self.datecodetool_encode)
        button_encode.grid(row=0, column = 0,pady=10)
        button_decode = ttk.Button(actions, text = "\u2190 Decode", command = self.datecodetool_decode)
        button_decode.grid(row=1, column = 0)

        # output
        self.edit_dc = ttk.Entry(self.top)
        self.edit_dc.grid(row = 0, column = 2,padx=10,pady=10)

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def datecodetool_encode(self):
        m=self.edit_mon.get()
        d=self.edit_day.get()
        h=self.edit_hr.get()
        mi=self.edit_min.get()

        errors=""

        if int(m)<1 or int(m)>12:
            errors+="The month value is out of range (1-12)\n"
        if int(d)<1 or int(d)>31:
            errors+="The day value is out of range (1-31)\n"
        if int(h)<0 or int(h)>23:
            errors+="The hour value is out of range (0-23)\n"
        if int(mi)<0 or int(mi)>59:
            errors+="The minute value is out of range (0-59)\n"

        if errors!="":
            messagebox.showwarning("Input Error",errors, parent=self.top)
        else:
            self.edit_dc.delete(0,END)
            self.edit_dc.insert(0,self.encode_custshorttime(m,d,h,mi))

    def datecodetool_decode(self):
        dc=self.edit_dc.get().upper()
        try:
            if dc[0] != "#":
                messagebox.showwarning("Error","Datecodes start with the # symbol.", parent=self.top)
                return
        except IndexError:
            return

        scan_date = re.search(r"([0-9]+)\/([0-9]+)\ ([0-9]+)\:([0-9]+)",self.decode_shorttime(dc))
        if scan_date:
            self.edit_mon.delete(0,END)
            self.edit_day.delete(0,END)
            self.edit_hr.delete(0,END)
            self.edit_min.delete(0,END)

            self.edit_mon.insert(0,scan_date[1])
            self.edit_day.insert(0,scan_date[2])
            self.edit_hr.insert(0,scan_date[3])
            self.edit_min.insert(0,scan_date[4])
        else:
            messagebox.showwarning("Error","There was an error decoding the text you entered.", parent=self.top)

    ## Toggle disable notification sounds
    def disable_sounds(self):
        global settings
        if settings['disable_sounds'] == "0":
            self.toolsmenu.entryconfigure(23, label="\u2713 Disable Sounds")
            c.execute("UPDATE setting SET value = '1' WHERE name = 'disable_sounds'")
            settings['disable_sounds'] = "1"
        else:
            self.toolsmenu.entryconfigure(23, label="Disable Sounds")
            c.execute("UPDATE setting SET value = '0' WHERE name = 'disable_sounds'")
            settings['disable_sounds'] = "0"
        conn.commit()

    ## Refresh main window keyword tree
    def refresh_keyword_tree(self):
        global search_strings, bgsearch_strings
        # preserve focus after refresh
        kwiid=0
        if self.keywords.focus(): kwiid = int(self.keywords.focus())

        # clear out and rebuild
        for entry in self.keywords.get_children():
            self.keywords.delete(entry)
        search_strings.clear()
        bgsearch_strings.clear()

        # we will need to know which profiles have background scan enabled
        c.execute("SELECT id FROM profile WHERE bgscan = '1'")
        profile_bgscan = c.fetchall()

        bgscans=[]
        for prof in profile_bgscan:
            bgscans.append(prof[0])

        c.execute("SELECT * FROM search ORDER BY last_seen DESC")
        search_records = c.fetchall()

        count=0
        for record in search_records:
            comment = str(record[4]) if str(record[4])!="None" else ""
            if record[1] == current_profile_id:
                if count % 2 == 1:
                    self.keywords.insert('', tk.END, iid=record[0], values=(record[2],comment,record[3]), tags=('oddrow'))
                else:
                    self.keywords.insert('', tk.END, iid=record[0], values=(record[2],comment,record[3]), tags=('evenrow'))

                # highlight if within selected highlight range
                if isinstance(record[3], str):
#                    recdelta = datetime.datetime.utcnow() - datetime.datetime.strptime(record[3], "%Y-%m-%d %H:%M:%S") # utcnow deprecated
                    recdelta = datetime.datetime.now() - datetime.datetime.strptime(record[3], '%Y-%m-%d %H:%M:%S')
                    rdmin = int(recdelta.total_seconds() / 60)

                    if rdmin < int(settings['highlight_new']) and int(settings['highlight_new'])>0:

                        if count % 2 == 1:
                            self.keywords.item(record[0], tags="hlorow")
                        else:
                            self.keywords.item(record[0], tags="hlerow")

                count+=1
                search_strings.append(record[2])
            else:
                # check if profile in question has background scan enabled
                if record[1] in bgscans:
                    bgsearch_strings[record[2]]=record[1]

        # restore focus
        if kwiid>0:
            if self.keywords.exists(kwiid) == True:
                self.keywords.focus(kwiid)
                self.keywords.selection_set(kwiid)

    # process a change in the view mode, save to db
    def proc_viewmode(self, ev):
        global settings
        viewmode = self.vmodecombo.get()

        c.execute("UPDATE setting SET value = '"+viewmode+"' WHERE name = 'view_mode'")
        settings['view_mode'] = viewmode
        conn.commit()

        self.refresh_activity_tree()

    ## Refresh main window activity tree
    def refresh_activity_tree(self):
        global settings
        # preserve focus after refresh
        aciid=0
        if self.activity.focus(): aciid = int(self.activity.focus())

        viewmode = self.vmodecombo.get()

        for entry in self.activity.get_children():
            self.activity.delete(entry)

        # process filter sql additions
        qfilter = self.filterword.get().upper()
        wheres = " AND value LIKE '%"+qfilter+"%' " if qfilter!="" else ""

        # process view mode sql additions
        reclimit=""
        if viewmode=="Last 100": reclimit = " LIMIT 100"
        if viewmode=="Last 1 Hour": wheres += " AND (spotdate > DATETIME('now','-1 Hour')) "
        if viewmode=="Last 2 Hours": wheres += " AND (spotdate > DATETIME('now','-2 Hour')) "
        if viewmode=="Last 4 Hours": wheres += " AND (spotdate > DATETIME('now','-4 Hour')) "
        if viewmode=="Last 8 Hours": wheres += " AND (spotdate > DATETIME('now','-8 Hour')) "
        if viewmode=="Last 24 Hours": wheres += " AND (spotdate > DATETIME('now','-24 Hour')) "
        if viewmode=="Last 48 Hours": wheres += " AND (spotdate > DATETIME('now','-48 Hour')) "
        if viewmode=="Last 72 Hours": wheres += " AND (spotdate > DATETIME('now','-72 Hour')) "

        # Update menu & labels based on view menu selections
        self.viewmenu.entryconfigure(0, label="Hide Heartbeats")
        self.viewmenu.entryconfigure(1, label="Hide RX.SPOT")
        self.viewmenu.entryconfigure(2, label="Hide RX.ACTIVITY")
        self.viewmenu.entryconfigure(3, label="Hide RX.DIRECTED")
        self.activitymark.config(text = "Matched Activity")

        # refreshing all checkmark settings in menus, and add any applicable WHERE statements
        if settings['pause_expect']=="1":
            self.toolsmenu.entryconfigure(4, label="\u2713 Expect - Pause Replies")

        if settings['pause_autotx']=="1":
            self.toolsmenu.entryconfigure(5, label="\u2713 Expect - Pause Auto TX")

        if settings['disable_sounds'] == "1":
            self.toolsmenu.entryconfigure(23, label="\u2713 Disable Sounds")

        if settings['hide_heartbeat']=="1":
            wheres += " AND value NOT LIKE '%HB%' AND value NOT LIKE '%HEARTBEAT%' "
            self.activitymark.config(text = "Matched Activity*")
            self.viewmenu.entryconfigure(0, label="\u2713 Hide Heartbeats")

        if settings['hide_spot']=="1":
            wheres += " AND type NOT LIKE '%RX.SPOT%' "
            self.activitymark.config(text = "Matched Activity*")
            self.viewmenu.entryconfigure(1, label="\u2713 Hide RX.SPOT")

        if settings['hide_activity']=="1":
            wheres += " AND type NOT LIKE '%RX.ACTIVITY%' "
            self.activitymark.config(text = "Matched Activity*")
            self.viewmenu.entryconfigure(2, label="\u2713 Hide RX.ACTIVITY")

        if settings['hide_directed']=="1":
            wheres += " AND type NOT LIKE '%RX.DIRECTED%' "
            self.activitymark.config(text = "Matched Activity*")
            self.viewmenu.entryconfigure(3, label="\u2713 Hide RX.DIRECTED")

        self.highlight_new(settings['highlight_new'])

        refresh_act_sql = "SELECT * FROM activity WHERE profile_id = '"+str(current_profile_id)+"' "+wheres+" ORDER BY spotdate DESC"+reclimit
        c.execute(refresh_act_sql)

        activity_records = c.fetchall()

        count=0
        for record in activity_records:
            # use CALL if ACTIVITY is blank (RX.SPOT)
            act=record[3]
            if act=="": act=record[6]

            if count % 2 == 1:
                self.activity.insert('', tk.END, iid=record[0], values=(record[2],act,record[7]), tags=('oddrow'))
            else:
                self.activity.insert('', tk.END, iid=record[0], values=(record[2],act,record[7]), tags=('evenrow'))
            count+=1

        if aciid>0:
            if self.activity.exists(aciid) == True:
                self.activity.focus(aciid)
                self.activity.selection_set(aciid)

    ## Build/rebuild profile sub-menu from database
    def build_profilemenu(self):
        global current_profile_id
        # first, remove any entries that exist in sub-menu
        if self.profilemenu.winfo_exists():
            if self.profilemenu.index('end') is not None:
                self.profilemenu.delete(0,self.profilemenu.index('end'))

        # also remove all from combobox
        self.profilecombo.delete(0, tk.END)

        # next, rebuild from database
        try:
            c.execute("SELECT * FROM profile ORDER BY sort,id")
        except sqlite3.OperationalError:
            messagebox.showwarning("Database Error","Could not load profiles.\n\nPlease make sure your database version is updated and compatible.")
            return

        profile_records = c.fetchall()
        comboopts = []

        for record in profile_records:
            comboopts.append(record[1])

            if record[2] == 1:
                seltext = " *"
                current_profile_id = record[0]
                combosel = record[1]
                bgscanbox = record[3]
            else:
                seltext = ""
            self.profilemenu.add_command(label = record[1]+seltext, command = lambda profileid=record[0]: self.profile_select(profileid))

        # update bgscan checkbox based on current visible profile setting
        if bgscanbox == 1:
            self.current_profile_scan.set(1)
        else:
            self.current_profile_scan.set(0)

        self.profilecombo['values'] = comboopts
        self.profilecombo.set(combosel)
        self.update()

    ## Select a profile
    def profile_select(self, profileid):
        c.execute("UPDATE profile SET def = 0")
        c.execute("UPDATE profile SET def = 1 WHERE id = ?", [profileid])
        conn.commit()
        self.build_profilemenu()
        self.refresh_keyword_tree()
        self.refresh_activity_tree()

    ## Select a profile through the combobox
    def profile_sel_combo(self, ev):
        # note that profile titles are a unique key in the database so they're safe to match on
        profile_title = self.profilecombo.get()
        c.execute("UPDATE profile SET def = 0")
        c.execute("UPDATE profile SET def = 1 WHERE title = ?", [profile_title])
        conn.commit()
        self.build_profilemenu()
        self.refresh_keyword_tree()
        self.refresh_activity_tree()

    ## Edit existing profile
    def profile_edit(self, action):
        global current_profile_id, notifyProfile
        self.top = Toplevel(self)

        if action=="edit":
            c.execute("SELECT * FROM profile WHERE id = ?",[current_profile_id])
            profile_record = c.fetchone()
            self.top.title("Edit Profile")
        else:
            self.top.title("New Profile")

        self.top.resizable(width=False, height=False)

        label_edit = ttk.Label(self.top, text = "Profile Name")
        label_edit.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.edit_profile = ttk.Entry(self.top)
        if action=="edit": self.edit_profile.insert(0, profile_record[1])
        self.edit_profile.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))

        label_sound = ttk.Label(self.top, text = "Notification WAV")
        label_sound.grid(row = 1, column = 0, padx=(10,0), pady=(20,0))

        self.wavsel = ttk.Combobox(self.top, values=wavs, state='readonly', width='15')
        if action=="edit":
            try:
                self.wavsel.current(wavs.index(notifyProfile[str(current_profile_id)]));
            except KeyError:
                self.wavsel.current(wavs.index("None"))
        else:
            self.wavsel.current(wavs.index("None"))

        self.wavsel.grid(row=1, column =1, padx=(0,10), pady=(20,0))
        self.wavsel.bind('<<ComboboxSelected>>', self.proc_wavsel)

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=2, columnspan=2, sticky='NSEW', padx=10)

        if action=="edit":
            save_button = ttk.Button(cbframe, text = "Save", command = lambda: self.proc_edit("edit"))
        else:
            save_button = ttk.Button(cbframe, text = "Save", command = lambda: self.proc_edit("new"))

        save_button.grid(row=0, column = 0, padx=(60,20), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 1, pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.edit_profile.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Process profile edit
    def proc_edit(self, action):
        global current_profile_id, notifyProfile
        new_val = self.edit_profile.get()
        new_wav = self.wavsel.get()

        if new_wav=="None": new_wav=""
        if new_val == "": return

        if action=="edit":
            c.execute("UPDATE profile SET title = ? WHERE id = ?", [new_val, current_profile_id])
            c.execute("DELETE FROM notify WHERE type = '1' AND trigger = ?", [current_profile_id])
            if new_wav != "":
                c.execute("INSERT INTO notify(type,trigger,action) VALUES ('1',?,?)", [current_profile_id,new_wav])
            conn.commit()
            notifyProfile[str(current_profile_id)]=new_wav
        else:
            c.execute("INSERT INTO profile(title,def,bgscan) VALUES (?,?,?)", [new_val,0,0])
            conn.commit()
            newprofid=c.lastrowid
            c.execute("DELETE FROM notify WHERE type = '1' AND trigger = ?", [newprofid])
            if new_wav != "":
                c.execute("INSERT INTO notify(type,trigger,action) VALUES ('1',?,?)", [newprofid,new_wav])
            conn.commit()
            notifyProfile[str(newprofid)]=new_wav

        self.build_profilemenu()
        self.top.destroy()

    ## process wav file selection change (preview sound on change)
    def proc_wavsel(self, ev):
        global nosound

        new_wav = self.wavsel.get()
        if new_wav=="None": return

        if nosound==0:
            try:
                snd = tkSnack.Sound()
                snd.read(new_wav)
                snd.play(blocking=0)
            except:
                pass
        if nosound==2:
            try:
                wave_obj = sa.WaveObject.from_wave_file(new_wav)
                play_obj = wave_obj.play()
            except:
                pass

    ## Delete the current selected profile
    def menu_remove(self):
        global current_profile_id

        # make sure we're not deleting the last remaining profile
        c.execute("SELECT Count() FROM profile")
        profile_count = c.fetchone()[0]

        if profile_count < 2:
            messagebox.showwarning("Error Removing Profile","Unable to remove selected profile, because it is the last remaining profile. At least one profile must be configured.")
            return

        c.execute("SELECT * FROM profile WHERE id = ?",[current_profile_id])
        profile_record = c.fetchone()

        msgtxt = "Are you sure you want to remove the profile named "+profile_record[1]+" and all associated activity? This action cannot be undone."
        answer = askyesno(title='Remove Profile?', message=msgtxt)
        if answer:
            c.execute("DELETE FROM profile WHERE id = ?", [current_profile_id])
            c.execute("DELETE FROM activity WHERE profile_id = ?", [current_profile_id])
            c.execute("DELETE FROM search WHERE profile_id = ?", [current_profile_id])
            c.execute("DELETE FROM notify WHERE type = '1' AND trigger = ?", [current_profile_id])
            c.execute("UPDATE profile SET def = 1 WHERE rowid = (SELECT MIN(rowid) FROM profile)") # reset the default profile
            conn.commit()
            current_profile_id = 0
            self.build_profilemenu()
            self.refresh_keyword_tree()
            self.refresh_activity_tree()

    def profile_sort(self):
        self.top = Toplevel(self)
        self.top.title("Sort Profiles")
        self.top.resizable(width=False, height=False)

        self.top.profiles = ttk.Treeview(self.top, show='headings', selectmode="browse", height="6")
        self.top.profiles["columns"]=("profile")
        self.top.profiles.column("profile", width=120, minwidth=120)
        self.top.profiles.heading("profile", text="Profiles")

        try:
            c.execute("SELECT * FROM profile ORDER BY sort,id")
        except sqlite3.OperationalError:
            messagebox.showwarning("Database Error","Could not load profiles.\n\nPlease make sure your database version is updated and compatible.")
            return

        profile_records = c.fetchall()

        for record in profile_records:
            self.top.profiles.insert("", tk.END, iid=record[0], value=(record[1],))

        self.top.profiles.grid(row=0, column=0, sticky='NSEW', padx=(10,0), pady=10)

        self.top.pscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.top.profiles.yview)
        self.top.profiles.configure(yscroll=self.top.pscrollbar.set)
        self.top.pscrollbar.grid(row=0, column=1, sticky='NS', padx=(0,10), pady=10)

        dirs = ttk.Frame(self.top)
        dirs.grid(row=1, columnspan=2,padx=10,pady=(0,10))

        move_up = ttk.Button(dirs, text="\u21E1", command=lambda: self.psort_move("up"), width=5)
        move_up.grid(row=0, column=0, padx=(0,10))
        move_dn = ttk.Button(dirs, text="\u21E3", command=lambda: self.psort_move("down"), width=5)
        move_dn.grid(row=0, column=1)

        move_dn = ttk.Button(self.top, text="Save", command=self.psort_save)
        move_dn.grid(row=2, columnspan=2, pady=(10,10))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def psort_move(self, direction):
        try:
            item = self.top.profiles.selection()[0]
        except IndexError:
            return
        items = self.top.profiles.get_children()
        current_index = items.index(item)

        if direction == "up" and current_index > 0:
            self.top.profiles.move(item, '', current_index - 1)
        elif direction == "down" and current_index < len(items) - 1:
            self.top.profiles.move(item, '', current_index + 1)

    def psort_save(self):
        i=1
        for entry in self.top.profiles.get_children():
            sql_sort = "UPDATE profile SET sort = '"+str(i)+"' WHERE id = '"+str(entry)+"'"
            i+=1
            c.execute(sql_sort)

        conn.commit()
        self.build_profilemenu()
        self.top.destroy()

    ## Export activity log for current profile
    def proc_exportlog(self):
        global current_profile_id
        c.execute("SELECT * FROM profile WHERE id = ?",[current_profile_id])
        profile_record = c.fetchone()

        self.top = Toplevel(self)
        self.top.title("Export "+profile_record[1]+" Activity")
        self.top.geometry('650x500')

        self.exportmark = ttk.Label(self.top, text="Tab-delimited export for profile:"+profile_record[1])
        self.exportmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save and copy buttons
        tlframe = ttk.Frame(self.top)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
        self.copy_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
        self.saveas_button.pack(side=RIGHT)

        # text window
        self.export_text = Text(self.top, wrap=NONE)
        export_scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscroll=export_scrollbar.set)
        export_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        # right-click action
        self.rcmenu = Menu(self.top, tearoff = 0)
        self.rcmenu.add_command(label = 'Copy')
        self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

        c.execute("SELECT * FROM activity WHERE profile_id = ? ORDER BY spotdate DESC",[current_profile_id])
        export_activity_records = c.fetchall()

        for record in export_activity_records:
            insert_rec = record[7]+"\t"+record[2]+"\t"+record[3]+"\t"+record[4]+"\t"+record[5]+"\t"+record[6]+"\n"
            self.export_text.insert(tk.END, insert_rec)

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def export_saveas_popup(self):
        fname = filedialog.asksaveasfilename(defaultextension=".txt", parent=self)
        if fname is None or fname == '' or type(fname) is tuple: return
        saveas_text = str(self.export_text.get('1.0', 'end'))
        with open(fname,mode='w',encoding='utf-8') as f:
            f.write(saveas_text)
            f.close()

    def export_copy_all(self):
        self.clipboard_clear()
        text = self.export_text.get('1.0', 'end')
        self.clipboard_append(text)

    ## Export right-click copy action
    def export_copy_popup(self, ev):
        self.rcmenu.post(ev.x_root,ev.y_root)
        if self.export_text.tag_ranges("sel"):
            self.clipboard_clear()
            text = self.export_text.get('sel.first', 'sel.last')
            self.clipboard_append(text)

    ## Delete profile activity log entries
    def proc_dellog(self):
        global current_profile_id

        c.execute("SELECT * FROM profile WHERE id = ?",[current_profile_id])
        profile_record = c.fetchone()

        msgtxt = "Are you sure you want to remove all activity for the "+profile_record[1]+" profile? This action cannot be undone."
        answer = askyesno(title='Clear Log?', message=msgtxt)
        if answer:
            # delete associated activity logs from the database
            c.execute("DELETE FROM activity WHERE profile_id = ?", [current_profile_id])
            conn.commit()
            self.refresh_activity_tree()

    def activity_msg_format(self, activity):
        global speeds
        speedtxt=""
        if activity[10]!="": speedtxt = speeds[activity[10]]
        actmsg="Message Details:\n\n"
#        actmsg+="DBID:     "+str(activity[0])+"\n"
        actmsg+="Call:     "+activity[6]+"\n"
        actmsg+="Dial:     "+activity[4]+"\n"
        actmsg+="Freq:     "+activity[8]+"\n"
        actmsg+="Offset:   "+activity[9]+"\n"
        actmsg+="Speed:    "+speedtxt+"\n\n"
        actmsg+="Date:     "+activity[7]+"\n"
        actmsg+="Text:     "+activity[3]+"\n\n"
        actmsg+="SNR:      "+activity[5]+"dB\n"
        actmsg+="Type:     "+activity[2]+"\n"
        return actmsg

    ## Copy activity to clipboard
    def copy_activity(self, ev, rxtype):
        aciid=0
        if rxtype=="mact" and self.activity.focus(): aciid = int(self.activity.focus())
        if rxtype=="act" and self.top.activity.focus(): aciid = int(self.top.activity.focus())
        if rxtype=="dir" and self.top.directed.focus(): aciid = int(self.top.directed.focus())
        if rxtype=="spot" and self.top.spot.focus(): aciid = int(self.top.spot.focus())

        if aciid>0:
            c.execute("SELECT * FROM activity WHERE id = ?",[aciid])
            activity = c.fetchone()
            actmsg = self.activity_msg_format(activity)
            self.clipboard_clear()
            self.clipboard_append(actmsg)
            if rxtype=="mact":
                messagebox.showinfo("Copied","Copied to clipboard")
            else:
                messagebox.showinfo("Copied","Copied to clipboard", parent=self.top)

    ## View activity detail from gui main window
    def view_activity(self, ev):
        if not self.activity.focus(): return
        aciid = int(self.activity.focus())
        c.execute("SELECT * FROM activity WHERE id = ?",[aciid])
        activity = c.fetchone()
        actmsg = self.activity_msg_format(activity)
        messagebox.showinfo("Activity Detail",actmsg)

    ## View activity details by type, from search term detail window
    def view_activity_type(self, rxtype):
        aciid=0
        if rxtype=="act" and self.top.activity.focus(): aciid = int(self.top.activity.focus())
        if rxtype=="dir" and self.top.directed.focus(): aciid = int(self.top.directed.focus())
        if rxtype=="spot" and self.top.spot.focus(): aciid = int(self.top.spot.focus())

        if aciid>0:
            c.execute("SELECT * FROM activity WHERE id = ?",[aciid])
            activity = c.fetchone()
            actmsg = self.activity_msg_format(activity)
            messagebox.showinfo("Activity Detail",actmsg, parent=self.top)

    ## View search term detail window, divided by type
    def view_keyword_activity(self, ev):
        if not self.keywords.focus(): return
        kwiid = int(self.keywords.focus())
        c.execute("SELECT * FROM search WHERE id = ?",[kwiid])
        search = c.fetchone()

        self.top = Toplevel(self)
        self.top.title("Search Term Activity")
        self.top.geometry('440x780')
        self.top.resizable(width=False, height=False)

        kwvals = self.keywords.item(kwiid)
        msgtxt = str(kwvals['values'][0])+" Activity"
        self.top.activitymark = ttk.Label(self.top, text=msgtxt, font=("14"))
        self.top.activitymark.grid(row=0, column = 0, sticky="W", padx=10)

        # Add/modify comment
        comframe = ttk.Frame(self.top)
        comframe.grid(row=1, column=0, columnspan=2, sticky='NSEW', padx=10, pady=(0,5))
        self.top.comment = ttk.Entry(comframe, width = '18')
        self.top.comment.grid(row=0, column=0, sticky='E', pady=(8,0))
        if str(search[4])!="None": self.top.comment.insert(0, str(search[4]))
        self.top.savecomment = ttk.Button(comframe, text = 'Save Comment', command = lambda: self.proc_comment(kwiid), width='14')
        self.top.savecomment.grid(row=0, column=1, sticky='E', padx=(8,8), pady=(8,0))

        # RX.ACTIVITY treeview
        self.top.activitymark = ttk.Label(self.top, text="RX.ACTIVITY", font=("12"))
        self.top.activitymark.grid(row=2, column = 0, sticky="W", padx=10)

        self.top.activity = ttk.Treeview(self.top, show='headings', selectmode="browse", height="6")
        self.top.activity["columns"]=("value","stamp")

        self.top.activity.column("value", width=240, minwidth=240)
        self.top.activity.column("stamp", width=120, minwidth=120, stretch=0)
        self.top.activity.heading('value', text='Activity')
        self.top.activity.heading('stamp', text='When')

        self.top.activity.bind('<Double-1>', lambda x: self.view_activity_type("act"))
        self.top.activity.bind('<Return>', lambda x: self.view_activity_type("act"))
        self.top.activity.bind('<Button-3>', lambda ev: self.copy_activity(ev,"act"))

        self.top.activity.grid(row=3, column = 0, sticky='NSEW', padx=(10,0), pady=(0,10))
        self.top.acscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.top.activity.yview)
        self.top.activity.configure(yscroll=self.top.acscrollbar.set)
        self.top.acscrollbar.grid(row=3, column=1, sticky='NSEW', padx=(0,10), pady=(0,10))

        sql = "SELECT * FROM activity WHERE profile_id = ? AND type = ? AND (call LIKE ? OR value LIKE ?) ORDER BY spotdate DESC"
        c.execute(sql,[current_profile_id,"RX.ACTIVITY",'%'+search[2]+'%','%'+search[2]+'%'])
        tactivity_records = c.fetchall()

        count=0
        for record in tactivity_records:
            if count % 2 == 1:
                self.top.activity.insert('', tk.END, iid=record[0], values=(record[3],record[7]), tags=('oddrow'))
            else:
                self.top.activity.insert('', tk.END, iid=record[0], values=(record[3],record[7]), tags=('evenrow'))
            count+=1

        # RX.DIRECTED treeview
        self.top.directedmark = ttk.Label(self.top, text="RX.DIRECTED", font=("12"))
        self.top.directedmark.grid(row=4, column = 0, sticky="W", padx=10)

        self.top.directed = ttk.Treeview(self.top, show='headings', selectmode="browse", height="6")
        self.top.directed["columns"]=("value","stamp")

        self.top.directed.column("value", width=240, minwidth=240)
        self.top.directed.column("stamp", width=120, minwidth=120, stretch=0)
        self.top.directed.heading('value', text='Directed')
        self.top.directed.heading('stamp', text='When')

        self.top.directed.bind('<Double-1>', lambda x: self.view_activity_type("dir"))
        self.top.directed.bind('<Return>', lambda x: self.view_activity_type("dir"))
        self.top.directed.bind('<Button-3>', lambda ev: self.copy_activity(ev,"dir"))

        self.top.directed.grid(row=5, column=0, sticky='NSEW', padx=(10,0), pady=(0,10))
        self.top.acscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.top.directed.yview)
        self.top.directed.configure(yscroll=self.top.acscrollbar.set)
        self.top.acscrollbar.grid(row=5, column=1, sticky='NS', padx=(0,10), pady=(0,10))

        sql = "SELECT * FROM activity WHERE profile_id = ? AND type = ? AND (call LIKE ? OR value LIKE ?) ORDER BY spotdate DESC"
        c.execute(sql,[current_profile_id,"RX.DIRECTED",'%'+search[2]+'%','%'+search[2]+'%'])
        dactivity_records = c.fetchall()

        count=0
        for record in dactivity_records:
            if count % 2 == 1:
                self.top.directed.insert('', tk.END, iid=record[0], values=(record[3],record[7]), tags=('oddrow'))
            else:
                self.top.directed.insert('', tk.END, iid=record[0], values=(record[3],record[7]), tags=('evenrow'))
            count+=1

        # RX.DIRECTED treeview
        self.top.spotmark = ttk.Label(self.top, text="RX.SPOT", font=("12"))
        self.top.spotmark.grid(row=6, column = 0, sticky="W", padx=10)

        self.top.spot = ttk.Treeview(self.top, show='headings', selectmode="browse", height="6")
        self.top.spot["columns"]=("snr","call","stamp")

        self.top.spot.column("snr", width=60, minwidth=60)
        self.top.spot.column("call", width=180, minwidth=180)
        self.top.spot.column("stamp", width=120, minwidth=120, stretch=0)
        self.top.spot.heading('snr', text='SNR')
        self.top.spot.heading('call', text='Call')
        self.top.spot.heading('stamp', text='When')

        self.top.spot.bind('<Double-1>', lambda x: self.view_activity_type("spot"))
        self.top.spot.bind('<Return>', lambda x: self.view_activity_type("spot"))
        self.top.spot.bind('<Button-3>', lambda ev: self.copy_activity(ev,"spot"))

        self.top.spot.grid(row=7, column=0, sticky='NSEW', padx=(10,0), pady=(0,10))
        self.top.acscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.top.spot.yview)
        self.top.spot.configure(yscroll=self.top.acscrollbar.set)
        self.top.acscrollbar.grid(row=7, column=1, sticky='NS', padx=(0,10), pady=(0,10))

        # button(s)
        self.top.expact_button = ttk.Button(self.top, text = 'Export', command = lambda: self.export_keyword_activity(search), width='6')
        self.top.expact_button.grid(row=8, column = 0, padx=8)

        sql = "SELECT * FROM activity WHERE profile_id = ? AND type = ? AND (call LIKE ? OR value LIKE ?) ORDER BY spotdate DESC"
        c.execute(sql,[current_profile_id,"RX.SPOT",'%'+search[2]+'%','%'+search[2]+'%'])
        sactivity_records = c.fetchall()

        count=0
        for record in sactivity_records:
            if count % 2 == 1:
                self.top.spot.insert('', tk.END, iid=record[0], values=(record[5],record[6],record[7]), tags=('oddrow'))
            else:
                self.top.spot.insert('', tk.END, iid=record[0], values=(record[5],record[6],record[7]), tags=('evenrow'))
            count+=1

        # set colors based on theme
        if settings['dark_theme']=='1':
            self.top.activity.tag_configure('oddrow', background='#777')
            self.top.activity.tag_configure('evenrow', background='#555')
            self.top.directed.tag_configure('oddrow', background='#777')
            self.top.directed.tag_configure('evenrow', background='#555')
            self.top.spot.tag_configure('oddrow', background='#777')
            self.top.spot.tag_configure('evenrow', background='#555')
        else:
            self.top.activity.tag_configure('oddrow', background='#EEE')
            self.top.activity.tag_configure('evenrow', background='#FFF')
            self.top.directed.tag_configure('oddrow', background='#EEE')
            self.top.directed.tag_configure('evenrow', background='#FFF')
            self.top.spot.tag_configure('oddrow', background='#EEE')
            self.top.spot.tag_configure('evenrow', background='#FFF')

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def proc_comment(self, kwiid):
        new_comment = self.top.comment.get()
        c.execute("UPDATE search SET comment = '"+str(new_comment)+"' WHERE id = '"+str(kwiid)+"'")
        conn.commit()
        self.refresh_keyword_tree()
        self.top.destroy()

    ## Export all activity from view activity pane
    def export_keyword_activity(self, search):
        self.top2 = Toplevel(self)
        self.top2.title("Export Activity")
        self.top2.geometry('400x500')
        self.top2.minsize(400,500)

        self.exportmark = ttk.Label(self.top2, text="Copy (ctrl+c) / Export Tab-delimited Activity")
        self.exportmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save and copy buttons
        tlframe = ttk.Frame(self.top2)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
        self.copy_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
        self.saveas_button.pack(side=RIGHT)

        # text export window
        self.export_text = Text(self.top2, wrap=NONE)
        export_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscroll=export_scrollbar.set)
        export_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        # right-click action
        self.rcmenu = Menu(self.top2, tearoff = 0)
        self.rcmenu.add_command(label = 'Copy')
        self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

        sql = "SELECT * FROM activity WHERE profile_id = ? AND (call LIKE ? OR value LIKE ?) ORDER BY spotdate DESC"
        c.execute(sql,[current_profile_id,'%'+search[2]+'%','%'+search[2]+'%'])
        export_kw_records = c.fetchall()

        for record in export_kw_records:
            insert_rec = record[2]+"\t"+record[3]+"\t"+record[4]+"\t"+record[5]+"\t"+record[6]+"\t"+record[7]+"\n"
            self.export_text.insert(tk.END, insert_rec)

        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Display a maidenhead grid map with SPOT locations
    def grid_map(self):
        global map_loc, totals

        totals[0]=0
        self.update_statusbar()

        self.top = Toplevel(self)
        self.top.title("Grid Location Map")
        self.top.geometry('1170x465')
        self.top.resizable(width=False, height=False)

        # callsign GRID treeview
        self.top.gridcall = ttk.Treeview(self.top, show='headings', style='keywords.Treeview')
        self.top.gridcall["columns"]=("call","grid","snr","last_seen")

        self.top.gridcall.column("call", width=55, minwidth=55)
        self.top.gridcall.column("grid", width=40, minwidth=40)
        self.top.gridcall.column("snr", width=35, minwidth=35, stretch=0)
        self.top.gridcall.column("last_seen", width=145, minwidth=145, stretch=0)

        self.top.gridcall.heading("call", text="Call", command=lambda c="call": self.sort_treeview(self.top.gridcall, c, False))
        self.top.gridcall.heading("grid", text="Grid", command=lambda c="grid": self.sort_treeview(self.top.gridcall, c, False))
        self.top.gridcall.heading("snr", text="SNR", command=lambda c="snr": self.sort_treeview(self.top.gridcall, c, False))
        self.top.gridcall.heading("last_seen", text="Last Seen", command=lambda c="last_seen": self.sort_treeview(self.top.gridcall, c, False))

        self.top.gridcall.bind('<Return>', self.highlight_grid)
        self.top.gridcall.bind('<Double-1>', self.highlight_grid)
        self.top.gridcall.bind('<Delete>', self.delete_grid)
        self.top.gridcall.bind('<Button-3>', self.delete_grid)
        self.top.gridcall.grid(row=0, column=1, sticky='NSEW', padx=(10,0), pady=(10,0))

        self.top.gcscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.top.gridcall.yview)
        self.top.gridcall.configure(yscroll=self.top.gcscrollbar.set)
        self.top.gcscrollbar.grid(row=0, column=2, sticky='NS', padx=(0,0), pady=(10,0))
        self.top.gridcall.tag_configure('notshown', foreground='gray')

        # map frame
        self.top.map = ttk.Frame(self.top)
        self.top.canvas = Canvas(self.top.map, width=806, height=406)
        self.top.map.grid(row=0,column=0, padx=(10,0), pady=(10,0))
        self.top.canvas.bind('<Button-1>', self.mapzoom)

        # left side buttons/selects/entry
        left_buttons = ttk.Frame(self.top)
        left_buttons.grid(row=1, column=0, sticky='W', padx=(8,8), pady=(8,8))

        # status info box for highlighted marker
        self.top.grid_status = ttk.Entry(left_buttons, width = '50')
        self.top.grid_status.grid(row=0, column=0, sticky='W')

        # map select
        self.top.maploc = ttk.Combobox(left_buttons, values=maplocs, state='readonly', width='15')
        self.top.maploc.grid(row=0, column=1, sticky='W', padx=(8,0))
        self.top.maploc.current(map_loc)
        self.top.maploc.bind('<<ComboboxSelected>>', self.maploc_sel_combo)

        # highlight type select (time or snr)
        self.top.hlmode = ttk.Combobox(left_buttons, values=["Age","SNR"], state='readonly', width='10')
        self.top.hlmode.grid(row=0, column=2, padx=(8,0))
        self.top.hlmode.current(settings['marker_hlmode'])
        self.top.hlmode.bind('<<ComboboxSelected>>', self.markerhlmode_sel_combo)


        # right size buttons/selects
        right_buttons = ttk.Frame(self.top)
        right_buttons.grid(row=1, column=1, sticky='W', padx=(8,8), pady=(8,8))

        # show marker count select
        self.top.markershow = ttk.Combobox(right_buttons, values=["Latest 100", "Latest 50", "Latest 25", "Latest 10"], state='readonly', width='12')
        self.top.markershow.grid(row=0, column=0, padx=(0,0), pady=(0,0))
        self.top.markershow.current(settings['marker_index'])
        self.top.markershow.bind('<<ComboboxSelected>>', self.markershow_sel_combo)

        # clear button
        self.top.grid_clearbtn = ttk.Button(right_buttons, text = 'Clear List', command = self.clear_grid)
        self.top.grid_clearbtn.grid(row=0, column=1, padx=(10,0), pady=0)

        self.top.grid_exportbtn = ttk.Button(right_buttons, text = 'Export', command = self.export_grid)
        self.top.grid_exportbtn.grid(row=0, column=2, padx=(10,0), pady=0)

        self.top.canvas.pack()
        self.update_grid()

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Select which map to display
    def maploc_sel_combo(self, ev):
        global map_loc
        map_loc = self.top.maploc.current()
        self.update_grid()

    ## Show n markers on map
    def markershow_sel_combo(self, ev):
        global settings
        settings['marker_index'] = str(self.top.markershow.current())
        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['marker_index']+"' WHERE name = 'marker_index'")
        conn.commit()
        self.update_grid()

    ## Marker highlight color mode
    def markerhlmode_sel_combo(self, ev):
        global settings
        settings['marker_hlmode'] = str(self.top.hlmode.current())
        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['marker_hlmode']+"' WHERE name = 'marker_hlmode'")
        conn.commit()
        self.update_grid()

    ## Map zoom (quadrants)
    def mapzoom(self, ev):
        global map_zoom

        if map_zoom==0:
            if ev.x<403 and ev.y<203: map_zoom=1
            if ev.x>402 and ev.y<203: map_zoom=2
            if ev.x<403 and ev.y>202: map_zoom=3
            if ev.x>402 and ev.y>203: map_zoom=4
        else:
            map_zoom=0

        self.update_grid()

    ## Update/refresh map and markers
    def update_grid(self):
        # preserve focus after refresh
        gciid=""
        if self.top.gridcall.focus(): gciid = self.top.gridcall.focus()

        if settings['marker_index']=='0': dispcount=100
        if settings['marker_index']=='1': dispcount=50
        if settings['marker_index']=='2': dispcount=25
        if settings['marker_index']=='3': dispcount=10

        # clear out and rebuild
        self.top.canvas.delete('all')

        for entry in self.top.gridcall.get_children():
            self.top.gridcall.delete(entry)

        if map_loc == 0:
                if map_zoom==0:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_NA-map.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_NA-labels.png'))
                else:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/NA_Quad/Maidenhead_NA-map-'+str(map_zoom)+'.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/NA_Quad/Maidenhead_NA-labels-'+str(map_zoom)+'.png'))

        if map_loc == 1:
                if map_zoom==0:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_EU-map.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_EU-labels.png'))
                else:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/EU_Quad/Maidenhead_EU-map-'+str(map_zoom)+'.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/EU_Quad/Maidenhead_EU-labels-'+str(map_zoom)+'.png'))

        if map_loc == 2:
                if map_zoom==0:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_AU-map.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_AU-labels.png'))
                else:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/AU_Quad/Maidenhead_AU-map-'+str(map_zoom)+'.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/AU_Quad/Maidenhead_AU-labels-'+str(map_zoom)+'.png'))

        if map_loc == 3:
                if map_zoom==0:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_ID-map.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_ID-labels.png'))
                else:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/ID_Quad/Maidenhead_ID-map-'+str(map_zoom)+'.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/ID_Quad/Maidenhead_ID-labels-'+str(map_zoom)+'.png'))

        if map_loc == 4:
                if map_zoom==0:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_NAF-map.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_NAF-labels.png'))
                else:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/NAF_Quad/Maidenhead_NAF-map-'+str(map_zoom)+'.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/NAF_Quad/Maidenhead_NAF-labels-'+str(map_zoom)+'.png'))

        if map_loc == 5:
                if map_zoom==0:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_SAF-map.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/Maidenhead_SAF-labels.png'))
                else:
                    self.top.mapimg = ImageTk.PhotoImage(Image.open('maps/SAF_Quad/Maidenhead_SAF-map-'+str(map_zoom)+'.png'))
                    self.top.txtimg = ImageTk.PhotoImage(Image.open('maps/SAF_Quad/Maidenhead_SAF-labels-'+str(map_zoom)+'.png'))


        # retrieve newest n records and add to treeview
        c.execute("SELECT * FROM grid WHERE grid_callsign!='' ORDER BY grid_timestamp DESC LIMIT "+str(dispcount))
        grid_records = c.fetchall()

        # Sort by SNR or Age
        if settings['marker_hlmode']=="1":
            grid_records.sort(key=lambda x: x[4]) # weakest to strongest
        else:
            grid_records.sort(key=lambda x: x[5]) # oldest to newest

        count = 0
        for record in grid_records:
            if count<dispcount:
                if count % 2 == 1:
                    self.top.gridcall.insert('', tk.END, iid=record[0], values=(record[0],record[1],record[4],record[5]), tags=('oddrow'))
                else:
                    self.top.gridcall.insert('', tk.END, iid=record[0], values=(record[0],record[1],record[4],record[5]), tags=('evenrow'))
                count+=1

        if settings['dark_theme'] == "1":
            self.top.gridcall.tag_configure('oddrow', background='#777')
            self.top.gridcall.tag_configure('evenrow', background='#555')
        else:
            self.top.gridcall.tag_configure('oddrow', background='#EEE')
            self.top.gridcall.tag_configure('evenrow', background='#FFF')

        # draw background map
        self.top.canvas.create_image(403,203,image=self.top.mapimg)

        # draw markers
        random.seed(100)
        for record in grid_records:
            count+=1

            gridletters = record[1][:2]
            if gridletters in gridmultiplier[map_loc]:
                pxcoords = self.mh2px(record[1])
                pxcoordX = pxcoords[0]
                pxcoordY = pxcoords[1]

                # add some fuzziness to help avoid markers directly overlapping
                pxcoordX = pxcoordX + random.randint(-4, 4)
                pxcoordY = pxcoordY + random.randint(-4, 4)

                marker_size=8

                # adjust for zoom
                if map_zoom > 0:
                    pxcoordX = pxcoordX*2
                    pxcoordY = pxcoordY*2
                    marker_size=16

                if map_zoom==2:
                    pxcoordX-=806
                if map_zoom==3:
                    pxcoordY-=406
                if map_zoom==4:
                    pxcoordX-=806
                    pxcoordY-=406

                if settings['marker_hlmode']=="1":
                    snrval=int(record[4])

                    # 8 colors/levels loaded from maps.pal file in maps folder
                    fcolor = mappal[7] # Default color for anything less than -26dB
                    if snrval > -22: fcolor = mappal[6]
                    if snrval > -18: fcolor = mappal[5]
                    if snrval > -15: fcolor = mappal[4]
                    if snrval > -10:  fcolor = mappal[3]
                    if snrval > -5:   fcolor = mappal[2]
                    if snrval > 1:   fcolor = mappal[1]
                    if snrval > 5:  fcolor = mappal[0]
                    self.top.canvas.create_oval(pxcoordX,pxcoordY,pxcoordX+marker_size,pxcoordY+marker_size, fill=fcolor, outline='black')
                else:
#                    recdelta = datetime.datetime.utcnow() - datetime.datetime.strptime(record[5], "%Y-%m-%d %H:%M:%S") # depricated utcnow
                    recdelta = datetime.datetime.now(datetime.UTC) - datetime.datetime.strptime(record[5], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
                    rechrs = int(recdelta.total_seconds() / 60 / 60)

                    fcolor = mappal[7]
                    if rechrs < 24 : fcolor = mappal[6]
                    if rechrs < 12: fcolor = mappal[5]
                    if rechrs < 10: fcolor = mappal[4]
                    if rechrs < 8: fcolor = mappal[3]
                    if rechrs < 6: fcolor = mappal[2]
                    if rechrs < 4: fcolor = mappal[1]
                    if rechrs < 2: fcolor = mappal[0]

                    self.top.canvas.create_rectangle(pxcoordX,pxcoordY,pxcoordX+marker_size,pxcoordY+marker_size, fill=fcolor, outline='black')

        # draw legend
        if settings['marker_hlmode']=="1":
            for i in range(8):
                x=10+(i*10)
                self.top.canvas.create_oval(x,390,x+8,398, fill=mappal[i], outline='black')
            self.top.canvas.create_text(50, 380, text="Strong -> Weak", font=("TkFixedFont", "8"), fill="#333333")
        else:
            for i in range(8):
                x=10+(i*10)
                self.top.canvas.create_rectangle(x,390,x+8,398, fill=mappal[i], outline='black')
            self.top.canvas.create_text(50, 380, text="Newer -> Older", font=("TkFixedFont", "8"), fill="#333333")

        # draw triangle marker for user grid location
        usercoords = self.mh2px(settings['grid'])
        userX = usercoords[0]
        userY = usercoords[1]

        marker_size=4
        # adjust for zoom
        if map_zoom > 0:
            userX = userX*2
            userY = userY*2
            marker_size=8

        if map_zoom==2:
            userX-=806
        if map_zoom==3:
            userY-=406
        if map_zoom==4:
            userX-=806
            userY-=406

        if userX>0 and userY>0:
            self.top.canvas.create_polygon([userX,userY+marker_size,userX+marker_size,userY-marker_size,userX+marker_size*2,userY+marker_size], outline='red', fill='#0000FF')

        # draw grid text overlay
        self.top.canvas.create_image(403,203,image=self.top.txtimg)

        if settings['marker_hlmode']=="1":
            self.sort_treeview(self.top.gridcall, "snr", True)
        else:
            self.sort_treeview(self.top.gridcall, "last_seen", True)

        # restore focus
        if gciid != "":
            if self.top.gridcall.exists(gciid) == True:
                self.top.gridcall.focus(gciid)
                self.top.gridcall.selection_set(gciid)

    ## Highlight GRID marker
    def highlight_grid(self, ev):
        if not self.top.gridcall.focus(): return
        gciid = self.top.gridcall.focus()

        self.update_grid()
        c.execute("SELECT * FROM grid WHERE grid_callsign = ?", [gciid])
        record = c.fetchone()

        usercoords = self.mh2px(settings['grid'])
        userX = usercoords[0]
        userY = usercoords[1]

        # adjust for zoom
        if map_zoom > 0:
            userX = userX*2
            userY = userY*2

        if map_zoom==2:
            userX-=806
        if map_zoom==3:
            userY-=406
        if map_zoom==4:
            userX-=806
            userY-=406

        gridletters = record[1][:2]
        if gridletters in gridmultiplier[map_loc]:
            pxcoords = self.mh2px(record[1])
            pxcoordX = pxcoords[0]
            pxcoordY = pxcoords[1]

            # adjust for zoom
            if map_zoom > 0:
                pxcoordX = pxcoordX*2
                pxcoordY = pxcoordY*2
                marker_size=16

            if map_zoom==2:
                pxcoordX-=806
            if map_zoom==3:
                pxcoordY-=406
            if map_zoom==4:
                pxcoordX-=806
                pxcoordY-=406

            if userX>0 and userY>0:
                self.top.canvas.create_line(pxcoordX+3,pxcoordY+3,userX+3,userY+3,fill='#000000', width='2')
#            self.top.canvas.create_oval(pxcoordX-4,pxcoordY-4,pxcoordX+12,pxcoordY+12, outline='blue', width='1')

        # update status info
        self.top.grid_status.delete(0,END)
        self.top.grid_status.insert(0,record[0]+", "+record[1]+", "+record[2]+", "+record[4]+"dB, "+record[5])

    ## Maidenhead to pixels
    def mh2px(self,mhtxt):
        global map_loc
        # convert GRID to pixel coords

        gridletters = mhtxt[:2]
        gridnum1 = mhtxt[2]
        gridnum2 = mhtxt[3]
        pxcoordX=-1 # returns if not found on selected map
        pxcoordY=-1

        if gridletters in gridmultiplier[map_loc]:
            pxcoordX = (gridmultiplier[map_loc][gridletters][0]*200)+(int(gridnum1)*20)+10
            pxcoordY = (400-((gridmultiplier[map_loc][gridletters][1]*100)+(int(gridnum2)*10)))-5
        rpx=[pxcoordX,pxcoordY]
        return rpx

    ## Delete item from grid map list
    def delete_grid(self, ev):
        if not self.top.gridcall.focus(): return
        gciid = self.top.gridcall.focus()

        answer = askyesno(title="Remove Map Record?", message="This will delete "+gciid+" from the map database. Continue?", parent=self.top)
        if answer:
            c.execute("DELETE FROM grid WHERE grid_callsign = ?", [gciid])
            conn.commit()
            self.update_grid()

    ## Delete ALL items from grid map list
    def clear_grid(self):

        answer = askyesno(title="Clear All Grids?", message="This will delete ALL callsign grids from the map database. Continue?", parent=self.top)
        if answer:
            c.execute("DELETE FROM grid")
            conn.commit()
            self.update_grid()

    def export_grid(self):
        self.expgridTop = Toplevel(self)
        self.expgridTop.title("Export Grid Entries")
        self.expgridTop.geometry('400x500')
        self.expgridTop.minsize(400,500)

        self.exportmark = ttk.Label(self.expgridTop, text="Copy (ctrl+c) / Export Tab-delimited Data")
        self.exportmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save and copy buttons
        tlframe = ttk.Frame(self.expgridTop)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
        self.copy_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
        self.saveas_button.pack(side=RIGHT)

        # text export window
        self.export_text = Text(self.expgridTop, wrap=NONE)
        export_scrollbar = ttk.Scrollbar(self.expgridTop, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscroll=export_scrollbar.set)
        export_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        # right-click action
        self.rcmenu = Menu(self.expgridTop, tearoff = 0)
        self.rcmenu.add_command(label = 'Copy')
        self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

        c.execute("SELECT * FROM grid ORDER BY grid_timestamp DESC")
        export_exp_records = c.fetchall()

        for record in export_exp_records:
            if record[0]!="":
                insert_rec = record[0]+"\t"+record[1]+"\t"+record[2]+"\t"+str(record[4])+"\t"+str(record[5])+"\n"
                self.export_text.insert(tk.END, insert_rec)

        self.expgridTop.wait_visibility()
        self.expgridTop.grab_set()
        self.expgridTop.focus_set()
        self.expgridTop.bind('<Escape>', lambda x: self.expgridTop.destroy())

    ## Display a simulated waterfall with visualization of recent band activity
    def visualize_waterfall(self):

        wfbands = ["80m - 3.578.000","40m - 7.078.000","30m - 10.130.000","20m - 14.078.000","17m - 18.104.000","15 - 21.078.000","12m - 24.922.000","10m - 28.078.000"]
        wftimes = ["Last 5 minutes","Last 30 minutes","Last 1 hour","Last 2 hours", "Last 4 hours", "Last 8 hours", "Last 12 hours", "Last 24 hours", "Last 72 hours", "Last 7 days"]

        self.top = Toplevel(self)
        self.top.title("Visualize Waterfall Activity")
        self.top.geometry('1157x300')
        self.top.resizable(width=False, height=False)

        # background waterfall image
        self.top.wf = ttk.Frame(self.top)
        self.top.canvas = Canvas(self.top.wf, width=1137, height=239)
        self.top.wf.grid(row=0,column=0, padx=(10,10), pady=(10,0))

        # options frame
        self.top.opts = ttk.Frame(self.top)
        self.top.opts.grid(row=1,column=0, padx=(10,10), pady=(0,10))

        # dial / band select
        self.top.wfband = ttk.Combobox(self.top.opts, values=wfbands, state='readonly', width='18')
        self.top.wfband.grid(row=0, column =0, sticky='NE', padx=(10,10), pady=(10,0))
        self.top.wfband.current(settings['wfband_index'])
        self.top.wfband.bind('<<ComboboxSelected>>', self.wfband_sel_combo)

        # manually enter frequency
        self.top.manfreq = ttk.Entry(self.top.opts, width = '10')
        self.top.manfreq.grid(row=0, column=1, sticky='NE', padx=(0,10), pady=(10,0))
        self.top.freqgo = ttk.Button(self.top.opts, text = "Set", command=lambda s="": self.update_simwf(s))
        self.top.freqgo.grid(row=0, column = 2, sticky='NE', padx=(0,20), pady=(10,10))
        self.top.manfreq.insert(0, wfbandshz[int(settings['wfband_index'])])

        # time select
        self.top.wftime = ttk.Combobox(self.top.opts, values=wftimes, state='readonly', width='14')
        self.top.wftime.grid(row=0, column =3, sticky='NE', padx=(10,10), pady=(10,0))
        self.top.wftime.current(settings['wftime_index'])
        self.top.wftime.bind('<<ComboboxSelected>>', self.wftime_sel_combo)

        # search button
        self.top.search_button = ttk.Button(self.top.opts, text = "Search", command = self.simwfsearch)
        self.top.search_button.grid(row=0, column = 4, sticky='NE', padx=(10,10), pady=(10,10))

        self.top.canvas.pack()
        self.update_simwf("")
        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Select band visual to display on sim waterfall
    def wfband_sel_combo(self, ev):
        global settings
        settings['wfband_index'] = str(self.top.wfband.current())

        self.top.manfreq.delete(0,END)
        self.top.manfreq.insert(0, wfbandshz[int(settings['wfband_index'])])

        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['wfband_index']+"' WHERE name = 'wfband_index'")
        conn.commit()
        self.update_simwf("")

    ## Select timeframe for sim waterfall
    def wftime_sel_combo(self, ev):
        global settings
        settings['wftime_index'] = str(self.top.wftime.current())
        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['wftime_index']+"' WHERE name = 'wftime_index'")
        conn.commit()
        self.update_simwf("")

    ## Search the signal table and limit the simulated waterfall to specific callsign(s)
    def simwfsearch(self):
        self.top2 = Toplevel(self)
        self.top2.title("Search for Signals by Callsign(s)")
        self.top2.geometry('400x500')
        self.top2.minsize(400,500)

        self.addbatmark = ttk.Label(self.top2, text="Type or paste (ctrl+v) callsigns, one per line")
        self.addbatmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save button
        tlframe = ttk.Frame(self.top2)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.save_button = ttk.Button(tlframe, text = 'Search', command = self.proc_simwfsearch)
        self.save_button.pack(side=LEFT, padx=(0,10))

        # text window
        self.batchcs = Text(self.top2, wrap=NONE)
        batch_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.batchcs.yview)
        self.batchcs.configure(yscroll=batch_scrollbar.set)
        batch_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.batchcs.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Process simulated wf callsign search
    def proc_simwfsearch(self):
        batch_values = StringIO(self.batchcs.get('1.0','end'))
        search = ""
        for line in batch_values:
            new_cslist = line.rstrip().upper()
            if new_cslist == "": continue
            if search == "":
                search = " AND (sig_callsign='"+new_cslist+"'"
            else:
                search = search + " OR sig_callsign='"+new_cslist+"' "
        if search != "":
            search = search + ")"
            self.update_simwf(search)

        self.top2.destroy()

    ## Update band activity on simulated waterfall
    def update_simwf(self,search):
        # clear out and rebuild
        self.top.canvas.delete('all')

        # draw background
        self.top.mapimg = ImageTk.PhotoImage(Image.open('waterfall.png'))
        self.top.canvas.create_image(569,120,image=self.top.mapimg)

        wftimesel = self.top.wftime.current()
        wffreq = self.top.manfreq.get()

        # get info from db based on selections
        wftimes = ["-5 minute","-30 minute","-1 hour","-2 hour","-4 hour","-8 hour","-12 hour","-24 hour", "-72 hour", "-7 day"]
        wftimes2 =["-0 minute","-5 minute","-30 minute","-1 hour","-2 hour","-4 hour","-8 hour","-12 hour", "-24 hour", "-72 hour"]

        # We want to iterate over date ranges in reverse, so the newest signals are layered over the oldest
        for i in range(wftimesel+1, 0, -1):
            c.execute("SELECT * FROM signal WHERE sig_offset<>'' AND sig_speed<>'' AND (sig_timestamp BETWEEN DATETIME('now', '"+wftimes[i-1]+"') AND DATETIME('now', '"+wftimes2[i-1]+"' )) AND sig_dial = '"+wffreq+"' "+search+" ORDER BY sig_freq ASC")
            wf_records = c.fetchall()

            for record in wf_records:
                # calculate location on wf and size
                # * png is 1137px to display 2500hz, so signals adjust to 45.4%
                # * signal display starts at 500hz, so that must be subtracted (adjusted to 45.4%)
                sx=int(record[4])*.454 - (500*.454)

                if record[5]=="0": # normal mode
                    w=22
                    h=42
                    sy=29
                if record[5]=="1": # fast mode
                    w=35
                    h=22
                    sy=90
                if record[5]=="2": # JS8 40 mode
                    w=70
                    h=11
                    sy=145
                if record[5]=="4": # slow mode
                    w=11
                    h=78
                    sy=162
                if record[5]=="16": # subspace mode: 150Hz bandwidth; lane sits between Turbo and Slow on the waterfall PNG
                    w=66
                    h=8
                    sy=192

                if i==1: scolor="#FF0000"
                if i==2: scolor="#D51125"
                if i==3: scolor="#BB1144"
                if i==4: scolor="#991166"
                if i==5: scolor="#771188"
                if i==6: scolor="#5511AA"
                if i==7: scolor="#3311CC"
                if i==8: scolor="#333333"
                if i==9: scolor="#333333"
                if i==10: scolor="#333333"

                # draw simulated signal placeholder on wf background
                self.top.canvas.create_rectangle(sx,sy,sx+w,sy+h, fill=scolor, width='0', stipple="gray50")

                # display callsigns over signals, when search is used
                if search != "":
                    self.top.canvas.create_text(sx, sy+h+5, anchor="nw", angle=90, fill="#FFFFFF", text=record[1])

        if search != "":
            messagebox.showinfo("Search Results","Only displaying signals for searched callsign(s). Change band, timeframe, or reload simulated waterfall to show all.", parent=self.top)

    ## Simple database search mechanism
    def database_search(self):
        self.top = Toplevel(self)
        self.top.title("Database Search")
        self.top.resizable(width=False, height=False)

        label_ds = ttk.Label(self.top, text = "Select a table and enter a search string")
        label_ds.grid(row=0, column=0, padx=(10,0), pady=(20,0))

        dbtabs = ["activity", "expect", "forms", "grid", "signal"]
        self.dbsel = ttk.Combobox(self.top, values=dbtabs, state='readonly', width='15')
        self.dbsel.grid(row=1, columnspan=2, sticky='NSEW', padx=(10,10), pady=(10,0))
        self.dbsel.current(0)

        self.edit_ds = ttk.Entry(self.top)
        self.edit_ds.grid(row=2, columnspan=2, sticky='NSEW', padx=(10,10), pady=(20,0))
        self.edit_ds.bind("<Return>", lambda x: self.proc_dbsearch())

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=3, columnspan=2, sticky='NSEW', padx=10)

        search_button = ttk.Button(cbframe, text = "Search", command = self.proc_dbsearch)
        search_button.grid(row=0, column = 0, padx=(20,20), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 1, padx=(0,20), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.edit_ds.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def proc_dbsearch(self):
        dbtable = self.dbsel.get()
        searchstring = self.edit_ds.get()

        if searchstring == "":
            messagebox.showinfo("No search text entered","Please enter search text to continue.")
            return

        self.top2 = Toplevel(self)
        self.top2.title("Search results for "+dbtable+" table")
        self.top2.geometry('650x500')

        self.dbsmark = ttk.Label(self.top2, text="Tab-delimited results for table:"+dbtable)
        self.dbsmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save and copy buttons
        tlframe = ttk.Frame(self.top2)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
        self.copy_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
        self.saveas_button.pack(side=RIGHT)

        # text window
        self.export_text = Text(self.top2, wrap=NONE)
        dbs_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscroll=dbs_scrollbar.set)
        dbs_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        # right-click action
        self.rcmenu = Menu(self.top2, tearoff = 0)
        self.rcmenu.add_command(label = 'Copy')
        self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

        dbs_sql=""
        if dbtable=="activity":
            dbs_sql="SELECT * FROM activity WHERE (type LIKE '%"+searchstring+"%' OR value LIKE '%"+searchstring+"%' OR call LIKE '%"+searchstring+"%') ORDER BY spotdate DESC"

        if dbtable=="expect":
            dbs_sql="SELECT * FROM expect WHERE (expect LIKE '%"+searchstring+"%' OR reply LIKE '%"+searchstring+"%' OR allowed LIKE '%"+searchstring+"%' OR txlist LIKE '%"+searchstring+"%') ORDER BY lm DESC"

        if dbtable=="forms":
            dbs_sql="SELECT * FROM forms WHERE (fromcall LIKE '%"+searchstring+"%' OR tocall LIKE '%"+searchstring+"%' OR typeid LIKE '%"+searchstring+"%' OR responses LIKE '%"+searchstring+"%'  OR msgtxt LIKE '%"+searchstring+"%' OR timesig LIKE '%"+searchstring+"%' ) ORDER BY lm DESC"

        if dbtable=="grid":
            dbs_sql="SELECT * FROM grid WHERE (grid_callsign LIKE '%"+searchstring+"%' OR grid_grid LIKE '%"+searchstring+"%' OR grid_dial LIKE '%"+searchstring+"%') ORDER BY grid_timestamp DESC"

        if dbtable=="signal":
            dbs_sql="SELECT * FROM signal WHERE (sig_callsign LIKE '%"+searchstring+"%' OR sig_dial LIKE '%"+searchstring+"%' OR sig_freq LIKE '%"+searchstring+"%' OR sig_offset LIKE '%"+searchstring+"%') ORDER BY sig_timestamp DESC"

        if dbs_sql:
            c.execute(dbs_sql)
            dbsearch_results = c.fetchall()
            for record in dbsearch_results:
                dbs_res = "\t".join(map(str, record))+"\n"
                self.export_text.insert(tk.END, dbs_res)

        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Expect subsystem main window
    def expect(self):
        global totals

        totals[1]=0
        totals[4]=0
        self.update_statusbar()

        if settings['pause_expect'] == "1":
            messagebox.showinfo("Expect System Paused","The Expect System is currently PAUSED, and no replies will be transmitted. To unpause, use the Tools menu. You may edit Expect items as normal.")

        if settings['pause_autotx'] == "1":
            messagebox.showinfo("Expect Auto TX Paused","Expect Auto TX is currently PAUSED, and there will be no auto transmissions. To unpause, use the Tools menu. You may edit Expect items as normal.")

        self.top = Toplevel(self)
        self.top.title("Expect Auto-Reply Subsystem")
        self.top.geometry('1120x465')
        self.top.minsize(1120,465)
        self.top.resizable(width=True, height=True)

        self.top.columnconfigure(0, weight=24)
        self.top.columnconfigure(1, weight=1)

        self.top.rowconfigure(0,weight=24)
        self.top.rowconfigure(1,weight=1)

        # expect treeview
        self.expect = ttk.Treeview(self.top, show='headings', selectmode="browse")
        self.expect["columns"]=("expect","reply","allowed","autotx","txlist","txmax","lm")
        self.expect.tag_configure('max', background='red')

        self.expect.column("expect", width=70, minwidth=70, stretch=0)
        self.expect.column("reply", width=240, minwidth=240)
        self.expect.column("allowed", width=143, minwidth=143)
        self.expect.column("autotx", width=142, minwidth=142)
        self.expect.column("txlist", width=195, minwidth=195)
        self.expect.column("txmax", width=195, minwidth=60)
        self.expect.column("lm", width=90, minwidth=90, stretch=0)

        self.expect.heading("expect", text="Expect")
        self.expect.heading("reply", text="Response")
        self.expect.heading("allowed", text="Allowed Calls/Groups")
        self.expect.heading("autotx", text="Auto TX")
        self.expect.heading("txlist", text="Sent To")
        self.expect.heading("txmax", text="Count")
        self.expect.heading("lm", text="Created")

        self.expect.bind('<Return>', self.show_expect)
        self.expect.bind('<Double-1>', self.show_expect)
        self.expect.bind('<Delete>', self.delete_expect)
        self.expect.bind('<Button-2>',  lambda event: self.tx_expect())
        self.expect.bind('<Button-3>',  lambda event: self.tx_expect())
        self.expect.grid(row=0, column=0, sticky='NSEW', padx=(10,0), pady=(10,5))

        self.gcscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.expect.yview)
        self.expect.configure(yscroll=self.gcscrollbar.set)
        self.gcscrollbar.grid(row=0, column=1, sticky='NS', padx=(0,10), pady=(10,5))

        # frame with import & export buttons
        self.ieframe = ttk.Frame(self.top)
        self.ieframe.grid(row=1, column=0, sticky='NSE')

        self.importexp = ttk.Button(self.ieframe, text = 'Import', command = self.import_expect, width='7')
        self.importexp.grid(row=0, column=1, sticky='NE', padx=(8,0),pady=(0,0))
        self.exportexp = ttk.Button(self.ieframe, text = 'Export', command = self.export_expect, width='7')
        self.exportexp.grid(row=0, column=2, sticky='NE', padx=(8,0),pady=(0,0))

        self.sendexp = ttk.Button(self.ieframe, text = 'Send Now',command = self.tx_expect, width='10')
        self.sendexp.grid(row=0, column=3, sticky='NE', padx=(40,0),pady=(0,0))

        self.addexp = ttk.Button(self.ieframe, text = 'Add',command = lambda: self.show_expect("new"), width='6')
        self.addexp.grid(row=0, column=4, sticky='NE', padx=(40,0),pady=(0,0))
        self.editexp = ttk.Button(self.ieframe, text = 'Edit',command = lambda: self.show_expect("edit"), width='6')
        self.editexp.grid(row=0, column=5, sticky='NE', padx=(8,0),pady=(0,0))
        self.delexp = ttk.Button(self.ieframe, text = 'Delete', command = lambda: self.delete_expect(""), width='8')
        self.delexp.grid(row=0, column=6, sticky='NE', padx=(8,0),pady=(0,0))

        self.update_expect()
        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def pause_expect(self):
        global settings
        if settings['pause_expect'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'pause_expect'")
            settings['pause_expect'] = "0"
            self.toolsmenu.entryconfigure(4, label="Expect - Pause Replies")
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'pause_expect'")
            settings['pause_expect'] = "1"
            self.toolsmenu.entryconfigure(4, label="\u2713 Expect - Pause Replies")
        conn.commit()
        self.update_statusbar()

    def pause_autotx(self):
        global settings
        if settings['pause_autotx'] == "1":
            c.execute("UPDATE setting SET value = '0' WHERE name = 'pause_autotx'")
            settings['pause_autotx'] = "0"
            self.toolsmenu.entryconfigure(5, label="Expect - Pause Auto TX")
        else:
            c.execute("UPDATE setting SET value = '1' WHERE name = 'pause_autotx'")
            settings['pause_autotx'] = "1"
            self.toolsmenu.entryconfigure(5, label="\u2713 Expect - Pause Auto TX")
        conn.commit()
        self.update_statusbar()

    def expect_blocklist(self):
        global settings

        self.top = Toplevel(self)
        self.top.title("Expect Blocklist")
        self.top.resizable(width=False, height=False)

        label_bl = ttk.Label(self.top, text = "Callsigns to block, comma separated")
        label_bl.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.edit_bl = ttk.Entry(self.top)
        self.edit_bl.insert(0, settings['expect_blocklist'])
        self.edit_bl.grid(row = 1, columnspan=2, sticky='NSEW', padx=(10,10), pady=(20,0))
        self.edit_bl.bind("<Return>", lambda x: self.proc_blocklist())

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=2, columnspan=2, sticky='NSEW', padx=10)

        save_button = ttk.Button(cbframe, text = "Save", command = self.proc_blocklist)
        save_button.grid(row=0, column = 0, padx=(20,20), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 1, padx=(0,20), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.edit_bl.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def proc_blocklist(self):
        global settings
        new_val = self.edit_bl.get()
        new_val = new_val.replace(" ", "")
        c.execute("UPDATE setting SET value = ? WHERE name = 'expect_blocklist'", [new_val])
        settings['expect_blocklist'] = new_val
        conn.commit()
        self.top.destroy()

    def import_expect(self):
        self.top2 = Toplevel(self)
        self.top2.title("Import Expect Statements")
        self.top2.geometry('400x500')
        self.top2.minsize(400,500)

        self.addmark = ttk.Label(self.top2, text="Type or paste (ctrl+v) Expect statements, one per line")
        self.addmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save button
        tlframe = ttk.Frame(self.top2)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.save_button = ttk.Button(tlframe, text = 'Import Expect', command = self.proc_importexpect)
        self.save_button.pack(side=LEFT, padx=(0,10))

        # text window
        self.batch = Text(self.top2, wrap=NONE)
        batch_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.batch.yview)
        self.batch.configure(yscroll=batch_scrollbar.set)
        batch_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.batch.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Process added expect statements
    def proc_importexpect(self):
        # sqlite3 database is setup ON CONFLICT REPLACE for unique expect field, no warning/error thrown if they overwrite
        # so we'll ask if they want to proceed
        msgtxt="If any expect statements in your import match existing statements, your existing statements will be replaced by the import. Do you want to continue?"
        answer = askyesno(title='Proceed with import?', message=msgtxt, parent=self.top2)
        if answer:

            batch_values = StringIO(self.batch.get('1.0','end'))

            lerr=0
            lsuc=0
            for line in batch_values:

                # format is EXPECT<tab>RESPONSE<tab>ALLOWED<tab>COUNT
                match_forms = re.search(r"(.*)\t(.*)\t(.*)\t(.*)",line)
                if match_forms:
                    new_expect = re.sub(r'[^A-Z0-9!]','',match_forms[1].upper())
                    new_reply = match_forms[2].upper()
                    new_allowed = match_forms[3].upper()
                    new_allowed = new_allowed.replace(" ", "")
                    new_txmax = re.sub(r'[^0-9]','',match_forms[4])

                    # validate input
                    if new_expect == "" or new_reply == "" or new_allowed == "" or new_txmax == "":
                        lerr+=1
                        continue

                    if new_txmax.isnumeric() == False:
                        lerr+=1
                        return

                    if int(new_txmax) < 1 or int(new_txmax) > 99:
                        lerr+=1
                        return

                    sql = "INSERT INTO expect(expect,reply,allowed,txmax,txlist,lm) VALUES (?,?,?,?,'', CURRENT_TIMESTAMP)"
                    c.execute(sql, [new_expect[0:6],new_reply,new_allowed,new_txmax])
                    conn.commit()
                    lsuc+=1

            if lsuc==0 and lerr==0:
                messagebox.showinfo("Results","No expect statements found. The correct format is EXPECT<tab>RESPONSE<tab>ALLOWED<tab>COUNT<newline>.", parent=self.top2)
            else:
                messagebox.showinfo("Results","Finished with "+str(lsuc)+" statements imported, and "+str(lerr)+" error(s).", parent=self.top2)

            self.get_expects()
            self.top2.destroy()
            self.update_expect()

    def export_expect(self):
        self.top2 = Toplevel(self)
        self.top2.title("Export Expect Entries")
        self.top2.geometry('400x500')
        self.top2.minsize(400,500)

        self.exportmark = ttk.Label(self.top2, text="Copy (ctrl+c) / Export Tab-delimited Expect")
        self.exportmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save and copy buttons
        tlframe = ttk.Frame(self.top2)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
        self.copy_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
        self.saveas_button.pack(side=RIGHT)

        # text export window
        self.export_text = Text(self.top2, wrap=NONE)
        export_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
        self.export_text.configure(yscroll=export_scrollbar.set)
        export_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        # right-click action
        self.rcmenu = Menu(self.top2, tearoff = 0)
        self.rcmenu.add_command(label = 'Copy')
        self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

        c.execute("SELECT * FROM expect ORDER BY lm DESC")
        export_exp_records = c.fetchall()

        for record in export_exp_records:
            insert_rec = record[0]+"\t"+record[1]+"\t"+record[2]+"\t"+str(record[4])+"\n"
            self.export_text.insert(tk.END, insert_rec)

        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Update expect treeview
    def update_expect(self):
        for entry in self.expect.get_children():
            self.expect.delete(entry)

        c.execute("SELECT * FROM expect ORDER BY lm DESC")
        expect_lines = c.fetchall()

        count = 0
        for record in expect_lines:
            reply_count=len(record[3].split(","))-1
            max_replies = record[4]
            if max_replies==99:
                has_replies = "\u221e"
            else:
                has_replies = str(max_replies)
            reply_max = str(reply_count)+"/"+has_replies
            ex_date = record[5].split(" ")[0]
            autotx_times = record[7]
            if autotx_times==None: autotx_times = ""

            if count % 2 == 1:
                self.expect.insert('', tk.END, iid=record[0], values=(record[0],record[1],record[2],autotx_times,record[3],reply_max,ex_date), tags=('oddrow'))
            else:
                self.expect.insert('', tk.END, iid=record[0], values=(record[0],record[1],record[2],autotx_times,record[3],reply_max,ex_date), tags=('evenrow'))

            count+=1
            if reply_count>=record[4] and max_replies<99: self.expect.item(record[0], tags=('max'))

        if settings['dark_theme'] == "1":
            self.expect.tag_configure('oddrow', background='#777')
            self.expect.tag_configure('evenrow', background='#555')
        else:
            self.expect.tag_configure('oddrow', background='#EEE')
            self.expect.tag_configure('evenrow', background='#FFF')

    ## Add or Edit an expect entry
    def show_expect(self, ev):
        win_title="Add Expect Entry"
        is_new=1

        # if they are editing an existing item, get the details from the database
        if self.expect.focus() and ev!="new":
            exiid = self.expect.focus()
            c.execute("SELECT * FROM expect WHERE expect = ?", [exiid])
            record = c.fetchone()

            if record:
                win_title = "Edit Expect Entry for "+record[0]
                is_new=0
            else:
                return

        if ev=="edit" and is_new==1:
            messagebox.showinfo("Error","Please select an entry to edit.", parent=self.top)
            return

        self.top2 = Toplevel(self)
        self.top2.geometry('830x325')
        self.top2.title(win_title)
        self.top2.resizable(width=False, height=False)

        # Left side inputs
        el = ttk.Frame(self.top2)
        el.grid(row=0, column=0, sticky='NSEW', padx=10)

        self.top2.lbl1 = ttk.Label(el, text='Text to Expect (6):')
        self.top2.lbl1.grid(row=0, column = 0, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_expect = ttk.Entry(el, width = '14')
        self.top2.entry_expect.grid(row=0, column=1, sticky='NW', padx=(8,0), pady=(8,0))

        self.top2.lbl2 = ttk.Label(el, text='Text to Respond With:')
        self.top2.lbl2.grid(row=1, column = 0, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_reply = ttk.Entry(el, width = '40')
        self.top2.entry_reply.grid(row=1, column=1, sticky='NW', padx=(8,0), pady=(8,0))

        self.top2.lbl3 = ttk.Label(el, text='Allowed Callsigns/Groups:')
        self.top2.lbl3.grid(row=2, column = 0, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_allowed = ttk.Entry(el, width = '30')
        self.top2.entry_allowed.insert(0, settings['exp_def_allow'])
        self.top2.entry_allowed.grid(row=2, column=1, sticky='NW', padx=(8,0), pady=(8,0))

        self.top2.lbl4 = ttk.Label(el, text='Max Replies:\n(0-99, 0=disabled, 99=unlimited)')
        self.top2.lbl4.grid(row=3, column = 0, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_txmax = ttk.Entry(el, width = '8')
        self.top2.entry_txmax.grid(row=3, column=1, sticky='NW', padx=(8,0), pady=(8,0))

        speedopts = ["Current", "Slow", "Normal", "Fast", "JS8 40", "JS8 60", "Subspace"]
        label_speed = ttk.Label(el, text = "TX Speed:")
        label_speed.grid(row = 4, column = 0, sticky=W, padx=(8,0), pady=(8,0))
        self.top2.entry_speed = ttk.Combobox(el, values=speedopts, state='readonly', width='16')
        self.top2.entry_speed.grid(row = 4, column = 1, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_speed.set("Normal")

        self.top2.lbl5 = ttk.Label(el, text="Auto TX Schedule:\n(HH:MM comma separated, "+str(atx_limit)+" max)")
        self.top2.lbl5.grid(row=5, column = 0, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_autotx = ttk.Entry(el, width = '30')
        self.top2.entry_autotx.grid(row=5, column=1, sticky='NW', padx=(8,0), pady=(8,0))

        self.top2.lbl6 = ttk.Label(el, text='Auto TX Target:\n(callsign or group)')
        self.top2.lbl6.grid(row=6, column = 0, sticky='NW', padx=(8,0), pady=(8,0))
        self.top2.entry_atx_target = ttk.Entry(el, width = '30')
        self.top2.entry_atx_target.grid(row=6, column=1, sticky='NW', padx=(8,0), pady=(8,0))

        elbtns = ttk.Frame(el)
        elbtns.grid(row=7, columnspan=2, sticky='NSEW', padx=10)

        self.top2.save = ttk.Button(elbtns, text = 'Save', command = self.save_expect, width='5')
        self.top2.save.grid(row=0, column=0, sticky='NW', padx=(8,0),pady=(8,0))
        self.top2.cancel = ttk.Button(elbtns, text = 'Cancel', command = self.top2.destroy, width='6')
        self.top2.cancel.grid(row=0, column=1, sticky='NW', padx=(8,8),pady=(8,0))
#        self.top2.sendnow = ttk.Button(elbtns, text = 'Send Now', command = self.tx_expect, width='12')
#        self.top2.sendnow.grid(row=0, column=2, sticky='NW', padx=(20,0),pady=(8,0))

        # Right-hand activity log section
        er = ttk.Frame(self.top2)
        er.grid(row=0, column=1, sticky='NSEW', padx=10)

        self.top2.lbl4 = ttk.Label(er, text='Sent to:')
        self.top2.lbl4.grid(row=0, column = 0, sticky='NW', pady=(8,0))
        self.top2.expect_text = Text(er, width=40, height=14)
        self.top2.expect_text.grid(row=1,column=0, sticky='NSEW')

        # clear button
        self.top2.clear_button = ttk.Button(er, text = 'Clear', command = self.clear_expect_reqs)
        self.top2.clear_button.grid(row=2,column=0, sticky='NE', pady=(8,0))

        exp_scrollbar = ttk.Scrollbar(er, orient=tk.VERTICAL, command=self.top2.expect_text.yview)
        self.top2.expect_text.configure(yscroll=exp_scrollbar.set)
        exp_scrollbar.grid(row=1,column=1, sticky='NS')


        # fill in values if editing
        if is_new==0:

            self.top2.entry_expect.delete(0,END)
            self.top2.entry_expect.insert(0,record[0])
            self.top2.entry_reply.delete(0,END)
            self.top2.entry_reply.insert(0,record[1])
            self.top2.entry_allowed.delete(0,END)
            self.top2.entry_allowed.insert(0,record[2])
            self.top2.entry_txmax.delete(0,END)
            self.top2.entry_txmax.insert(0,record[4])

            if record[6]!=None:
                self.top2.entry_speed.set(record[6])
            else:
                self.top2.entry_speed.set("Current")

            if record[7]!=None:
                self.top2.entry_autotx.delete(0,END)
                self.top2.entry_autotx.insert(0,record[7])

            if record[8]!=None:
                self.top2.entry_atx_target.delete(0,END)
                self.top2.entry_atx_target.insert(0,record[8])

            expect_contents = ""
            for txitem in record[3].split(","):
                expect_contents += txitem+"\n"
            self.top2.expect_text.insert(tk.END, expect_contents)

        self.top2.expect_text.configure(state='disabled')
        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Clear the sent to list for expect entry
    def clear_expect_reqs(self):
        exiid = self.expect.focus()
        msgtxt = "Are you sure you want clear the Sent To list for this entry? This action cannot be undone."
        answer = askyesno(title='Clear Sent To?', message=msgtxt, parent=self.top2)
        if answer:
            c.execute("UPDATE expect SET txlist='' WHERE expect = ?", [exiid])
            conn.commit()
            self.get_expects()
            self.top2.destroy()
            self.update_expect()

    # Called from show_expect only
    def save_expect(self):
        new_expect = re.sub(r'[^A-Z0-9!]','',self.top2.entry_expect.get().upper())
        new_reply = self.top2.entry_reply.get().upper()
        new_allowed = self.top2.entry_allowed.get().upper()
        new_allowed = new_allowed.replace(" ", "")
        new_txmax = self.top2.entry_txmax.get().upper()
        new_txspeed = self.top2.entry_speed.get()
        # "Current" means leave JS8Call's current TX speed untouched -- store NULL so downstream skips MODE.SET_SPEED
        if new_txspeed == "Current": new_txspeed = None
        new_autotx = self.top2.entry_autotx.get()
        new_atx_target = self.top2.entry_atx_target.get()

        # validate input
        if new_expect == "" or new_reply == "" or new_allowed == "" or new_txmax == "" : return

        if new_txmax.isnumeric() == False:
            messagebox.showinfo("Error","Max Replies must be a number (1-99)", parent=self.top2)
            return

        if int(new_txmax) < 0 or int(new_txmax) > 99:
            messagebox.showinfo("Error","Max Replies must be between 0 and 99. Set to 0 to disable an entry. Set to 99 to allow unlimited replies.", parent=self.top2)
            return

        auto_tx_list = re.findall(r"([0-9]{2}):([0-9]{2})",new_autotx)
        if len(auto_tx_list)==0 and len(new_autotx)>0:
            messagebox.showinfo("Error","Your Auto TX times were not formatted properly. They must be in HH:MM format, comma separated.", parent=self.top2)
            return
        if len(auto_tx_list)>0:
             for auto_tx_item in auto_tx_list:
                atx_hours = int(auto_tx_item[0])
                atx_mins = int(auto_tx_item[1])
                if atx_hours<0 or atx_hours>23 or atx_mins<0 or atx_mins>59:
                    messagebox.showinfo("Error","Your Auto TX times were out of range. Valid times on planet earth are between 00:00 and 23:59.", parent=self.top2)
                    return

        if len(auto_tx_list)>atx_limit:
            messagebox.showinfo("Error","You can only have up to "+str(atx_limit)+" Auto TX times per Expect entry.", parent=self.top2)
            return

        # preserve txlist if it exists already
        c.execute("SELECT * FROM expect WHERE expect = ?", [new_expect[0:6]])
        record = c.fetchone()
        old_txlist = ""
        if record:
            old_txlist = record[3]

        # checks passed, save and update
#        sql = "INSERT INTO expect(expect,reply,allowed,txmax,txlist,lm,txspeed,autotx) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP,?,?)"
#        c.execute(sql, [new_expect[0:6],new_reply,new_allowed,new_txmax,old_txlist,new_txspeed,new_autotx])
        sql = "INSERT INTO expect(expect,reply,allowed,txmax,txlist,lm,txspeed,autotx,atxtarget) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP,?,?,?)"
        c.execute(sql, [new_expect[0:6],new_reply,new_allowed,new_txmax,old_txlist,new_txspeed,new_autotx,new_atx_target])
        conn.commit()

        self.get_expects()
        self.top2.destroy()
        self.update_expect()

    def cancelsave_expect(self):
        self.entry_expect.delete(0,END)
        self.entry_reply.delete(0,END)
        self.entry_allowed.delete(0,END)
        self.entry_txmax.delete(0,END)

    def delete_expect(self, ev):
        if not self.expect.focus(): return
        exiid = self.expect.focus()

        msgtxt = "Remove the expect entry for "+exiid+"?"
        answer = askyesno(title='Remove Expect Entry?', message=msgtxt, parent=self.top)
        if answer:
            c.execute("DELETE FROM expect WHERE expect = ?", [exiid])
            conn.commit()
            self.get_expects()
            self.update_expect()

    def get_expects(self):
        global expects, auto_txes

        expects.clear()
        auto_txes.clear()

        c.execute("SELECT * FROM expect")
        expects = c.fetchall()

        # update store of auto tx times
        for expect_item in expects:
            if expect_item[7] != None:
                auto_tx_list = re.findall(r"([0-9]{2}):([0-9]{2})",expect_item[7])
                if len(auto_tx_list)>0:
                     for auto_tx_item in auto_tx_list[:atx_limit]:
                        atx_hours = int(auto_tx_item[0])
                        atx_mins = int(auto_tx_item[1])
                        auto_txes.append([expect_item[0],atx_hours,atx_mins])

    ## Manually tx an expect response
    def tx_expect(self):
        try:
            expid=self.expect.focus()
        except:
            expid = self.newexpectid

        c.execute("SELECT * FROM expect WHERE expect = ?", [expid])
        record = c.fetchone()

        self.new_reply=""
        if record!=None:
            self.new_reply = record[1]

        if self.new_reply=="":
            messagebox.showinfo("Nothing to Send","Please select an entry to send.", parent=self.top)
            return

        self.txexptop = Toplevel(self)
        self.txexptop.title("Manually Send Expect Response")
        self.txexptop.resizable(width=False, height=False)

        label_new = ttk.Label(self.txexptop, text = "Send to (single callsign or group)")
        label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.sendto = ttk.Entry(self.txexptop, width='34')
        self.sendto.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
        self.sendto.bind("<KeyRelease>", lambda x: self.txexpect_updatecmd())

        if settings['expect_lastsentto'] != "":
            self.sendto.delete(0,END)
            self.sendto.insert(0,settings['expect_lastsentto'])

        self.msgcheck = ttk.Checkbutton(self.txexptop, text='Send as MSG', onvalue=1, offvalue=0, command=self.txexpect_updatecmd)
        self.msgcheck.grid(row=1, column=0, sticky='W', pady=(8,0))
        self.msgcheck.state(['!alternate','!selected'])

        self.tx_cmd = ttk.Entry(self.txexptop)
        self.tx_cmd.grid(row = 2, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        if record[6] not in (None, "Current"):
            self.tx_speed=record[6]
        else:
            self.tx_speed=None

        cbframe = ttk.Frame(self.txexptop)
        cbframe.grid(row=3, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_txexpect)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        create_button = ttk.Button(cbframe, text = "Copy", command = self.txexpect_copy)
        create_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.txexptop.destroy)
        cancel_button.grid(row=0, column = 3, padx=(10,0), pady=(20,20))

        self.txexpect_updatecmd()
        self.txexptop.wait_visibility()
        self.txexptop.grab_set()
        self.txexptop.focus_set()
        self.sendto.focus()
        self.txexptop.bind('<Escape>', lambda x: self.txexptop.destroy())

    def txexpect_copy(self):
        global settings
        settings['expect_lastsentto']=self.sendto.get()
        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['expect_lastsentto']+"' WHERE name = 'expect_lastsentto'")
        conn.commit()

        messagebox.showinfo("Copied","Copied to clipboard", parent=self.txexptop)
        self.clipboard_clear()
        text = self.tx_cmd.get()
        self.clipboard_append(text)

    def txexpect_updatecmd(self):
        to = self.sendto.get().strip().upper()
        msg = self.new_reply.strip()

        msgadd=""
        if self.msgcheck.instate(['selected']):
            msgadd="MSG "

        tx_cmd = to+" "+msgadd+msg
        self.tx_cmd.delete(0,END)
        self.tx_cmd.insert(0,tx_cmd)

    def proc_txexpect(self):
        global settings
        settings['expect_lastsentto']=self.sendto.get()
        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['expect_lastsentto']+"' WHERE name = 'expect_lastsentto'")
        conn.commit()

        new_cmd = self.tx_cmd.get()
        if new_cmd == "": return

        # MODE.GET_SPEED / MODE.SET_SPEED, 0=normal, 1=fast, 2=JS8 40, 4=slow, 8=JS8 60, 16=Subspace
        if self.tx_speed!=None:
            old_speed = reported_speed
            new_speed = 0
            if self.tx_speed=="Normal": new_speed=0
            if self.tx_speed=="Fast":   new_speed=1
            if self.tx_speed=="JS8 40":  new_speed=2
            if self.tx_speed=="Slow":   new_speed=4
            if self.tx_speed=="JS8 60":  new_speed=8
            if self.tx_speed=="Subspace":   new_speed=16

            tx_content = json.dumps({"params":{"SPEED":new_speed},"type":"MODE.SET_SPEED"})
            self.sock.send(bytes(tx_content + '\n','utf-8'))
            time.sleep(0.25)

            # as of v2.4.0, we must estimate when to set the speed back
            sent_words = len(new_cmd.split())
            speed_reset_delay = self.get_tx_time(new_speed,sent_words)
            super().after(int(speed_reset_delay*1000),self.reset_speed,old_speed)

        # make sure the message pane is empty
        tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        time.sleep(0.33)

        tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":new_cmd})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        time.sleep(0.25)

#       # in later versions we may be able to instantly reset the system-wide speed, without breaking the queued speed
#        if self.tx_speed!=None:
#            tx_content = json.dumps({"params":{"SPEED":old_speed},"type":"MODE.SET_SPEED"})
#            self.sock.send(bytes(tx_content + '\n','utf-8'))
#            time.sleep(0.25)

        self.txexptop.destroy()

    ## MCForms subsystem form responses list view
    def form_responses(self):
        global totals

        totals[2]=0
        self.update_statusbar()

        self.top = Toplevel(self)
        self.top.title("MCForms - Form Responses")
        self.top.geometry('1000x465')
        self.top.minsize(1000,465)
        self.top.resizable(width=True, height=True)

        self.top.columnconfigure(0, weight=24)
        self.top.columnconfigure(1, weight=1)

        self.top.rowconfigure(0,weight=1)
        self.top.rowconfigure(1,weight=24)
        self.top.rowconfigure(2,weight=1)

        # form type select, date range select, & title
        self.ftframe = ttk.Frame(self.top)
        self.ftframe.grid(row=0, column=0, columnspan=2, sticky='NSEW', padx=10, pady=(0,5))

        self.ftmark = ttk.Label(self.ftframe, text='View Form Responses:', font=("Segoe Ui Bold", 12))
        self.ftmark.grid(row=0, column = 0, sticky='W', padx=0, pady=(8,0))
        self.ftcombo = ttk.Combobox(self.ftframe, values="", state='readonly', width='40')
        self.ftcombo.grid(row=0, column =1 , sticky='E', padx=8, pady=(8,0))
        self.ftcombo.bind('<<ComboboxSelected>>', self.formtype_selcombo)
        self.drcombo = ttk.Combobox(self.ftframe, values=("All Time","Last 24hrs","Last Week","Last Month","Last Year"), state='readonly')
        self.drcombo.grid(row=0, column =2 , sticky='E', padx=8, pady=(8,0))
        self.drcombo.bind('<<ComboboxSelected>>', self.formtype_selcombo)
        self.dupcombo = ttk.Combobox(self.ftframe, values=("No Filter","Filter Duplicates"), state='readonly')
        self.dupcombo.grid(row=0, column =3 , sticky='E', padx=8, pady=(8,0))
        self.dupcombo.bind('<<ComboboxSelected>>', self.formtype_selcombo)

        # form response treeview
        self.formresp = ttk.Treeview(self.top, show='headings') #, selectmode="browse")
        self.formresp["columns"]=("fromcall","tocall","typeid","response","msgtxt","timesig","gw","lm")

        self.formresp.column("fromcall", width=60, minwidth=60, stretch=0)
        self.formresp.column("tocall", width=60, minwidth=60)
        self.formresp.column("typeid", width=60, minwidth=60)
        self.formresp.column("response", width=260, minwidth=260)
        self.formresp.column("msgtxt", width=260, minwidth=260)
        self.formresp.column("timesig", width=95, minwidth=95)
        self.formresp.column("gw", width=40, minwidth=40)
        self.formresp.column("lm", width=120, minwidth=120, stretch=0)

        self.formresp.heading("fromcall", text="From", command=lambda c="fromcall": self.sort_treeview(self.formresp, c, False))
        self.formresp.heading("tocall", text="To", command=lambda c="tocall": self.sort_treeview(self.formresp, c, False))
        self.formresp.heading("typeid", text="Form #", command=lambda c="typeid": self.sort_treeview(self.formresp, c, False))
        self.formresp.heading("response", text="Form Responses")
        self.formresp.heading("msgtxt", text="Message")
        self.formresp.heading("timesig", text="Timestamp")
        self.formresp.heading("gw", text="GW")
        self.formresp.heading("lm", text="Received", command=lambda c="lm": self.sort_treeview(self.formresp, c, False))

        self.formresp.bind('<Double-1>', self.show_formresp)
        self.formresp.bind('<Button-3>', lambda ev: self.form_view(0,ev))

        self.formresp.bind('<Delete>', self.delete_formresp)
        self.formresp.grid(row=1, column=0, sticky='NSEW', padx=(10,0), pady=(10,10))

        self.frscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.formresp.yview)
        self.formresp.configure(yscroll=self.frscrollbar.set)
        self.frscrollbar.grid(row=1, column=1, sticky='NS', padx=(0,10), pady=(10,10))

        # frame with action items
        self.frframe = ttk.Frame(self.top)
        self.frframe.grid(row=2, column=0, sticky='NSEW')

        self.frexport = ttk.Button(self.frframe, text = 'Import', command = self.import_formresps, width='9')
        self.frexport.grid(row=0, column=0, sticky='NE', padx=(8,8),pady=(8,8))

        self.frexport = ttk.Button(self.frframe, text = 'Export All', command = self.export_formresps, width='12')
        self.frexport.grid(row=0, column=1, sticky='NE', padx=(8,8),pady=(8,8))

        self.gwlabel = Label(self.frframe, text='Gateway:')
        self.gwlabel.grid(row=0, column = 2, sticky='NE', padx=(30,0), pady=(12,8))
        self.gateway = ttk.Entry(self.frframe, width = '44')
        self.gateway.grid(row = 0, column = 3, sticky='NE', padx=(8,8), pady=(8,8))
        self.gateway.insert(0, settings['forms_gateway'])
        self.gateway.bind('<Return>', lambda ev: self.form_savegw())
        self.gwsave = ttk.Button(self.frframe, text = 'Save GW', command = self.form_savegw, width='10')
        self.gwsave.grid(row=0, column=4, sticky='NE', padx=(2,8),pady=(8,8))

        self.fwresp = ttk.Button(self.frframe, text = 'Forward', command = self.form_fwresp, width='10')
        self.fwresp.grid(row=0, column=5, sticky='NE', padx=(32,8),pady=(8,8))

        self.update_formtypecombo()
        self.ftcombo.set("View All Form Types")
        self.drcombo.set("All Time")
        self.dupcombo.set("No Filter")
        self.update_formresponses()
        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Save form gateway setting
    def form_savegw(self):
        global settings
        new_gw = self.gateway.get()
        settings['forms_gateway'] = str(new_gw)
        # save change in settings table
        c.execute("UPDATE setting SET value = '"+settings['forms_gateway']+"' WHERE name = 'forms_gateway'")
        conn.commit()
        messagebox.showinfo("Forms Gateway","Forms gateway saved. If you entered a valid URL, any new forms stored will also be sent to this URL. Save the Gateway box empty to disable.", parent=self.top)

    ## Forward a form response to another station/group
    def form_fwresp(self):
        if not self.formresp.focus():
            messagebox.showinfo("Nothing to Forward","Please select a row to forward.", parent=self.top)
            return
        friid = self.formresp.focus()

        if friid == "": return

        c.execute("SELECT * FROM forms WHERE id = '"+friid+"'")
        formresp_db = c.fetchone()

        if formresp_db:

            self.new_reply = formresp_db[3]+" "+formresp_db[4]+" "+formresp_db[5]+" "+formresp_db[6]+" "+" *DE* "+formresp_db[1]

            self.top2 = Toplevel(self)
            self.top2.title("Forward Form Response")
            self.top2.resizable(width=False, height=False)

            label_new = ttk.Label(self.top2, text = "Forward to (single callsign or group)")
            label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
            self.sendto = ttk.Entry(self.top2, width='34')
            self.sendto.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
            self.sendto.bind("<KeyRelease>", lambda x: self.fwresp_updatecmd())

            self.msgcheck = ttk.Checkbutton(self.top2, text='Send as MSG', onvalue=1, offvalue=0, command=self.fwresp_updatecmd)
            self.msgcheck.grid(row=1, column=0, sticky='W', pady=(8,0))
            self.msgcheck.state(['!alternate','!selected'])

            self.tx_cmd = ttk.Entry(self.top2)
            self.tx_cmd.grid(row = 2, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

            cbframe = ttk.Frame(self.top2)
            cbframe.grid(row=3, columnspan=2, sticky='e', padx=10)

            create_button = ttk.Button(cbframe, text = "Send", command = self.proc_fwresp)
            create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
            cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top2.destroy)
            cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

            self.txexpect_updatecmd()
            self.top2.wait_visibility()
            self.top2.grab_set()
            self.top2.focus_set()
            self.sendto.focus()
            self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    def fwresp_updatecmd(self):
        to = self.sendto.get().strip().upper() + ">"
        msg = self.new_reply.strip()

        msgadd=""
        if self.msgcheck.instate(['selected']):
            msgadd="MSG "

        tx_cmd = to+" "+msgadd+msg
        self.tx_cmd.delete(0,END)
        self.tx_cmd.insert(0,tx_cmd)

    def proc_fwresp(self):
        new_cmd = self.tx_cmd.get()
        if new_cmd == "": return

        # make sure the message pane is empty
        tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        time.sleep(0.33)

        tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":new_cmd})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        self.top2.destroy()

    ## Update form responses treeview
    def update_formresponses(self):
        # limit to selected form type
        typeid_selection = self.ftcombo.get().split(",")[0]
        wheres = ""
        if typeid_selection!="" and typeid_selection!="View All Form Types":
            wheres = " WHERE typeid = '"+typeid_selection+"' "

        # limit to selected date range
        range_selection = self.drcombo.get()
        if range_selection:
            if range_selection!="All Time":
                if wheres=="":
                    wheres = " WHERE "
                else:
                    wheres += " AND "
                if range_selection=="Last 24hrs": wheres+="lm > DATETIME('now', '-24 hour')"
                if range_selection=="Last Week": wheres+="lm > DATETIME('now', '-7 day')"
                if range_selection=="Last Month": wheres+="lm > DATETIME('now', '-31 day')"
                if range_selection=="Last Year": wheres+="lm > DATETIME('now', '-365 day')"

        # filter duplicates if selected
        filter_dup = self.dupcombo.get()
        if filter_dup=="Filter Duplicates":
            wheres+=" GROUP BY fromcall, typeid, responses, timesig"

        # clear out the tree
        for entry in self.formresp.get_children():
            self.formresp.delete(entry)

        c.execute("SELECT * FROM forms "+wheres+" ORDER BY lm DESC")
        formresp_lines = c.fetchall()

        count = 0
        for record in formresp_lines:
            fr_date = record[7] # or format, such as: record[7].split(" ")[0]
            fr_gwtx = "!"
            if record[8]=="<Response [200]>": fr_gwtx="\u2713" # http response from gateway, 200, 404, 403, 500, etc
            if record[8]=="": fr_gwtx=""

            if count % 2 == 1:
                self.formresp.insert('', tk.END, iid=record[0], values=(record[1],record[2],record[3],record[4],record[5],self.decode_shorttime(record[6]),fr_gwtx,fr_date), tags=('oddrow'))
            else:
                self.formresp.insert('', tk.END, iid=record[0], values=(record[1],record[2],record[3],record[4],record[5],self.decode_shorttime(record[6]),fr_gwtx,fr_date), tags=('evenrow'))
            count+=1

        if settings['dark_theme'] == "1":
            self.formresp.tag_configure('oddrow', background='#777')
            self.formresp.tag_configure('evenrow', background='#555')
        else:
            self.formresp.tag_configure('oddrow', background='#EEE')
            self.formresp.tag_configure('evenrow', background='#FFF')

    ## Build/rebuild form type combobox
    def update_formtypecombo(self):
        global forms
        self.form_refresh()

        # clear combobox
        self.ftcombo.delete(0, tk.END)

        # rebuild from database
        c.execute("SELECT id,typeid FROM forms ORDER BY typeid ASC")
        ftype_records = c.fetchall()
        ftcomboopts = []

        ftcomboopts.append("View All Form Types")
        for record in ftype_records:
            if record[1] in forms.keys():
                newrec = record[1]+", "+forms[record[1]][0]
            else:
                newrec = record[1]+", Unknown Form"

            #if record[1] not in ftcomboopts:
            if newrec not in ftcomboopts:
                ftcomboopts.append(newrec)

        self.ftcombo['values'] = ftcomboopts

    ## Select a form typeid through the combobox
    def formtype_selcombo(self, ev):
        self.update_formresponses()

    ## Display formatted version of form response data
    def show_formresp(self,ev):
        if not self.formresp.focus(): return
        friid = self.formresp.focus()

        if friid == "": return

        c.execute("SELECT * FROM forms WHERE id = '"+friid+"'")
        formresp_db = c.fetchone()

        if formresp_db:
            formdata, formtext = self.form_items(formresp_db[3])
            dcst = self.decode_shorttime(formresp_db[6])

            self.top2 = Toplevel(self)
            self.top2.title("Form "+formresp_db[3]+" from "+formresp_db[1])
            self.top2.geometry('650x500')

            # display window
            self.export_text = Text(self.top2, wrap=NONE, font='TkFixedFont')
            fr_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
            self.export_text.configure(yscroll=fr_scrollbar.set)
            fr_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(10,10))

            # save and copy buttons
            tlframe = ttk.Frame(self.top2)
            tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
            self.top2.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
            self.top2.copy_button.pack(side=LEFT, padx=(0,10))
            self.top2.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
            self.top2.saveas_button.pack(side=RIGHT)

            self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(10,10))

            # right-click action
            self.rcmenu = Menu(self.top2, tearoff = 0)
            self.rcmenu.add_command(label = 'Copy')
            self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

            gwresp=""
            if formresp_db[8]!="": gwresp="\nGateway Response: "+formresp_db[8]
            raw_form = formresp_db[3]+" "+formresp_db[4]+" "+formresp_db[5]+formresp_db[6]
            fr_contents = "Form:         "+formresp_db[3]+"\nFROM Station: "+formresp_db[1]+"\nTO Station:   "+formresp_db[2]+"\nFiled:        "+dcst+"\nReceived:     "+formresp_db[7]+gwresp+"\nRaw Format: "+raw_form+"\n========================\n\n"

            freeform_resps = re.findall(r"([A-Z0-9]{2})\[(.*?)\]\ ",formresp_db[5]+" ")
            resp_num=0
            fr_error=""

            # iterate through the form
            for qitem in formdata:
                for qdata in formdata[qitem]:
                    # if a question is found, check the next character in the string of responses against the available answers
                    if "question" in qdata:
                        fr_contents+= str(qdata['question'])
                        try:
                            qans = [i[str(formresp_db[4][resp_num])] for i in formdata[qitem] if str(formresp_db[4][resp_num]) in i]
                            if qans:
                                fr_contents += str(qans[0])+"\n"
                            resp_num+=1
                        except KeyError:
                            fr_error = "!!! Error building report !!!\nCheck that you have the correct form file in your forms folder.\n\n"
                    # if a prompt is found, attempt to locate a formatted response in the comments if available
                    elif "prompt" in qdata:
                        if len(freeform_resps)>0:
                            fr_contents+= str(qdata['prompt'][2:])
                            for key, value in freeform_resps:
                                if key == qdata['prompt'][:2]:
                                    fr_contents+=str(value)+"\n\n"

            fr_contents += fr_error
            fr_contents += "Comment: "+formresp_db[5]

            self.export_text.insert(tk.END, fr_contents)
            self.export_text.configure(state='disabled')

            self.top2.wait_visibility()
            self.top2.grab_set()
            self.top2.focus_set()
            self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Remove saved form response(s) from database/tree
    def delete_formresp(self,ev):
        frlist = ""
        for friid in self.formresp.selection():
            frlist += "DBID ["+friid+"] from "+str(self.formresp.item(friid)['values'][0])+" received "+str(self.formresp.item(friid)['values'][7])+"\n"

        if frlist == "": return

        msgtxt = "Remove the following form response(s)? This action cannot be undone.\n\n"+frlist
        answer = askyesno(title='Remove Form Response(s)?', message=msgtxt, parent=self.top)
        if answer:
            for friid in self.formresp.selection():
                c.execute("DELETE FROM forms WHERE id = ?", [friid])
            conn.commit()
            self.update_formresponses()

    ## Add form responses to the database manually (import)
    def import_formresps(self):
        self.top2 = Toplevel(self)
        self.top2.title("Add Form Responses")
        self.top2.geometry('400x500')
        self.top2.minsize(400,500)

        self.addmark = ttk.Label(self.top2, text="Type or paste (ctrl+v) form responses, one per line\nFormat is FROM TO FORM RESPS MSG TIMESIG\nFields are tab delimited")
        self.addmark.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # save button
        tlframe = ttk.Frame(self.top2)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.save_button = ttk.Button(tlframe, text = 'Add Responses', command = self.proc_importformresps)
        self.save_button.pack(side=LEFT, padx=(0,10))

        # text window
        self.batch = Text(self.top2, wrap=NONE)
        batch_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.batch.yview)
        self.batch.configure(yscroll=batch_scrollbar.set)
        batch_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.batch.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    ## Process added form responses
    def proc_importformresps(self):
        batch_values = StringIO(self.batch.get('1.0','end'))
        for line in batch_values:

            # format is FROM<tab>TO<tab>FORM#<tab>RESPS<tab>MSG<tab`>TIMESIG
            match_forms = re.search(r"(.*)\t(.*)\t(F!.*)\t(.*)\t(.*)\t(\#[A-Z]+)",line.upper())
            if match_forms:
                sql = "INSERT INTO forms(fromcall,tocall,typeid,responses,msgtxt,timesig,lm,gwtx) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP,'')"
                c.execute(sql, [match_forms[1],match_forms[2],match_forms[3],match_forms[4],match_forms[5],match_forms[6]])
                conn.commit()

        self.top2.destroy()
        self.update_formresponses()

    def export_formresps(self):
        # limit to selected form type
        typeid_selection = self.ftcombo.get().split(",")[0]
        wheres = ""
        if typeid_selection!="" and typeid_selection!="View All Form Types":
            wheres = " WHERE typeid = '"+typeid_selection+"' "

        # limit to selected date range
        range_selection = self.drcombo.get()
        if range_selection:
            if range_selection!="All Time":
                if wheres=="":
                    wheres = " WHERE "
                else:
                    wheres += " AND "
                if range_selection=="Last 24hrs": wheres+="lm > DATETIME('now', '-24 hour')"
                if range_selection=="Last Week": wheres+="lm > DATETIME('now', '-7 day')"
                if range_selection=="Last Month": wheres+="lm > DATETIME('now', '-31 day')"
                if range_selection=="Last Year": wheres+="lm > DATETIME('now', '-365 day')"

        c.execute("SELECT * FROM forms "+wheres+" ORDER BY lm DESC")
        formresp_lines = c.fetchall()

        if formresp_lines:
            self.top2 = Toplevel(self)
            self.top2.title("Form Responses Export")
            self.top2.geometry('650x500')

            # display window
            self.export_text = Text(self.top2, wrap=NONE, font='TkFixedFont')
            fr_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
            self.export_text.configure(yscroll=fr_scrollbar.set)
            fr_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(10,10))

            # save and copy buttons
            tlframe = ttk.Frame(self.top2)
            tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
            self.top2.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
            self.top2.copy_button.pack(side=LEFT, padx=(0,10))
            self.top2.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
            self.top2.saveas_button.pack(side=RIGHT)

            self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(10,10))

            # right-click action
            self.rcmenu = Menu(self.top2, tearoff = 0)
            self.rcmenu.add_command(label = 'Copy')
            self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

            # loop through form responses to build export
            export_contents = ""
            for record in formresp_lines:
                for i in record:
                    export_contents+=str(i)+chr(9)
                export_contents+="\n"

            self.export_text.insert(tk.END, export_contents)
            self.export_text.configure(state='disabled')

            self.top2.wait_visibility()
            self.top2.grab_set()
            self.top2.focus_set()
            self.top2.bind('<Escape>', lambda x: self.top2.destroy())
        else:
            messagebox.showinfo("No Form Responses","Couldn't find any form responses to export.", parent=self.top)

    ## View a dynamically generated GUI form to fill in (or, view a response in GUI mode)
    def form_view(self, formid, friid):
        global forms

        # Process captured response view in GUI mode
        if type(friid) is not int:
            if not self.formresp.focus(): return
            friid = self.formresp.focus()

            if friid == "": return

            c.execute("SELECT * FROM forms WHERE id = '"+friid+"'")
            formresp_db = c.fetchone()

            if formresp_db:
                formid = formresp_db[3]
                dcst = self.decode_shorttime(formresp_db[6])
                # captured response found, generate header
                fr_contents = "FROM Station: "+formresp_db[1]+"        TO Station: "+formresp_db[2]+"\nFiled: "+dcst+"        Received: "+formresp_db[7]+"\nComment: "+formresp_db[5]

                if formresp_db[5]!="":
                    # process any free-form entries from comments section (append space for imported forms that may be missing space used in regex)
                    freeform_resps = re.findall(r"([A-Z0-9]{2})\[(.*?)\]\ ",formresp_db[5]+" ")

        if formid not in forms:
            messagebox.showwarning("Missing Form","The associated form is not in your forms folder.", parent=self.top)
            return

        self.top3 = Toplevel(self)
        self.top3.title("MCForms - Form "+str(formid)+" | "+forms[formid][0])
        self.top3.geometry('1024x600')
        self.top3.minsize(600,500)
        self.top3.resizable(width=True, height=True)

        self.top3.columnconfigure(0,weight=12)

        formtitle = ttk.Label(self.top3, text = str(formid)+" -- "+forms[formid][0], font=("Segoe Ui Bold", 14))
        formtitle.grid(row=0, column = 0, sticky='W', padx=0, pady=(8,0))

        if type(friid) is str:
            self.top3.rowconfigure(0,weight=1)
            self.top3.rowconfigure(1,weight=1)
            self.top3.rowconfigure(2,weight=12)
            self.top3.rowconfigure(3,weight=1)
            self.top3.rowconfigure(4,weight=1)

            formsummary = Label(self.top3, text = fr_contents, wraplength=600, justify=LEFT)
            formsummary.grid(row = 1, column = 0, sticky='W', padx=0, pady=0)
            frame=ttk.Frame(self.top3)
            frame.grid(row=2, column=0, sticky='NEWS', padx=0, pady=0)
        else:
            self.top3.rowconfigure(0,weight=1)
            self.top3.rowconfigure(1,weight=12)
            self.top3.rowconfigure(2,weight=1)
            self.top3.rowconfigure(3,weight=1)

            frame=ttk.Frame(self.top3)
            frame.grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)

        self.formcanvas=Canvas(frame, width=300, height=300, scrollregion=(0,0,1900,1900), bd=0, highlightthickness=0, relief='ridge')

        hbar=ttk.Scrollbar(frame,orient=tk.HORIZONTAL, command=self.formcanvas.xview)
        hbar.config(command=self.formcanvas.xview)
        hbar.pack(side=BOTTOM,fill=X, padx=10, pady=10)

        vbar=ttk.Scrollbar(frame,orient=tk.VERTICAL, command=self.formcanvas.yview)
        vbar.config(command=self.formcanvas.yview)
        vbar.pack(side=RIGHT,fill=Y, padx=10, pady=10)

        self.top3.formframe = ttk.Frame(self.formcanvas)
        self.top3.formframe.grid(row=0, column=0, padx=10, pady=10)
        self.formcanvas.create_window((0, 0), window=self.top3.formframe, anchor='nw')

        formdata, formtext = self.form_items(formid)
        formlabels = {}
        self.top3.formcombos = {}
        self.top3.formprompts = {}

        # loop through all the questions in this form (and associated text)
        hp=0
        qnumoffset=0
        for qnum in formdata:
            fcopts = []
            maxlen=0
            anum=0
            defanum=-1

            # process all text (if any) associated with this question
            if qnum in formtext:
                for tdata in formtext[qnum]:
                    if "header1" in tdata:
                        formlabels[qnum] = Label(self.top3.formframe, text = tdata["header1"].strip(), wraplength=600, justify=CENTER, fg='orange', font=("Segoe Ui Bold",15))
                        formlabels[qnum].grid(row = qnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                        hp+=1
                    if "header2" in tdata:
                        formlabels[qnum] = Label(self.top3.formframe, text = tdata["header2"].strip(), wraplength=600, justify=CENTER, fg='#3399ff', font=("Segoe Ui Bold",13))
                        formlabels[qnum].grid(row = qnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                        hp+=1
                    if "header3" in tdata:
                        formlabels[qnum] = Label(self.top3.formframe, text = tdata["header3"].strip(), wraplength=600, justify=CENTER, fg='red', font=("Segoe Ui Bold",11))
                        formlabels[qnum].grid(row = qnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                        hp+=1
                    if "text" in tdata:
                        formlabels[qnum] = Label(self.top3.formframe, text = tdata["text"].strip(), wraplength=600, justify=CENTER)
                        formlabels[qnum].grid(row = qnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                        hp+=1

            # process all question/response data
            for qdata in formdata[qnum]:
                if "question" in qdata:
                    formlabels[qnum] = ttk.Label(self.top3.formframe, text = qdata["question"].strip(), wraplength=300, justify=RIGHT)
                    formlabels[qnum].grid(row = qnum+hp, column = 0, sticky=E, padx=10, pady=(0,10))

                    self.top3.formcombos[qnum] = ttk.Combobox(self.top3.formframe, values="", state='readonly')
                    self.top3.formcombos[qnum].grid(row = qnum+hp, column = 1 , sticky=W, padx=10, pady=(0,10))
                elif "prompt" in qdata:
                    formlabels[qnum] = ttk.Label(self.top3.formframe, text = qdata["prompt"][2:].strip(), wraplength=300, justify=RIGHT)
                    formlabels[qnum].grid(row = qnum+hp, column = 0, sticky=E, padx=10, pady=(0,10))
                    pcode=qdata["prompt"][:2]

                    self.top3.formprompts[pcode] = ttk.Entry(self.top3.formframe, width='34')
                    self.top3.formprompts[pcode].bind("<FocusOut>", self.build_comment)
                    self.top3.formprompts[pcode].grid(row = qnum+hp, column = 1 , sticky=W, padx=10, pady=(0,10))

                    qnumoffset+=1
                else:
                    for i in qdata:
                        qdatastr = str(i)+" "+str(qdata[i].strip())
                        if str(qdata[i])[0] == "*":
                            if defanum==-1: defanum=anum
                        # process captured form response gui display [][need to complete -- use load_form?]
                        if type(friid) is str:
                            try:
                                if str(formresp_db[4][qnum-1-qnumoffset])==str(i):
                                    defanum=anum
                            except IndexError:
                                # So that partial forms still display the available data.
                                # Shouldn't normally happen, but may happen if a form template changes and you have old saved forms
                                pass
                    anum+=1
                    fcopts.append(qdatastr)
                    if maxlen < len(qdatastr): maxlen = len(qdatastr)+2

            if qnum in self.top3.formcombos:
                self.top3.formcombos[qnum]["values"] = fcopts
                self.top3.formcombos[qnum]["width"] = maxlen
                if defanum>-1: self.top3.formcombos[qnum].current(defanum)
                if type(friid) is str:
                    self.top3.formcombos[qnum].config(state=DISABLED)

        # handle any ., !, !!, !!! items not associated with a question (after last question qnum)
        lqnum = len(formdata)+1
        if lqnum in formtext:
            for tdata in formtext[lqnum]:
                if "header1" in tdata:
                    formlabels[lqnum] = Label(self.top3.formframe, text = tdata["header1"].strip(), wraplength=600, justify=CENTER, fg='orange', font=("Segoe Ui Bold",15))
                    formlabels[lqnum].grid(row = lqnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                    hp+=1
                if "header2" in tdata:
                    formlabels[lqnum] = Label(self.top3.formframe, text = tdata["header2"].strip(), wraplength=600, justify=CENTER, fg='#3399ff', font=("Segoe Ui Bold",13))
                    formlabels[lqnum].grid(row = lqnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                    hp+=1
                if "header3" in tdata:
                    formlabels[lqnum] = Label(self.top3.formframe, text = tdata["header3"].strip(), wraplength=600, justify=CENTER, fg='red', font=("Segoe Ui Bold",11))
                    formlabels[lqnum].grid(row = lqnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                    hp+=1
                if "text" in tdata:
                    formlabels[lqnum] = Label(self.top3.formframe, text = tdata["text"].strip(), wraplength=600, justify=CENTER)
                    formlabels[lqnum].grid(row = lqnum+hp, column = 0, columnspan=2, sticky=NSEW, padx=10, pady=(0,10))
                    hp+=1

        self.formcanvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows
        self.formcanvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.formcanvas.bind_all("<Button-5>", self._on_mousewheel)  # Linux scroll down

        self.formcanvas.pack(side=LEFT,expand=True,fill=BOTH)
        self.formcanvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        try:
            if len(freeform_resps)>0:
                qnum=0

                for pcode,resp in freeform_resps:
                    if pcode in self.top3.formprompts:
                        self.top3.formprompts[pcode].delete(0,END)
                        self.top3.formprompts[pcode].insert(0,resp)
        except:
            pass

        if type(friid) is not str:
            finish_frame=ttk.Frame(self.top3)
            finish_frame.grid(row=2, column=0, sticky='NEWS', padx=0, pady=0)

            label_comment = ttk.Label(finish_frame, text = "Form Comment:")
            label_comment.grid(row = 0, column = 0, padx=(10,10), pady=(20,0))
            self.top3.fcomment = ttk.Entry(finish_frame, width='34')
            self.top3.fcomment.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))

            label_allow = ttk.Label(finish_frame, text = "Allowed:")
            label_allow.grid(row = 0, column = 2, padx=(10,10), pady=(20,0))
            self.top3.fallow = ttk.Entry(finish_frame, width='20')
            self.top3.fallow.insert(0, settings['exp_def_allow'])
            self.top3.fallow.grid(row = 0, column = 3, padx=(0,10), pady=(20,0))

            post_button = ttk.Button(finish_frame, text = "Post Form to Expect", command = lambda : self.post_form(formid))
            post_button.grid(row=0, column = 4, padx=(10,0), pady=(20,0))
            post_button = ttk.Button(finish_frame, text = "Load Posted Expect Form", command = lambda : self.load_form(formid))
            post_button.grid(row=0, column = 5, padx=(10,0), pady=(20,0))

        self.formcanvas.update_idletasks()
        self.formcanvas.configure(scrollregion = self.formcanvas.bbox('all'))

        self.top3.wait_visibility()
        self.top3.grab_set()
        self.top3.focus_set()
        self.top3.bind('<Escape>', lambda x: self.top3.destroy())

    ## form view scroll
    def _on_mousewheel(self, ev):
        try:
            if ev.num == 4:
                self.formcanvas.yview_scroll(-1, "units")
            elif ev.num == 5:
                self.formcanvas.yview_scroll(1, "units")
            else:
                self.formcanvas.yview_scroll(int(-1*(ev.delta/120)), "units")
        except:
            pass

    ## Automatically (re-)build the comments section based on form entry boxes
    def build_comment(self, ev):
        # capture current comments entry value, clean out any form items
        cmt = self.top3.fcomment.get()
        cmt = re.sub(r"[A-Z0-9]{2}\[(.*?)\]\ ", "", cmt)

        prompt_output=""
        for index, pcode in enumerate(self.top3.formprompts):
            # (re-)build new form comment parts
            if self.top3.formprompts[pcode].get()!="":
                prompt_output+=pcode+"["+str(self.top3.formprompts[pcode].get().strip())+"] "

        self.top3.fcomment.delete(0,END)
        self.top3.fcomment.insert(0, prompt_output+cmt)

    ## Load saved form from expect system if it exists
    def load_form(self, formid):
        c.execute("SELECT * FROM expect WHERE expect = ?", [formid])
        ex_exists = c.fetchone()
        if ex_exists:
            form_resps = re.search(r"(F\![A-Z0-9]+)\s+?([A-Z0-9]+)\s+?(.*?)(\#[A-Z0-9]+)",ex_exists[1])

            if form_resps[2]:
                # loop through form responses to set comboboxes
                qnum=0
                for resp in form_resps[2]:
                    qnum+=1
                    cnum=0

                    while qnum not in self.top3.formcombos:
                        qnum+=1

                    for index in self.top3.formcombos[qnum]["values"]:
                        if index[0] == resp: self.top3.formcombos[qnum].current(cnum)
                        cnum+=1

            if form_resps[3]!="":
                # process free-form entries from comments section
                freeform_resps = re.findall(r"([A-Z0-9]{2})\[(.*?)\]\ ",form_resps[3])
                if len(freeform_resps)>0:
                    qnum=0

                    for pcode,resp in freeform_resps:
                        if pcode in self.top3.formprompts:
                            self.top3.formprompts[pcode].delete(0,END)
                            self.top3.formprompts[pcode].insert(0,resp)

                # paste in as-found in comments entry box
                self.top3.fcomment.delete(0,END)
                self.top3.fcomment.insert(0, form_resps[3])

            # restore allowed tx list
            self.top3.fallow.delete(0,END)
            self.top3.fallow.insert(0, ex_exists[2])
        else:
            messagebox.showinfo("Form Not Found","A matching previously posted form was not found in the expect system.", parent=self.top3)

    ## Process form to expect system
    def post_form(self, formid):
        formdata, formtext = self.form_items(formid)
        allowed = self.top3.fallow.get().upper()

        resps = ""
        for qnum in formdata:
            if qnum in self.top3.formcombos:
                answer=str(self.top3.formcombos[qnum].get())
                if answer:
                    resps+=answer[0]
                else:
                    messagebox.showinfo("Please complete the form","Please make a selection for each box on the form before posting.", parent=self.top3)
                    return

        if allowed=="":
            messagebox.showinfo("Please complete the form","Please make to specify allowed requesting stations and/or groups before posting.", parent=self.top3)
            return

        resps = resps.strip()
        ecst = self.encode_shorttime()
        cmt = self.top3.fcomment.get().upper().strip()
        fresp = formid+" "+resps+" "+cmt+" "+ecst

        msgtxt = "Post the following form response to the Expect system?\n\n"+formid+" "+fresp+"\n\nThis will overwrite any existing responses to this form. TX log and Auto TX will be preserved."
        answer = askyesno(title='Post Form Response?', message=msgtxt, parent=self.top3)
        if answer:
            # preserve txlist (3), speed, and auto tx items (6,7,8)
            c.execute("SELECT * FROM expect WHERE expect = ?", [formid])
            record = c.fetchone()
            old_txlist = ""
            if record:
                old_txlist = record[3]
                old_speed = record[6]
                old_atx = record[7]
                old_atxtarget = record[8]

                sql = "INSERT INTO expect(expect,reply,allowed,txmax,txlist,lm,txspeed,autotx,atxtarget) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP,?,?,?)"
                c.execute(sql,[formid,fresp,allowed,"99",old_txlist,old_speed,old_atx,old_atxtarget])
            else:
                sql = "INSERT INTO expect(expect,reply,allowed,txmax,txlist,lm) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP)"
                c.execute(sql,[formid,fresp,allowed,"99",""])
            conn.commit()

            # offer to "Send Now"
            self.newexpectid = formid

            msgtxt = "Transmit your form over the air now?"
            answer2 = askyesno(title='Send Now?', message=msgtxt, parent=self.top3)

            if answer2:
                self.tx_expect()

            self.get_expects()
            self.top3.destroy()

    ## Build reports sub-menu from database
    def build_formsmenu(self):
        global forms, forms_focus
        self.form_refresh()

        # flagged primary forms
        if len(forms_focus)>0:
            for record in forms_focus:
                self.formsmenu.add_command(label = "\u2691 "+record+" "+forms_focus[record][0], command = lambda formid=record: self.form_view(formid,0))
            self.formsmenu.add_separator()

        # These are built here so that the flagged primary forms will be at the top
        self.formsmenu.add_cascade(label = '100-199 Informational, Informal, Non-Emergency', menu = self.mcf100)
        self.formsmenu.add_cascade(label = '300-399 Emergency, Exercise, Situation Reports', menu = self.mcf300)
        self.formsmenu.add_cascade(label = '500-599 Surveys, supply availability, weather, etc.', menu = self.mcf500)
        self.formsmenu.add_cascade(label = '700-799 Specific Group and Net', menu = self.mcf700)
        self.formsmenu.add_cascade(label = 'All Other Forms', menu = self.mcfother)

        for record in forms:
            if re.search(r"F\!1[0-9][0-9]",record):
                self.mcf100.add_command(label = record+" "+forms[record][0], command = lambda formid=record: self.form_view(formid,0))
            elif re.search(r"F\!3[0-9][0-9]",record):
                self.mcf300.add_command(label = record+" "+forms[record][0], command = lambda formid=record: self.form_view(formid,0))
            elif re.search(r"F\!5[0-9][0-9]",record):
                self.mcf500.add_command(label = record+" "+forms[record][0], command = lambda formid=record: self.form_view(formid,0))
            elif re.search(r"F\!7[0-9][0-9]",record):
                self.mcf700.add_command(label = record+" "+forms[record][0], command = lambda formid=record: self.form_view(formid,0))
            else:
                self.mcfother.add_command(label = record+" "+forms[record][0], command = lambda formid=record: self.form_view(formid,0))

        self.update()

    ## Re-generate list of forms on system
    def form_refresh(self):
        global forms, forms_focus

        forms_unsorted = {}
        for mcffile in os.scandir('./forms'):
            if mcffile.path.endswith('txt'):
                with open(mcffile) as f:
                    try:
                        first_line = f.readline().strip('\n')
                    except UnicodeDecodeError:
                        messagebox.showinfo("Unicode Error","An unsupported unicode character caused the following form to FAIL: "+str(mcffile.name))
                        continue
                try:
                    forms_unsorted[first_line.split("|")[1]]=(first_line.split("|")[0],mcffile.path)
                except IndexError:
                    # improprly formatted form file, skip it
                    messagebox.showinfo("Form Format Error","Please verify the format of the skipped form: "+str(mcffile.name))
                    continue
                f.close()

        forms.clear()
        for form_item in sorted(forms_unsorted.keys()):
            if form_item in settings['forms_focus'].split(','):
                forms_focus[form_item]=(forms_unsorted[form_item][0],forms_unsorted[form_item][1])
            forms[form_item]=(forms_unsorted[form_item][0],forms_unsorted[form_item][1])

    ## Get form questions and answers, return questions+answers
    def form_items(self,formid):
        global forms
        formdata={}
        formtext={}
        qindex=0

        if formid in forms.keys():
            with open(forms[formid][1]) as form_file:
                for form_line in form_file:

                    if form_line[0]=="!":
                        hv="header1"
                        if form_line[1]=="!": hv="header2"
                        if form_line[2]=="!": hv="header3"

                        if qindex+1 in formtext:
                            formtext[qindex+1].extend([{hv:form_line.partition(" ")[2]}])
                        else:
                            formtext[qindex+1]=[{hv:form_line.partition(" ")[2]}]

                    if form_line[0]==".":
                        if qindex+1 in formtext:
                            formtext[qindex+1].extend([{"text":form_line.partition(" ")[2]}])
                        else:
                            formtext[qindex+1]=[{"text":form_line.partition(" ")[2]}]

                    if form_line[0]=="[" and form_line[3]=="]":
                        qindex+=1
                        formdata[qindex]=[{"prompt":form_line[1]+form_line[2]+form_line.partition(" ")[2]}]

                    if form_line[0]=="?":
                        qindex+=1
                        formdata[qindex]=[{"question":form_line.partition(" ")[2]}]

                    if form_line[0]=="@" and qindex>0:
                        if qindex in formdata:
                            formdata[qindex].extend([{form_line[1]:form_line.partition(" ")[2]}])
        return formdata, formtext

    ## CommStat compatible StatRep forms (Based on CommStat but not using any code from that project)
    def commstat_rx(self):
        # view received statreps
        if settings['statrepgrp'] == "":
            messagebox.showinfo("No CommStat Group","You have not defined a CommStat group name in File > Settings. Without a group or *, no new reports will be captured.")

        totals[3]=0 # Reset counter for status bar notification area

        self.top = Toplevel(self)
        self.top.title("CommStat Status Reports Received")
        self.top.geometry('1000x465')
        self.top.minsize(1000,465)
        self.top.resizable(width=True, height=True)

        self.top.columnconfigure(0, weight=24)
        self.top.columnconfigure(1, weight=1)

        self.top.rowconfigure(0,weight=1)
        self.top.rowconfigure(1,weight=24)
        self.top.rowconfigure(2,weight=1)

        # statRep date/tim range
        self.ftframe = ttk.Frame(self.top)
        self.ftframe.grid(row=0, column=0, columnspan=2, sticky='NSEW', padx=10, pady=(0,5))

        self.ftmark = ttk.Label(self.ftframe, text='View Status Reports:', font=("Segoe Ui Bold", 12))
        self.ftmark.grid(row=0, column = 0, sticky='W', padx=0, pady=(8,0))

        self.drcombo = ttk.Combobox(self.ftframe, values=("All Time","Last 24hrs","Last Week","Last Month","Last Year"), state='readonly')
        self.drcombo.grid(row=0, column =2 , sticky='E', padx=8, pady=(8,0))
        self.drcombo.bind('<<ComboboxSelected>>', self.statreps_selcombo)

        # statrep treeview
        self.statreps = ttk.Treeview(self.top, show='headings')
        self.statreps["columns"]=("from","group","grid","scope","msgid","status","notes","lm")

        self.statreps.column("from", width=60, minwidth=60, stretch=0)
        self.statreps.column("group", width=80, minwidth=80)
        self.statreps.column("grid", width=60, minwidth=60)
        self.statreps.column("scope", width=60, minwidth=60)
        self.statreps.column("msgid", width=60, minwidth=60)
        self.statreps.column("status", width=210, minwidth=210)
        self.statreps.column("notes", width=295, minwidth=295)
        self.statreps.column("lm", width=150, minwidth=150, stretch=0)

        self.statreps.heading("from", text="From", command=lambda c="from": self.sort_treeview(self.statreps, c, False))
        self.statreps.heading("group", text="Group", command=lambda c="group": self.sort_treeview(self.statreps, c, False))
        self.statreps.heading("grid", text="Grid", command=lambda c="grid": self.sort_treeview(self.statreps, c, False))
        self.statreps.heading("scope", text="Scope", command=lambda c="scope": self.sort_treeview(self.statreps, c, False))
        self.statreps.heading("msgid", text="ID", command=lambda c="msgid": self.sort_treeview(self.statreps, c, False))
        self.statreps.heading("status", text="Status")
        self.statreps.heading("notes", text="Remarks")
        self.statreps.heading("lm", text="Received", command=lambda c="lm": self.sort_treeview(self.statreps, c, False))

        self.statreps.bind('<Double-1>', self.show_statrep)
        self.statreps.bind('<Delete>', self.delete_statrep)

        self.statreps.grid(row=1, column=0, sticky='NSEW', padx=(10,0), pady=(10,10))

        self.frscrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.statreps.yview)
        self.statreps.configure(yscroll=self.frscrollbar.set)
        self.frscrollbar.grid(row=1, column=1, sticky='NS', padx=(0,10), pady=(10,10))

        # frame with action items
        self.frframe = ttk.Frame(self.top)
        self.frframe.grid(row=2, column=0, sticky='NSEW')

        self.frexport = ttk.Button(self.frframe, text = 'Export', command = self.export_statreps, width='12')
        self.frexport.grid(row=0, column=1, sticky='NE', padx=(8,8),pady=(8,8))

        self.frforward = ttk.Button(self.frframe, text = 'Forward', width='14', command = self.forward_statrep)
        self.frforward.grid(row=0, column=2, sticky='NE', padx=(8,8),pady=(8,8))

        self.drcombo.set("All Time")
        self.update_statreps()
        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    def update_statreps(self):
        # limit to selected date range
        wheres = ""
        range_selection = self.drcombo.get()
        if range_selection:
            if range_selection!="All Time":
                if wheres=="": wheres = " WHERE "
                if range_selection=="Last 24hrs": wheres+="cssr_timestamp > DATETIME('now', '-24 hour')"
                if range_selection=="Last Week": wheres+="cssr_timestamp > DATETIME('now', '-7 day')"
                if range_selection=="Last Month": wheres+="cssr_timestamp > DATETIME('now', '-31 day')"
                if range_selection=="Last Year": wheres+="cssr_timestamp > DATETIME('now', '-365 day')"

        # clear out the tree
        for entry in self.statreps.get_children():
            self.statreps.delete(entry)

        c.execute("SELECT * FROM csstatrep "+wheres+" ORDER BY cssr_timestamp DESC")
        statrep_lines = c.fetchall()

        count = 0
        for record in statrep_lines:
            sr_date = record[8] # or format, such as: record[7].split(" ")[0]

            if count % 2 == 1:
                self.statreps.insert('', tk.END, iid=record[0], values=(record[1],record[2],record[3],record[4],record[5],record[6],record[7],sr_date), tags=('oddrow'))
            else:
                self.statreps.insert('', tk.END, iid=record[0], values=(record[1],record[2],record[3],record[4],record[5],record[6],record[7],sr_date), tags=('evenrow'))
            count+=1

        if settings['dark_theme'] == "1":
            self.statreps.tag_configure('oddrow', background='#777')
            self.statreps.tag_configure('evenrow', background='#555')
        else:
            self.statreps.tag_configure('oddrow', background='#EEE')
            self.statreps.tag_configure('evenrow', background='#FFF')

    def statreps_selcombo(self, ev):
        self.update_statreps()

    ## Display a selected statrep in a text format
    def show_statrep(self, ev):
        if not self.statreps.focus(): return
        friid = self.statreps.focus()

        if friid == "": return

        c.execute("SELECT * FROM csstatrep WHERE id = '"+friid+"'")
        statrep_db = c.fetchone()

        if statrep_db:
            self.top2 = Toplevel(self)
            self.top2.title("CommStat Status Report")
            self.top2.geometry('650x600')

            # display window
            self.export_text = Text(self.top2, wrap=NONE, font='TkFixedFont')
            fr_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
            self.export_text.configure(yscroll=fr_scrollbar.set)
            fr_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(10,10))

            # save and copy buttons
            tlframe = ttk.Frame(self.top2)
            tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
            self.top2.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
            self.top2.copy_button.pack(side=LEFT, padx=(0,10))
            self.top2.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
            self.top2.saveas_button.pack(side=RIGHT)

            self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(10,10))

            # right-click action
            self.rcmenu = Menu(self.top2, tearoff = 0)
            self.rcmenu.add_command(label = 'Copy')
            self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

            # statrep specific formatting
            if statrep_db[4]=="1": sr_scope = "My Location (1)"
            if statrep_db[4]=="2": sr_scope = "My Community (2)"
            if statrep_db[4]=="3": sr_scope = "My County (3)"
            if statrep_db[4]=="4": sr_scope = "My Region (4)"
            if statrep_db[4]=="5": sr_scope = "Other (5)"

            cs_stypes = ["Overall status","Commercial Power","Public Water","Medical","Over Air Comms","Travel Conditions","Internet","Fuel","Food","Criminal Activity","Civil","Political"]
            cs_slevels = ["Green (1)","Yellow (2)","Red (3)", "Unknown (4)"]
            cs_snum = 0
            cs_statusinfo = ""

            for cs_stat in statrep_db[6]:
                stat_div = " " * (23-len(cs_stypes[int(cs_snum)]))
                try:
                    cs_statusinfo += "  "+cs_stypes[int(cs_snum)]+": "+stat_div+cs_slevels[int(cs_stat)-1]+"\n"
                except:
                    cs_statusinfo += "  "+cs_stypes[int(cs_snum)]+": "+stat_div+"(Raw Data: "+str(cs_stat)+")\n"
                cs_snum+=1

            fr_contents = "CommStat Format Status Report\n\n"
            fr_contents += "Received:     "+statrep_db[8]+"\n"
            fr_contents += "FROM Station: "+statrep_db[1]+"\n"
            fr_contents += "TO Group:     "+statrep_db[2]+"\n"
            fr_contents += "Grid:         "+statrep_db[3]+"\n"
            fr_contents += "Scope:        "+sr_scope+"\n"
            fr_contents += "ID:           "+statrep_db[5]+"\n\n"
            fr_contents += "Status Items\n\n"+cs_statusinfo+"\n"
            fr_contents += "Remarks:\n"+statrep_db[7]

            self.export_text.insert(tk.END, fr_contents)
            self.export_text.configure(state='disabled')

            self.top2.wait_visibility()
            self.top2.grab_set()
            self.top2.focus_set()
            self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    def delete_statrep(self, ev):
        frlist = ""
        for friid in self.statreps.selection():
            frlist += "DBID ["+friid+"] from "+str(self.statreps.item(friid)['values'][0])+" received "+str(self.statreps.item(friid)['values'][7])+"\n"

        if frlist == "": return

        msgtxt = "Remove the following status report(s)? This action cannot be undone.\n\n"+frlist
        answer = askyesno(title='Remove Status Report(s)?', message=msgtxt, parent=self.top)
        if answer:
            for friid in self.statreps.selection():
                c.execute("DELETE FROM csstatrep WHERE id = ?", [friid])
            conn.commit()
            self.update_statreps()

    def export_statreps(self):
        # limit to selected date range
        wheres = ""
        range_selection = self.drcombo.get()
        if range_selection:
            if range_selection!="All Time":
                if wheres=="": wheres = " WHERE "
                if range_selection=="Last 24hrs": wheres+="cssr_timestamp > DATETIME('now', '-24 hour')"
                if range_selection=="Last Week": wheres+="cssr_timestamp > DATETIME('now', '-7 day')"
                if range_selection=="Last Month": wheres+="cssr_timestamp > DATETIME('now', '-31 day')"
                if range_selection=="Last Year": wheres+="cssr_timestamp > DATETIME('now', '-365 day')"

        c.execute("SELECT * FROM csstatrep "+wheres+" ORDER BY cssr_timestamp DESC")
        statrep_lines = c.fetchall()

        if statrep_lines:
            self.top2 = Toplevel(self)
            self.top2.title("CommStat Status Report Export")
            self.top2.geometry('650x600')

            # display window
            self.export_text = Text(self.top2, wrap=NONE, font='TkFixedFont')
            fr_scrollbar = ttk.Scrollbar(self.top2, orient=tk.VERTICAL, command=self.export_text.yview)
            self.export_text.configure(yscroll=fr_scrollbar.set)
            fr_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(10,10))

            # save and copy buttons
            tlframe = ttk.Frame(self.top2)
            tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
            self.top2.copy_button = ttk.Button(tlframe, text = 'Copy All', command = self.export_copy_all)
            self.top2.copy_button.pack(side=LEFT, padx=(0,10))
            self.top2.saveas_button = ttk.Button(tlframe, text = 'Save As', command = self.export_saveas_popup)
            self.top2.saveas_button.pack(side=RIGHT)

            self.export_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(10,10))

            # right-click action
            self.rcmenu = Menu(self.top2, tearoff = 0)
            self.rcmenu.add_command(label = 'Copy')
            self.export_text.bind('<Button-3>', lambda ev: self.export_copy_popup(ev))

            # loop through form responses to build export
            export_contents = ""
            for record in statrep_lines:
                for i in record:
                    export_contents+=str(i)+chr(9)
                export_contents+="\n"

            self.export_text.insert(tk.END, export_contents)
            self.export_text.configure(state='disabled')

            self.top2.wait_visibility()
            self.top2.grab_set()
            self.top2.focus_set()
            self.top2.bind('<Escape>', lambda x: self.top2.destroy())
        else:
            messagebox.showinfo("No Status Reports","Couldn't find any status reports to export.", parent=self.top)

    def forward_statrep(self):
        if not self.statreps.focus(): return

        self.top2 = Toplevel(self)
        self.top2.title("Forward Statrep")
        self.top2.resizable(width=False, height=False)

        label_new = ttk.Label(self.top2, text = "Forward to:")
        label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.fwdsrto = ttk.Entry(self.top2, width='34')
        self.fwdsrto.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
        self.fwdsrto.bind("<KeyRelease>", lambda x: self.update_forwardsr())
        self.fwdsrto.insert(0,settings['statrepgrp'])

        self.sms_cmd = ttk.Entry(self.top2)
        self.sms_cmd.grid(row = 2, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top2)
        cbframe.grid(row=3, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd) # proc_aprscmd may be used to send from any fuction using a sms_cmd entry box
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top2.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.update_forwardsr()
        self.top2.wait_visibility()
        self.top2.grab_set()
        self.top2.focus_set()
        self.fwdsrto.focus()
        self.top2.bind('<Escape>', lambda x: self.top2.destroy())

    def update_forwardsr(self):
        friid = self.statreps.focus()
        if friid == "": return

        c.execute("SELECT * FROM csstatrep WHERE id = '"+friid+"'")
        statrep_db = c.fetchone()

        if statrep_db:
            fwdto = self.fwdsrto.get().strip()
            if fwdto=="":
                self.sms_cmd.delete(0,END)
                return

            # Generate statrep forward format, based on commstat v1.0.5
            # example: @TST11  ,EM48,1,959,111111111111,NTR,KF7MIX,{F%}
            new_cmd = fwdto
            new_cmd += " ,"+ statrep_db[3]
            new_cmd += ","+ statrep_db[4]
            new_cmd += ","+ statrep_db[5]
            new_cmd += ","+ statrep_db[6]
            new_cmd += ","+ statrep_db[7]
            new_cmd += ","+ statrep_db[1]
            new_cmd += ",{F%}"

            self.sms_cmd.delete(0,END)
            self.sms_cmd.insert(0,new_cmd)

    ## Fill out and send a CommStat style StatRep
    def commstat_tx(self):

        if settings['statrepgrp'] == "":
            messagebox.showinfo("No CommStat Group","You should define a CommStat group in File > Settings. You may TX a statrep, but won't receive and store without a defined group or *.")

        self.top = Toplevel(self)
        self.top.title("CommStat Status Report")
        self.top.resizable(width=False, height=False)

        # Message core info entry
        label_new = ttk.Label(self.top, text = "Group")
        label_new.grid(row = 0, column = 0, sticky=W, padx=(10,0), pady=(20,0))
        self.csstat_grp = ttk.Entry(self.top, width='16')
        self.csstat_grp.grid(row = 0, column = 1, sticky=W, padx=(0,10), pady=(20,0))
        self.csstat_grp.bind("<KeyRelease>", lambda x: self.update_csstat())
        self.csstat_grp.insert(0,settings['statrepgrp'])

        label_new = ttk.Label(self.top, text = "Grid")
        label_new.grid(row = 0, column = 2, sticky=W, padx=(10,0), pady=(20,0))
        self.csstat_grid = ttk.Entry(self.top, width='16')
        self.csstat_grid.grid(row = 0, column = 3, sticky=W, padx=(0,10), pady=(20,0))
        self.csstat_grid.bind("<KeyRelease>", lambda x: self.update_csstat())
        self.csstat_grid.insert(0,settings['grid'])

        label_new = ttk.Label(self.top, text = "Scope")
        label_new.grid(row = 0, column = 4, sticky=W, padx=(10,0), pady=(20,0))
        self.scopesel = ttk.Combobox(self.top, values=("1: My Location","2: My Community","3: My County","4: My Region", "5: Other"), state='readonly', width='16')
        self.scopesel.grid(row = 0, column = 5, sticky=W, padx=(10,0), pady=(20,0))
        self.scopesel.current(0)
        self.scopesel.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "ID")
        label_new.grid(row = 0, column = 6, sticky=W, padx=(10,0), pady=(20,0))
        self.csstat_id = ttk.Entry(self.top, width='16')
        self.csstat_id.grid(row = 0, column = 7, sticky=W, padx=(0,10), pady=(20,0))
        self.csstat_id.bind("<KeyRelease>", lambda x: self.update_csstat())
        self.csstat_id.insert(0,random.randint(100, 999))

        # Status report items, row 1/3 (12 total, 4/row)
        statrepopts = ["1: Green", "2: Yellow", "3: Red", "4: Unknown"]

        label_new = ttk.Label(self.top, text = "Overall Status")
        label_new.grid(row = 1, column = 0, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp1 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp1.grid(row = 1, column = 1, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp1.current(0)
        self.statresp1.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Commercial Power")
        label_new.grid(row = 1, column = 2, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp2 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp2.grid(row = 1, column = 3, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp2.current(0)
        self.statresp2.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Public Water")
        label_new.grid(row = 1, column = 4, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp3 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp3.grid(row = 1, column = 5, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp3.current(0)
        self.statresp3.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Medical")
        label_new.grid(row = 1, column = 6, sticky=W, padx=(0,10), pady=(20,0))
        self.statresp4 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp4.grid(row = 1, column = 7, sticky=W, padx=(0,10), pady=(20,0))
        self.statresp4.current(0)
        self.statresp4.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        # Status row 2/3
        label_new = ttk.Label(self.top, text = "Over Air Comms")
        label_new.grid(row = 2, column = 0, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp5 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp5.grid(row = 2, column = 1, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp5.current(0)
        self.statresp5.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Travel Conditions")
        label_new.grid(row = 2, column = 2, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp6 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp6.grid(row = 2, column = 3, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp6.current(0)
        self.statresp6.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Internet")
        label_new.grid(row = 2, column = 4, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp7 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp7.grid(row = 2, column = 5, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp7.current(0)
        self.statresp7.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Fuel")
        label_new.grid(row = 2, column = 6, sticky=W, padx=(0,10), pady=(20,0))
        self.statresp8 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp8.grid(row = 2, column = 7, sticky=W, padx=(0,10), pady=(20,0))
        self.statresp8.current(0)
        self.statresp8.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        # Status row 3/3
        label_new = ttk.Label(self.top, text = "Food")
        label_new.grid(row = 3, column = 0, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp9 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp9.grid(row = 3, column = 1, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp9.current(0)
        self.statresp9.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Criminal Activity")
        label_new.grid(row = 3, column = 2, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp10 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp10.grid(row = 3, column = 3, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp10.current(0)
        self.statresp10.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Civil")
        label_new.grid(row = 3, column = 4, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp11 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp11.grid(row = 3, column = 5, sticky=W, padx=(10,0), pady=(20,0))
        self.statresp11.current(0)
        self.statresp11.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        label_new = ttk.Label(self.top, text = "Political")
        label_new.grid(row = 3, column = 6, sticky=W, padx=(0,10), pady=(20,0))
        self.statresp12 = ttk.Combobox(self.top, values=statrepopts, state='readonly', width='16')
        self.statresp12.grid(row = 3, column = 7, sticky=W, padx=(0,10), pady=(20,0))
        self.statresp12.current(0)
        self.statresp12.bind("<<ComboboxSelected>>", lambda x: self.update_csstat())

        # Remarks
        label_new = ttk.Label(self.top, text = "Brief Remarks")
        label_new.grid(row = 4, column = 0, sticky=W, padx=(10,0), pady=(20,0))
        self.csstat_rem = ttk.Entry(self.top, width='32')
        self.csstat_rem.grid(row = 4, column = 1, columnspan=3, sticky='EW', padx=(10,0), pady=(20,0))
        self.csstat_rem.bind("<KeyRelease>", lambda x: self.update_csstat())

        # Entry box where command will be built
        self.cs_cmd = ttk.Entry(self.top)
        self.cs_cmd.grid(row = 5, column = 0, columnspan=4, sticky='EW', padx=(10,0), pady=(20,20))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=5, column = 2, columnspan=4, sticky='e', padx=(10,0),pady=(0,0))

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_commstat)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.update_csstat()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    # detect a change in statrep fields and update send string
    def update_csstat(self):
        csgroup = self.csstat_grp.get().strip()
        cscomment = self.csstat_rem.get().strip()
        csgrid = self.csstat_grid.get().strip()
        csscope = str(self.scopesel.current()+1)
        csid = self.csstat_id.get().strip()

        csstatus = str(self.statresp1.current()+1)
        csstatus += str(self.statresp2.current()+1)
        csstatus += str(self.statresp3.current()+1)
        csstatus += str(self.statresp4.current()+1)
        csstatus += str(self.statresp5.current()+1)
        csstatus += str(self.statresp6.current()+1)
        csstatus += str(self.statresp7.current()+1)
        csstatus += str(self.statresp8.current()+1)
        csstatus += str(self.statresp9.current()+1)
        csstatus += str(self.statresp10.current()+1)
        csstatus += str(self.statresp11.current()+1)
        csstatus += str(self.statresp12.current()+1)

        if csgroup=="" or csid=="" or csgrid=="" or csscope=="":
            self.cs_cmd.delete(0,END)
            return

        # format @GROUPNAME ,EM48,1,501,111111111111,Test,{&%}
        cs_cmd_string = csgroup+" ,"+csgrid+","+csscope+","+csid+","+csstatus+","+cscomment+",{&%}"
        self.cs_cmd.delete(0,END)
        self.cs_cmd.insert(0,cs_cmd_string)

    ## Send a basic CommStat compatible net checkin
    def commstat_checkin(self):
        self.top = Toplevel(self)
        self.top.title("CommStat Net Checkin")
        self.top.resizable(width=False, height=False)

        # Format: "@group ," + comments + "," + state + "," + grid + ",{~%}"
        label_new = ttk.Label(self.top, text = "Group")
        label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.cscheck_grp = ttk.Entry(self.top, width='34')
        self.cscheck_grp.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
        self.cscheck_grp.bind("<KeyRelease>", lambda x: self.update_cscheckin())
        self.cscheck_grp.insert(0,settings['statrepgrp'])

        label_new = ttk.Label(self.top, text = "Comments")
        label_new.grid(row = 1, column = 0, padx=(10,0), pady=(10,0))
        self.cscheck_comment = ttk.Entry(self.top, width='34')
        self.cscheck_comment.grid(row = 1, column = 1, padx=(0,10), pady=(10,0))
        self.cscheck_comment.bind("<KeyRelease>", lambda x: self.update_cscheckin())

        label_new = ttk.Label(self.top, text = "State (2 char abbr.)")
        label_new.grid(row = 2, column = 0, padx=(10,0), pady=(10,0))
        self.cscheck_state = ttk.Entry(self.top, width='34')
        self.cscheck_state.grid(row = 2, column = 1, padx=(0,10), pady=(10,0))
        self.cscheck_state.bind("<KeyRelease>", lambda x: self.update_cscheckin())

        label_new = ttk.Label(self.top, text = "Grid")
        label_new.grid(row = 3, column = 0, padx=(10,0), pady=(10,0))
        self.cscheck_grid = ttk.Entry(self.top, width='34')
        self.cscheck_grid.grid(row = 3, column = 1, padx=(0,10), pady=(10,0))
        self.cscheck_grid.bind("<KeyRelease>", lambda x: self.update_cscheckin())
        self.cscheck_grid.insert(0,settings['grid'])

        self.cs_cmd = ttk.Entry(self.top)
        self.cs_cmd.grid(row = 4, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=5, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_commstat)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.cscheck_comment.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated commstat checkin cmd string on keypress
    def update_cscheckin(self):
        csgroup = self.cscheck_grp.get().strip()
        cscomment = self.cscheck_comment.get().strip()
        csstate = self.cscheck_state.get().strip()
        csgrid = self.cscheck_grid.get().strip()
        if csgroup=="" or cscomment=="" or csstate=="" or csgrid=="":
            self.cs_cmd.delete(0,END)
            return
        cs_cmd_string = csgroup+" ,"+cscomment+","+csstate+","+csgrid+",{~%}"
        self.cs_cmd.delete(0,END)
        self.cs_cmd.insert(0,cs_cmd_string)

    def proc_commstat(self):
        new_cmd = self.cs_cmd.get()
        if new_cmd == "": return

        # make sure the message pane is empty
        tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        time.sleep(0.33)

        tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":new_cmd})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        self.top.destroy()

    ## Send APRS SMS (http://aprs.wiki/SMS/ -- ONLINE OPT IN REQUIRED to receieve SMS!!!)
    def aprs_sms(self):
        self.top = Toplevel(self)
        self.top.title("APRS: Send SMS Text")
        self.top.resizable(width=False, height=False)

        label_new = ttk.Label(self.top, text = "Phone numbers must be registered at http://aprs.wiki/SMS/")
        label_new.grid(row = 0, column = 0, columnspan=2, padx=(10,0), pady=(20,0))

        label_new = ttk.Label(self.top, text = "Phone or Alias")
        label_new.grid(row = 1, column = 0, padx=(10,0), pady=(20,0))
        self.sms_phone = ttk.Entry(self.top, width='34')
        self.sms_phone.grid(row = 1, column = 1, padx=(0,10), pady=(20,0))
        self.sms_phone.bind("<KeyRelease>", lambda x: self.update_aprssms())

        label_new = ttk.Label(self.top, text = "Message (32 char)")
        label_new.grid(row = 2, column = 0, padx=(10,0), pady=(10,0))
        self.sms_msg = ttk.Entry(self.top, width='34')
        self.sms_msg.grid(row = 2, column = 1, padx=(0,10), pady=(10,0))
        self.sms_msg.bind("<KeyRelease>", lambda x: self.update_aprssms())

        self.sms_cmd = ttk.Entry(self.top)
        self.sms_cmd.grid(row = 3, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=4, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.sms_phone.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated APRS cmd string on keypress
    def update_aprssms(self):
        phone = self.sms_phone.get().strip()
        #phone = re.sub("[^0-9]","",phone) # aliases may be used instead, no need to process input
        msg = self.sms_msg.get().strip()
        if phone=="" or msg=="":
            self.sms_cmd.delete(0,END)
            return
#        aprs_cmd = "@APRSIS CMD :SMSGTE   :@"+phone+" "+msg+"{01}" # old version, retain in code in case it re-activates or for reference
        aprs_cmd = "@APRSIS CMD :SMS      :@"+phone+" "+msg+"{01}"

        self.sms_cmd.delete(0,END)
        self.sms_cmd.insert(0,aprs_cmd)

    ## Send APRS WhatsAPP (See https://wtsapp.org/)
    def aprs_wts(self):
        self.top = Toplevel(self)
        self.top.title("APRS: Send WhatsApp Message")
        self.top.resizable(width=False, height=False)

        label_new = ttk.Label(self.top, text = "WhatsApp numbers start with + no spaces or dashes")
        label_new.grid(row = 0, column = 0, columnspan=2, padx=(10,0), pady=(20,0))

        label_new = ttk.Label(self.top, text = "Number")
        label_new.grid(row = 1, column = 0, padx=(10,0), pady=(20,0))
        self.sms_phone = ttk.Entry(self.top, width='34')
        self.sms_phone.grid(row = 1, column = 1, padx=(0,10), pady=(20,0))
        self.sms_phone.bind("<KeyRelease>", lambda x: self.update_aprswts())

        label_new = ttk.Label(self.top, text = "Message (32 char)")
        label_new.grid(row = 2, column = 0, padx=(10,0), pady=(10,0))
        self.sms_msg = ttk.Entry(self.top, width='34')
        self.sms_msg.grid(row = 2, column = 1, padx=(0,10), pady=(10,0))
        self.sms_msg.bind("<KeyRelease>", lambda x: self.update_aprswts())

        self.sms_cmd = ttk.Entry(self.top)
        self.sms_cmd.grid(row = 3, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=4, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.sms_phone.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated APRS cmd string on keypress
    def update_aprswts(self):
        phone = self.sms_phone.get().strip()
        #phone = re.sub("[^0-9]","",phone) # aliases may be used instead, no need to process input
        msg = self.sms_msg.get().strip()
        if phone=="" or msg=="":
            self.sms_cmd.delete(0,END)
            return
        aprs_cmd = "@APRSIS CMD :WTSAPP   :@"+phone+" "+msg

        self.sms_cmd.delete(0,END)
        self.sms_cmd.insert(0,aprs_cmd)

    ## Send APRS message (not email or SMS, but direct through APRS system only)
    def aprs_msg(self):
        self.top = Toplevel(self)
        self.top.title("APRS: Send Message")
        self.top.resizable(width=False, height=False)

        label_new = ttk.Label(self.top, text = "For simple APRS-Only messages")
        label_new.grid(row = 0, column = 0, columnspan=2, padx=(10,0), pady=(20,0))

        label_new = ttk.Label(self.top, text = "Target Station")
        label_new.grid(row = 1, column = 0, padx=(10,0), pady=(20,0))
        self.sms_target = ttk.Entry(self.top, width='34')
        self.sms_target.grid(row = 1, column = 1, padx=(0,10), pady=(20,0))
        self.sms_target.bind("<KeyRelease>", lambda x: self.update_aprsmsg())

        label_new = ttk.Label(self.top, text = "Message (64 char)")
        label_new.grid(row = 2, column = 0, padx=(10,0), pady=(10,0))
        self.sms_msg = ttk.Entry(self.top, width='34')
        self.sms_msg.grid(row = 2, column = 1, padx=(0,10), pady=(10,0))
        self.sms_msg.bind("<KeyRelease>", lambda x: self.update_aprsmsg())

        self.sms_cmd = ttk.Entry(self.top)
        self.sms_cmd.grid(row = 3, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=4, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.sms_target.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated APRS cmd string on keypress
    def update_aprsmsg(self):
        target = self.sms_target.get().strip()
        target = '{:<9}'.format(target[:9])

        msg = self.sms_msg.get().strip()
        if target=="" or msg=="":
            self.sms_cmd.delete(0,END)
            return
        aprs_cmd = "@APRSIS CMD :"+target+":"+msg+"{05}"

        self.sms_cmd.delete(0,END)
        self.sms_cmd.insert(0,aprs_cmd)

    ## Send APRS email
    def aprs_email(self):
        self.top = Toplevel(self)
        self.top.title("APRS: Send Email")
        self.top.resizable(width=False, height=False)

        label_new = ttk.Label(self.top, text = "Email")
        label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.sms_email = ttk.Entry(self.top, width='34')
        self.sms_email.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
        self.sms_email.bind("<KeyRelease>", lambda x: self.update_aprsemail())

        label_new = ttk.Label(self.top, text = "Message")
        label_new.grid(row = 1, column = 0, padx=(10,0), pady=(10,0))
        self.sms_msg = ttk.Entry(self.top, width='34')
        self.sms_msg.grid(row = 1, column = 1, padx=(0,10), pady=(10,0))
        self.sms_msg.bind("<KeyRelease>", lambda x: self.update_aprsemail())

        self.sms_cmd = ttk.Entry(self.top)
        self.sms_cmd.grid(row = 2, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=3, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.sms_email.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated aprs cmd string on keypress
    def update_aprsemail(self):
        email = self.sms_email.get().strip()
        msg = self.sms_msg.get().strip()
        if email=="" or msg=="":
            self.sms_cmd.delete(0,END)
            return
        aprs_cmd = "@APRSIS CMD :EMAIL-2  :"+email+" "+msg+"{01}"
        self.sms_cmd.delete(0,END)
        self.sms_cmd.insert(0,aprs_cmd)

    ## Report grid to APRS system
    def aprs_grid(self):
        self.top = Toplevel(self)
        self.top.title("APRS: Report Grid Location")
        self.top.resizable(width=False, height=False)

        label_new = ttk.Label(self.top, text = "Grid Location")
        label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.aprs_grid = ttk.Entry(self.top, width='34')
        self.aprs_grid.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
        self.aprs_grid.bind("<KeyRelease>", lambda x: self.update_aprsgrid())
        self.aprs_grid.insert(0,settings['grid'])

        self.sms_cmd = ttk.Entry(self.top)
        self.sms_cmd.grid(row = 2, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=3, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.update_aprsgrid()
        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.aprs_grid.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated APRS cmd string on keypress
    def update_aprsgrid(self):
        grid = self.aprs_grid.get().strip()
        if grid=="":
            self.sms_cmd.delete(0,END)
            return
        aprs_cmd = "@APRSIS GRID "+grid
        self.sms_cmd.delete(0,END)
        self.sms_cmd.insert(0,aprs_cmd)


    ## Send APRS POTAGW data
    def aprs_pota(self):
        self.top = Toplevel(self)
        self.top.title("APRS: POTA Gateway")
        self.top.resizable(width=False, height=False)

        # Input PARK,Frequency(KHz),Mode,Comments
        label_new = ttk.Label(self.top, text = "Park")
        label_new.grid(row = 0, column = 0, padx=(10,0), pady=(20,0))
        self.pota_park = ttk.Entry(self.top, width='34')
        self.pota_park.grid(row = 0, column = 1, padx=(0,10), pady=(20,0))
        self.pota_park.bind("<KeyRelease>", lambda x: self.update_aprspota())

        label_new = ttk.Label(self.top, text = "Freq (KHz)")
        label_new.grid(row = 1, column = 0, padx=(10,0), pady=(10,0))
        self.pota_freq = ttk.Entry(self.top, width='34')
        self.pota_freq.grid(row = 1, column = 1, padx=(0,10), pady=(10,0))
        self.pota_freq.bind("<KeyRelease>", lambda x: self.update_aprspota())

        label_new = ttk.Label(self.top, text = "Mode")
        label_new.grid(row = 2, column = 0, padx=(10,0), pady=(10,0))
        self.pota_mode = ttk.Entry(self.top, width='34')
        self.pota_mode.grid(row = 2, column = 1, padx=(0,10), pady=(10,0))
        self.pota_mode.bind("<KeyRelease>", lambda x: self.update_aprspota())

        label_new = ttk.Label(self.top, text = "Comments")
        label_new.grid(row = 3, column = 0, padx=(10,0), pady=(10,0))
        self.pota_comm = ttk.Entry(self.top, width='34')
        self.pota_comm.grid(row = 3, column = 1, padx=(0,10), pady=(10,0))
        self.pota_comm.bind("<KeyRelease>", lambda x: self.update_aprspota())

        self.sms_cmd = ttk.Entry(self.top)
        self.sms_cmd.grid(row = 4, column = 0, columnspan=2, stick='NSEW', padx=(10,10), pady=(20,0))

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=5, columnspan=2, sticky='e', padx=10)

        create_button = ttk.Button(cbframe, text = "Send", command = self.proc_aprscmd)
        create_button.grid(row=0, column = 1, padx=(10,0), pady=(20,20))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 2, padx=(10,0), pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.pota_park.focus()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Update generated aprs cmd string on keypress
    def update_aprspota(self):
        park = self.pota_park.get().strip()
        freq = self.pota_freq.get().strip()
        mode = self.pota_mode.get().strip()
        comm = self.pota_comm.get().strip()
        if park=="" or freq=="" or mode=="":
            self.sms_cmd.delete(0,END)
            return
        aprs_cmd = "@APRSIS CMD :POTAGW   :"+settings['callsign']+" "+park+" "+freq+" "+mode+" "+comm
        self.sms_cmd.delete(0,END)
        self.sms_cmd.insert(0,aprs_cmd)

    ## Process (send/tx) APRS cmd
    def proc_aprscmd(self):
        new_cmd = self.sms_cmd.get()
        if new_cmd == "": return

        # make sure the message pane is empty
        tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        time.sleep(0.33)

        tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":new_cmd})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        self.top.destroy()

    ## Show a simple text help file for in-application help
    def showhelp(self):
        self.top = Toplevel(self)
        self.top.title("JS8Spotter Help")
        self.top.geometry('650x500')

         # display window
        self.help_text = Text(self.top, wrap=NONE)
        help_scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.help_text.yview)
        self.help_text.configure(yscroll=help_scrollbar.set)
        help_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(10,10))
        self.help_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(10,10))

        help_file = open("HELP.txt", "r")
        help_contents = help_file.read()
        help_file.close()

        self.help_text.insert(tk.END, help_contents)
        self.help_text.configure(state='disabled')

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Edit user settings
    def settings_edit(self):
        global settings

        self.top = Toplevel(self)
        self.top.title("Edit Settings")
        self.top.resizable(width=False, height=False)

        # dropping this here... test an API call when opening the settings dialog, for TESTING only of course
        #tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
        #self.sock.send(bytes(tx_content + '\n','utf-8'))
        #time.sleep(0.25)

        label_instruct = ttk.Label(self.top, text = "Please check that these settings match in JS8Call.")
        label_instruct.grid(row = 0, columnspan = 2, padx=(10,10), pady=(20,0))

        label_call = ttk.Label(self.top, text = "Your Callsign")
        label_call.grid(row = 1, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_call = ttk.Entry(self.top)
        self.edit_call.insert(0, settings['callsign'])
        self.edit_call.grid(row = 1, column = 1, padx=(0,10), pady=(20,0))
        self.edit_call.bind("<Return>", lambda x: self.proc_settings_edit())

        label_grid = ttk.Label(self.top, text = "Your GRID")
        label_grid.grid(row = 2, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_grid = ttk.Entry(self.top)
        self.edit_grid.insert(0, settings['grid'])
        self.edit_grid.grid(row = 2, column = 1, padx=(0,10), pady=(10,0))
        self.edit_grid.bind("<Return>", lambda x: self.proc_settings_edit())

        label_address = ttk.Label(self.top, text = "IP Address (127.0.0.1)")
        label_address.grid(row = 3, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_address = ttk.Entry(self.top)
        self.edit_address.insert(0, settings['tcp_ip'])
        self.edit_address.grid(row = 3, column = 1, padx=(0,10), pady=(20,0))
        self.edit_address.bind("<Return>", lambda x: self.proc_settings_edit())

        label_port = ttk.Label(self.top, text = "TCP Port (2442)")
        label_port.grid(row = 4, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_port = ttk.Entry(self.top)
        self.edit_port.insert(0, settings['tcp_port'])
        self.edit_port.grid(row = 4, column = 1, padx=(0,10), pady=(10,0))
        self.edit_port.bind("<Return>", lambda x: self.proc_settings_edit())

        label_srg = ttk.Label(self.top, text = "CommStat Group (or blank, or *)")
        label_srg.grid(row = 5, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_srg = ttk.Entry(self.top)
        self.edit_srg.insert(0, settings['statrepgrp'])
        self.edit_srg.grid(row = 5, column = 1, padx=(0,10), pady=(10,0))
        self.edit_srg.bind("<Return>", lambda x: self.proc_settings_edit())

        label_eda = ttk.Label(self.top, text = "Default Expect Allow")
        label_eda.grid(row = 6, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_eda = ttk.Entry(self.top)
        self.edit_eda.insert(0, settings['exp_def_allow'])
        self.edit_eda.grid(row = 6, column = 1, padx=(0,10), pady=(10,0))
        self.edit_eda.bind("<Return>", lambda x: self.proc_settings_edit())

        label_epf = ttk.Label(self.top, text = "Primary Forms")
        label_epf.grid(row = 7, column = 0, sticky=W, padx=(10,10), pady=(10,0))
        self.edit_epf = ttk.Entry(self.top)
        self.edit_epf.insert(0, settings['forms_focus'])
        self.edit_epf.grid(row = 7, column = 1, padx=(0,10), pady=(10,0))
        self.edit_epf.bind("<Return>", lambda x: self.proc_settings_edit())

        cbframe = ttk.Frame(self.top)
        cbframe.grid(row=8, columnspan=2, sticky='NSEW', padx=10)

        save_button = ttk.Button(cbframe, text = "Save", command = self.proc_settings_edit)
        save_button.grid(row=0, column = 0, padx=(60,10), pady=(10,10))
        cancel_button = ttk.Button(cbframe, text = "Cancel", command = self.top.destroy)
        cancel_button.grid(row=0, column = 1, pady=(20,20))

        self.top.wait_visibility()
        self.top.grab_set()
        self.top.focus_set()
        self.top.bind('<Escape>', lambda x: self.top.destroy())

    ## Process user settings edit
    def proc_settings_edit(self):
        global settings
        new_addr = self.edit_address.get()
        new_port = self.edit_port.get()
        new_call = self.edit_call.get().upper()
        new_grid = self.edit_grid.get().upper()
        new_srg = self.edit_srg.get().upper()
        new_eda = self.edit_eda.get().upper()
        new_epf = self.edit_epf.get().upper()

        restart_required=0
        if new_addr!=settings['tcp_ip'] or new_port!=settings['tcp_port'] or new_epf!=settings['forms_focus']:
            restart_required=1

        # validate settings
        if new_addr == "" or new_port == "" or new_call == "" or new_grid == "":
            messagebox.showinfo("Error","Please complete all fields", parent=self.top)
            return

        if new_port.isnumeric() == False:
            messagebox.showinfo("Error","Port must be a number (1-9999)", parent=self.top)
            return

        if int(new_port) < 1 or int(new_port) > 9999: #9999 is js8call settings interface limit
            messagebox.showinfo("Error","Port must be between 1 and 9999", parent=self.top)
            return

        if self.check_ip(new_addr) == False:
            messagebox.showinfo("Error","The IP address ("+new_addr+") is formatted incorrectly", parent=self.top)
            return

        if (new_srg != "") and (new_srg[0] != "@") and (new_srg != "*"):
            messagebox.showinfo("Error","CommStat group must be either a group starting with @, blank, or * for all.", parent=self.top)
            return

        if (new_eda == ""):
            new_eda = "*"

        # checks passed, save and update
        c.execute("UPDATE setting SET value = ? WHERE name = 'tcp_ip'", [new_addr])
        c.execute("UPDATE setting SET value = ? WHERE name = 'tcp_port'", [new_port])
        c.execute("UPDATE setting SET value = ? WHERE name = 'callsign'", [new_call])
        c.execute("UPDATE setting SET value = ? WHERE name = 'grid'", [new_grid])
        c.execute("UPDATE setting SET value = ? WHERE name = 'statrepgrp'", [new_srg])
        c.execute("UPDATE setting SET value = ? WHERE name = 'exp_def_allow'", [new_eda])
        c.execute("UPDATE setting SET value = ? WHERE name = 'forms_focus'", [new_epf])
        conn.commit()

        settings['tcp_ip']=new_addr
        settings['tcp_port']=new_port
        settings['callsign']=new_call
        settings['grid']=new_grid
        settings['statrepgrp']=new_srg
        settings['exp_def_allow']=new_eda
        settings['forms_focus']=new_epf

        if restart_required==1:
            messagebox.showinfo("Restart Required","Changes to IP address, TCP Port, or Primary Forms will take effect when you restart the program.")

        self.top.destroy()

    # Sort any bound treeview
    def sort_treeview(self, tree, col, sorder):
        if col=="snr":
            treeitems = [(int(tree.set(item, col)), item) for item in tree.get_children('')]
        else:
            treeitems = [(tree.set(item, col), item) for item in tree.get_children('')]
        treeitems.sort(reverse=sorder)

        # these search_records are only used when they are sorting the search terms screen
        c.execute("SELECT * FROM search WHERE profile_id = ? ORDER BY last_seen DESC", [current_profile_id])
        search_records = c.fetchall()
        search_dict = {item[0]: item[1:] for item in search_records}

        count = 0
        for index, (val, item) in enumerate(treeitems):
            tree.move(item, '', index)
            if count % 2 == 1:
                tree.item(item, tags=('oddrow'))
            else:
                tree.item(item, tags=('evenrow'))
            count+=1

            # highlight if within selected highlight range (search terms screen only)
            if isinstance(item, int):
                if int(item) in search_dict:
                    if isinstance(search_dict[int(item)][2],str):
#                        recdelta = datetime.datetime.utcnow() - datetime.datetime.strptime(search_dict[int(item)][2], "%Y-%m-%d %H:%M:%S") # depricated utcnow
                        recdelta = datetime.datetime.now(datetime.UTC) - datetime.datetime.strptime(search_dict[int(item)][2], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)

                        rdmin = int(recdelta.total_seconds() / 60)
                        if rdmin < int(settings['highlight_new']):
                            if count % 2 == 1:
                                self.keywords.item(item, tags="hlorow")
                            else:
                                self.keywords.item(item, tags="hlerow")

        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not sorder))

    ## Basic database trim
    def proc_dbtrim(self):
        msgtxt = "This action will remove all activity database older than 6 months. You may wish to make a backup of your js8spotter.db file, as this action cannot be undone. Proceed?"
        answer = askyesno(title='Trim Database?', message=msgtxt)
        if answer:
            c.execute("DELETE FROM activity WHERE spotdate < DATETIME('now', '-6 month')")
            c.execute("DELETE FROM grid WHERE grid_timestamp < DATETIME('now', '-6 month')")
            conn.commit()
            self.refresh_keyword_tree()

    def about(self):
        about_info = swname+" version "+displayversion+"\n\nOpen Source, MIT License\nQuestions to Joe, KF7MIX\nwww.kf7mix.com"
        messagebox.showinfo("About "+swname,about_info)

    def check_ip(self, addr):
        octets = addr.split(".")
        if len(octets) != 4: return False
        for octet in octets:
            if not isinstance(int(octet), int): return False
            if int(octet) < 0 or int(octet) > 255: return False
        return True

    ## Minimalistic low resolution timestamp (datecode) for MCForms (full timestamp is known when a report is received. year is inferred from that by the operator)
    def decode_shorttime(self, ststamp):
        dcst=""
        # note that ststamp has # at position [0]. We can decode partial timestamps
        m = ""
        if len(ststamp) > 1:
            ma = ord(ststamp[1]) # Month, A-L (1-12)
            if ma>64 and ma<77: m = str(ma-64)
        else:
            m="0"

        d = ""
        if len(ststamp) > 2:
            da = ord(ststamp[2]) # Day, A-Z = 1-26, 0-4 = 27-31
            if da>47 and da<53: d = str((da-47)+26)
            if da>64 and da<91: d = str(da-64)
        else:
            d="0"

        h=""
        if len(ststamp) > 3:
            ha = ord(ststamp[3]) # Hour, A-X = 0-23
            if ha>64 and ha<89: h = str(ha-65)
        else:
            h="00"

        t=""
        if len(ststamp) > 4: # old JS8Spotter versions had only three (plus #) characters, so we'll have this be optional
            ma = ord(ststamp[4]) # Minutes, 2min resolution, A-Z and 0-3 (A=0, B=2, C=4, etc)
            if ma>47 and ma<52: t = h+":"+str(((ma-48)+26)*2).zfill(2)
            if ma>64 and ma<91: t = h+":"+str((ma-65)*2).zfill(2)
        else:
            t = h+":00"

        if m != "" and d != "" and h !="" and t != "":
            dcst = str(m+"/"+d+" "+t)

        return dcst

    ## Return the current time as an encoded short time string (datecode)
    def encode_shorttime(self):
        curtime=time.localtime(time.time())
        m=chr(curtime[1]+64)
        da=int(curtime[2])
        if da<27: d=chr(da+64)
        if da>26: d=chr((da-26)+47)
        h=chr(curtime[3]+65)
        mi=int(curtime[4]/2)+1+64
        if mi>90: mi-=43
        return "#"+m+d+h+chr(mi)

    def encode_custshorttime(self,mon,day,hr,min):
        m=chr(int(mon)+64)
        da=int(day)
        if da<27: d=chr(da+64)
        if da>26: d=chr((da-26)+47)
        h=chr(int(hr)+65)
        mi=int(int(min)/2)+1+64
        if mi>90: mi-=43
        return "#"+m+d+h+chr(mi)

    def clear_statusbar(self):
        totals[1]=0
        totals[2]=0
        totals[3]=0
        totals[4]=0
        self.update_statusbar()

    ## Update status bar in main window based on certain activities, activate notify 1 sounds
    def update_statusbar(self):
        global totals, nosound

        # Play notification type 1 sounds (profile match activity)
        for pid in notifyProfile:
            if notifyProfile[pid]!="":
                c.execute("SELECT count(*) FROM activity WHERE profile_id = '"+pid+"' AND spotdate > DATETIME('now', '-3 second')")
                newinpid=c.fetchone()[0]

                # If able, play a defined sound
                if newinpid>0 and settings['disable_sounds']=="0":
                    if nosound==0:
                        try:
                            snd = tkSnack.Sound()
                            snd.read(notifyProfile[pid])
                            snd.play(blocking=0)
                        except:
                            pass
                    if nosound==2:
                        try:
                            wave_obj = sa.WaveObject.from_wave_file(notifyProfile[pid])
                            play_obj = wave_obj.play()
                        except:
                            pass

        # Update status bar
        c.execute("SELECT count(*) FROM expect WHERE lm > DATETIME('now', '-5 second')")
        totals[1]+=c.fetchone()[0]

        c.execute("SELECT count(*) FROM forms WHERE lm > DATETIME('now', '-5 second')")
        totals[2]+=c.fetchone()[0]

        c.execute("SELECT count(*) FROM csstatrep WHERE cssr_timestamp > DATETIME('now', '-5 second')")
        totals[3]+=c.fetchone()[0]

        stupdate="Status: Waiting for Data "
        if totals[1]>0: stupdate+="[EXPECT Updated] "
        if totals[2]>0: stupdate+="[FORM RESPONSES Updated] "
        if totals[3]>0: stupdate+="[STATREPS Updated] "
        if totals[4]>0: stupdate+="[AUTOTX Sent] "

        if settings['pause_expect']=="1": stupdate+="[!! EXPECT RESPONSES PAUSED !!] "
        if settings['pause_autotx']=="1": stupdate+="[!! EXPECT AUTOTX PAUSED !!] "

        self.statusbar.config(text=stupdate)

    def expire_messagebox(self, title, message, timeout_ms):

        self.embtop = tk.Toplevel(self)
        self.embtop.title(title)

        tk.Label(self.embtop, text=message).pack(padx=20, pady=20)
        ok_button = tk.Button(self.embtop, text="OK", command=self.embtop.destroy)
        ok_button.pack(pady=5)

        self.embtop.after(timeout_ms, self.embtop.destroy)

        self.embtop.focus()
        self.embtop.grab_set()

    # not currently used
    def clear_activity_dupes(self):
        # clear duplicate entries in the activity table 
        dupes_sql = "DELETE FROM activity WHERE ROWID NOT IN (SELECT MIN(ROWID) FROM activity GROUP BY profile_id,type,value,dial,snr,call,spotdate,freq,offset,speed);"
        c.execute(dupes_sql)
        conn.commit()

    ## Watch activity thread, update gui as needed
    def poll_activity(self):
        global last_auto_tx

        # Check if JS8Call was closed, inform the user
        if js8close.is_set():
            messagebox.showinfo("JS8Call Was Closed","The JS8Call application was closed. Please restart JS8Spotter after you restart JS8Call.")
            self.menu_bye()

        # update status if event is set by TCP_RX thread
        if event.is_set():
            self.refresh_activity_tree()
            self.refresh_keyword_tree()
            self.update_statusbar()
            event.clear()

        # check if speed reset needs to be scheduled
        if speedmod.is_set():
            super().after(int(speedmod_timeout*1000),self.reset_speed,speedmod_oldspeed)
            speedmod.clear()

        # also check for auto tx needs
        atx_now = datetime.datetime.now()
        atx_current_hr = atx_now.hour
        atx_current_min = atx_now.minute
        atx_check = str(atx_current_hr)+":"+str(atx_current_min)

        if atx_check != last_auto_tx and settings['pause_autotx']!='1':
            for atx in auto_txes:
                if atx[1]==atx_current_hr and atx[2]==atx_current_min:
                    # perform send
                    atx_expect = [tup for tup in expects if tup[0] == atx[0]]
                    to_send = str(atx_expect[0][8])+" "+str(atx_expect[0][1])
                    atx_speed = atx_expect[0][6]

                    # MODE.GET_SPEED / MODE.SET_SPEED, 0=normal, 1=fast, 2=JS8 40, 4=slow, 8=JS8 60, 16=Subspace
                    # "Current" / None means leave JS8Call's current speed alone (don't send SET_SPEED)
                    if atx_speed not in (None, "Current"):
                        old_speed = reported_speed
                        new_speed = 0

                        if atx_speed=="Normal": new_speed=0
                        if atx_speed=="Fast":   new_speed=1
                        if atx_speed=="JS8 40":  new_speed=2
                        if atx_speed=="Slow":   new_speed=4
                        if atx_speed=="JS8 60":  new_speed=8
                        if atx_speed=="Subspace":   new_speed=16

                        tx_content = json.dumps({"params":{"SPEED":new_speed},"type":"MODE.SET_SPEED"})
                        self.sock.send(bytes(tx_content + '\n','utf-8'))
                        time.sleep(0.25)

                        # as of v2.4.0, we must estimate when to set the speed back
                        sent_words = len(to_send.split())
                        speed_reset_delay = self.get_tx_time(new_speed,sent_words)
                        super().after(int(speed_reset_delay*1000),self.reset_speed,old_speed)

                    # make sure the message pane is empty
                    tx_content = json.dumps({"params":{},"type":"TX.SET_TEXT","value":""})
                    self.sock.send(bytes(tx_content + '\n','utf-8'))
                    time.sleep(0.33)

                    tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":to_send})
                    self.sock.send(bytes(tx_content + '\n','utf-8'))

                    # for eventual use when speed is tied to transmission and we don't have to guess, otherwise it resets before sending
#                    time.sleep(0.25)
#                    if atx_speed != None:
#                        tx_content = json.dumps({"params":{"SPEED":old_speed},"type":"MODE.SET_SPEED"})
#                        self.sock.send(bytes(tx_content + '\n','utf-8'))
#                        time.sleep(0.25)

                    # append database txlist
                    sql = "UPDATE expect SET txlist = txlist || 'AUTO TX "+atx_expect[0][8]+" "+datetime.datetime.now().strftime("%x %X")+",' WHERE expect = ?"
                    c.execute(sql,[atx_expect[0][0]])
                    conn.commit()

                    # prevent multiple TXes in a single minute
                    last_auto_tx=str(atx_current_hr)+":"+str(atx_current_min)

                    totals[4]+=1
                    self.update_statusbar()
                    try:
                        self.expire_messagebox("Auto TX", "An auto transmission was sent and logged in Expect.\n\n(This message will close automatically)", 5000)
                    except:
                        pass

        super().after(2000,self.poll_activity)

    def reset_speed(self,speed):
        tx_content = json.dumps({"params":{"SPEED":speed},"type":"MODE.SET_SPEED"})
        self.sock.send(bytes(tx_content + '\n','utf-8'))
        time.sleep(0.25)

    def get_tx_time(self, speed, words):
        if speed==0: wpm,frame=16,15
        if speed==1: wpm,frame=24,10
        if speed==2: wpm,frame=40,6
        if speed==4: wpm,frame=8,30
        if speed==8: wpm,frame=60,4
        if speed==16: wpm,frame=60,4

        tts = (words/wpm)*60
        if tts<frame: tts=frame
        tts+=(frame*2)
        # returning approx number of seconds to send, plus two frames (one to account for start, one for after) in seconds
        return tts

    # universal right-click menu with cut/copy/paste
    def rcmenu_ccp(self,event):
        self.context_menu = tk.Menu(event.widget, tearoff=0)
        self.context_menu.add_command(label="Cut", command=lambda: event.widget.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="Copy", command=lambda: event.widget.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Paste", command=lambda: event.widget.event_generate("<<Paste>>"))
        self.context_menu.bind("<Leave>", self.rcmenu_leave)
        self.context_menu.post(event.x_root, event.y_root)

    def rcmenu_leave(self,event):
        self.grab_release()
        self.context_menu.unpost()
        self.context_menu.destroy()
        self.context_menu.master.focus_set()

    def start_receiving(self):
        self.receiver = TCP_RX(self.sock)
        self.receiver.start()

    def stop_receiving(self):
        self.receiver.stop()
        self.receiver.join()
        self.receiver = None

    ## Quit function, close the recv thread, database connection, and main gui window
    def menu_bye(self):
        c.execute("UPDATE setting SET value = ? WHERE name = 'win_geometry'", [self.geometry()])
        conn.commit()
        conn.close()
        self.stop_receiving()
        self.destroy()

    def mainloop(self, *args):
        super().mainloop(*args)
        if self.receiver: self.receiver.stop()

def main():
    ## Check for tcp connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((settings['tcp_ip'], int(settings['tcp_port'])))
    except ConnectionRefusedError:
        sock = None # we'll provide the connection error message after the gui loads
    except TimeoutError:
        sock = None # we'll provide the connection error message after the gui loads
    except OSError:
        sock = None

    # start the application
    app = App(sock)
    app.mainloop()

## Start the program execution
if __name__ == '__main__':
    main()
