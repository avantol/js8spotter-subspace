#!/usr/bin/env python3
# JS8Spotter DB Tool v1.17. Visit https://kf7mix.com/js8spotter.html for information
# For keeping your JS8Spotter database up-to-date with new JS8Spotter releases. Checks/corrects existing tables have all columns, and all tables are present.
# Version of this program matches JS8Spotter program it was distributed with.
#
# MIT License, Copyright 2026 Joseph D Lyman KF7MIX --- Permission is hereby granted,  free of charge, to any person obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.  The Software IS PROVIDED "AS IS",  WITHOUT WARRANTY OF ANY KIND,  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES  OF  MERCHANTABILITY,  FITNESS OR A PARTICULAR PURPOSE AND  NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,  DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import tkinter as tk
import tkinter.scrolledtext as st
import sqlite3
import os

#### init
dbverTarget = "1.17"
hrline = "\n"+("-" * 30)+"\n"

columns = {}

columns['activity'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("profile_id", "INTEGER"),
    ("type", "TEXT"),
    ("value", "TEXT"),
    ("dial", "TEXT"),
    ("snr", "TEXT"),
    ("call", "TEXT"),
    ("spotdate", "TIMESTAMP"),
    ("freq", "TEXT DEFAULT ''"),
    ("offset", "TEXT DEFAULT ''"),
    ("speed", "TEXT DEFAULT ''")
)

columns['expect'] = (
    ("expect", "VARCHAR(6) UNIQUE ON CONFLICT REPLACE PRIMARY KEY"),
    ("reply", "VARCHAR(128)"),
    ("allowed", "TEXT"),
    ("txlist", "TEXT"),
    ("txmax", "INTEGER"),
    ("lm", "TIMESTAMP"),
    ("txspeed","TEXT"),
    ("autotx","TEXT"),
    ("atxtarget","TEXT")
)

columns['forms'] = (
    ("id", "PRIMARY KEY AUTOINCREMENT"),
    ("fromcall", "TEXT"),
    ("tocall", "TEXT"),
    ("typeid", "TEXT"),
    ("responses", "TEXT"),
    ("msgtxt", "TEXT"),
    ("timesig", "TEXT"),
    ("lm", "TIMESTAMP"),
    ("gwtx", "TEXT DEFAULT ''")
)

columns['grid'] = (
    ("grid_callsign", "VARCHAR (64) UNIQUE ON CONFLICT REPLACE PRIMARY KEY"),
    ("grid_grid", "VARCHAR (16)"),
    ("grid_dial", "VARCHAR (64)"),
    ("grid_type", "VARCHAR (64)"),
    ("grid_snr", "VARCHAR (16)"),
    ("grid_timestamp", "TIMESTAMP")
)

columns['profile'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("title", "TEXT UNIQUE ON CONFLICT IGNORE"),
    ("def", "BOOLEAN DEFAULT (0)"),
    ("bgscan", "BOOLEAN DEFAULT (0)"),
    ("sort", "INT")
)

columns['search'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("profile_id", "INT"),
    ("keyword", "TEXT"),
    ("last_seen", "TIMESTAMP"),
    ("comment", "TEXT")
)

columns['signal'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("sig_callsign", "VARCHAR (64)"),
    ("sig_dial", "TEXT"),
    ("sig_freq", "TEXT"),
    ("sig_offset", "TEXT"),
    ("sig_speed", "TEXT"),
    ("sig_snr", "TEXT"),
    ("sig_timestamp", "TIMESTAMP")
)

columns['setting'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("name", "TEXT UNIQUE ON CONFLICT IGNORE"),
    ("value", "TEXT")
)

columns['notify'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("type", "INT"),
    ("trigger", "TEXT"),
    ("action", "TEXT")
)

columns['csstatrep'] = (
    ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
    ("cssr_from", "VARCHAR (64)"),
    ("cssr_group", "VARCHAR (64)"),
    ("cssr_grid", "TEXT"),
    ("cssr_prio", "TEXT"),
    ("cssr_msgid", "TEXT"),
    ("cssr_status", "TEXT"),
    ("cssr_notes", "TEXT"),
    ("cssr_timestamp", "TIMESTAMP")
)

tables = {}

for tname in columns:
    tables[tname]= []
    for col, setup in columns[tname]:
        tables[tname].append(col)

#### functions
def upgradedb():
    info_text.configure(state ='normal')
    info_text.insert('end', hrline+'Attempting update...\n')

    # do update
    for vtable in tables:
        validateTable(vtable,True)

    # update db version
    c.execute("DELETE FROM setting WHERE name='dbver'")
    c.execute("INSERT INTO setting(name,value) VALUES('dbver',?)", [dbverTarget])
    conn.commit()

    info_text.configure(state ='normal')
    info_text.insert('end', hrline+'Update complete.\n')
    info_text.configure(state ='disabled')
    info_text.see("end")

def genTableCreate(tablename):
    newCreate = "CREATE TABLE \""+tablename+"\" ("
    for col, setup in columns[tablename]:
        newCreate = newCreate + ("\""+col+"\" "+setup+",")
    newCreate = newCreate[:-1] + ");"
    return newCreate

def genTableAlter(tablename,column):
    csetup = next((item for item in columns[tablename] if column in item),None)
    newAlter = "ALTER TABLE \""+tablename+"\" ADD COLUMN \""+column+"\" "+csetup[1]
    return newAlter

def validateTable(tablename, doUpdate):
    info_text.configure(state ='normal')
    if doUpdate==True:
        info_text.insert('end', '< '+tablename+' Table >\n')
    else:
        info_text.insert('end', '[ '+tablename+' Table ]\n')

    try:
        c.execute('SELECT * FROM '+tablename+' LIMIT 0')
        table_current = [res[0] for res in c.description]

        if table_current == tables[tablename]:
            # Nothing to do, report only
            if doUpdate==True:
                info_text.insert('end', '  Table already contains the correct columns, no action taken.\n')
            else:
                info_text.insert('end', '  Table already contains the correct columns.\n')
        else:
            missingCols=""

            for colname in tables[tablename]:
                if colname not in table_current:
                    missingCols+=colname+" "

            if doUpdate==True:
                info_text.insert('end', '  ** Adding column(s): '+str(missingCols)+"\n")

                # perform the update (alter table to add column)
                for colname in tables[tablename]:
                    if colname not in table_current:
                        tasql = genTableAlter(tablename,colname)
                        c.execute(tasql)
                        conn.commit()
            else:
                info_text.insert('end', '  !! Missing column(s): '+str(missingCols)+"\n")
    except sqlite3.OperationalError:
        if doUpdate==True:
            # add missing table
            info_text.insert('end', '  ** Adding table: '+str(tablename)+"\n")
            tcsql = genTableCreate(tablename)
            c.execute(tcsql)
            conn.commit()
        else:
            info_text.insert('end', '  !! '+tablename+' is missing and will be created during upgrade.\n')

    info_text.see("end")
    info_text.configure(state ='disabled')
    win.update()

#### create gui
win = tk.Tk()
win.title("JS8Spotter Database Tool v1.17")
win.geometry('600x500')
win.minsize(600,500)

# gui: info text window
info_text = st.ScrolledText(win)
info_text.pack(expand=True, fill='both', padx=(10,0), pady=(0,10))
info_text.insert('end', 'Target database version:'+dbverTarget+"\n")

errors=0

# connect to database file in current directory
if os.path.exists("js8spotter.db"):
    dbfile = 'js8spotter.db'
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
else:
    info_text.insert('end', "Database file missing. Please copy your .db backup file into this folder and try again."+hrline)
    errors=errors+1

# check for database version in settings table
try:
    c.execute("SELECT * FROM setting")
    dbsettings = c.fetchall()
    settings = {}
    for setting in dbsettings:
        settings[setting[1]]=setting[2]
except:
    info_text.insert('end', "Database missing or invalid. Please re-copy your .db backup file into this folder and try again."+hrline)
    errors=errors+1

try:
    info_text.insert('end', 'Current database version:'+settings['dbver']+hrline)
except:
    info_text.insert('end', "Database error. Please re-copy your .db backup file into this folder and try again."+hrline)
    errors=errors+1

if errors==0:
    # Validate table structures
    for vtable in tables:
        validateTable(vtable,False)

    # gui: buttons
    btnframe = tk.Frame(win)
    btnframe.pack(anchor='sw', padx=10, pady=(0,10))
    upgrade_button = tk.Button(btnframe, text = 'Upgrade DB', command = upgradedb)
    upgrade_button.pack(padx=(0,10))


#### start main event loop
win.mainloop()


