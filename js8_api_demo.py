# JS8Call API Demo v01, KF7MIX -- Public domain, use it however you like

# This is a minimal GUI application that talks with the JS8Call API.
# May be useful as a stub for creating new JS8Call API programs.

import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from threading import Event, Thread
from io import StringIO
import socket
import select
import json

event = Event() # for inter-thread comms
settings = {"tcp_ip": "127.0.0.1", "tcp_port": "2442"}

### RX thread
class TCP_RX(Thread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.keep_running = True

    def stop(self):
        self.keep_running = False

    def run(self):
        # If you want to process only certain activity types from the API
        track_types = {"RX.ACTIVITY", "RX.DIRECTED", "RX.SPOT"}

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

                        if data_json['type'] in track_types:
                            # gather basic elements of this record
                            msg_call = ""
                            msg_dial = ""
                            msg_snr = ""
                            msg_freq = ""
                            msg_offset = ""
                            msg_speed = "" # 0=Normal, 1=Fast, 2=Turbo, 4=Slow (8=Ultra, in src code of js8call but not generally used)

                            if "CALL" in data_json['params']: msg_call = data_json['params']['CALL']
                            if "FROM" in data_json['params']: msg_call = data_json['params']['FROM'] # we're saving either CALL or FROM with preference for FROM
                            if "DIAL" in data_json['params']: msg_dial = data_json['params']['DIAL']
                            if "FREQ" in data_json['params']: msg_freq = data_json['params']['FREQ']
                            if "OFFSET" in data_json['params']: msg_offset = data_json['params']['OFFSET']
                            if "SPEED" in data_json['params']: msg_speed = data_json['params']['SPEED']
                            if "SNR" in data_json['params']: msg_snr = data_json['params']['SNR']
                            msg_value = data_json['value']

                            msg_grid = ""
                            if "GRID" in data_json['params']: msg_grid = data_json['params']['GRID'].strip()

                            # Here you can do whatever you like with the data
                            # print it, put it in a database, process it, etc
                            # this example prints a few of the values gathered to the command line


                            print("\nRaw Data:\n"+str(iodata)+"\n")
                            print("\nProceed data sample: "+str(msg_call)+", "+str(msg_dial)+", "+str(msg_freq)+", "+str(msg_value)+"\n")

                            # this thread cannot modify the gui, you can set an event to nofity of database changes etc
                            event.set()

                            # If you want to transmit, you can do so in this thread
                            # you could use the info you gathered, or part of it, to construct your message for the JS8Call API
                            #tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":ex_reply})
                            #self.sock.send(bytes(tx_content + '\n','utf-8'))
                            #time.sleep(0.25)

                except socket.error as err:
                    print("TCP error at receiving socket {}".format(err))
                    break

### Main program thread
class App(tk.Tk):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.sender = None
        self.receiver = None
        self.protocol("WM_DELETE_WINDOW", self.menu_bye)

        self.create_gui()
        self.eval('tk::PlaceWindow . center')

        self.start_receiving()
        self.poll_activity()
        self.update()

        if self.sock == None:
            messagebox.showinfo("TCP Error","Can't connect to JS8Call.")

    def create_gui(self):
        self.title("JS8Call API Demo")
        self.geometry('500x500')
        self.minsize(500,500)
        self.resizable(width=True, height=True)

        self.toplabel = ttk.Label(self, text="Thread Activity Indicator")
        self.toplabel.pack(side=TOP, anchor='nw', padx=10, pady=10)

        # Quit and TX buttons
        tlframe = ttk.Frame(self)
        tlframe.pack(side=BOTTOM, anchor='sw', padx=10, pady=(0,10))
        self.bye_button = ttk.Button(tlframe, text = 'Quit', command = self.menu_bye)
        self.bye_button.pack(side=LEFT, padx=(0,10))
        self.saveas_button = ttk.Button(tlframe, text = 'TX Test', command = self.proc_txtest)
        self.saveas_button.pack(side=RIGHT)

        # text window
        self.info_text = Text(self, wrap=NONE)
        info_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscroll=info_scrollbar.set)
        info_scrollbar.pack(side=RIGHT, fill='y', padx=(0,10), pady=(0,10))
        self.info_text.pack(side=LEFT, expand=True, fill='both', padx=(10,0), pady=(0,10))

        self.info_text.insert(tk.END, "Notifications will appear in this box.\nData from the API will print in the console.\n\n")


    def proc_txtest(self):
        tx_content = json.dumps({"params":{},"type":"TX.SEND_MESSAGE","value":"TEST"})
        self.sock.send(bytes(tx_content + '\n','utf-8'))


    ## Watch activity thread, update gui as needed
    def poll_activity(self):
        if event.is_set():
            # do anything you want in the gui here, read from db, update gui, etc
            # in response to activity from tcp thread
            self.info_text.insert(tk.END, "Received info from JS8Call API\n")
            event.clear()
        super().after(2000,self.poll_activity)

    def start_receiving(self):
        self.receiver = TCP_RX(self.sock)
        self.receiver.start()

    def stop_receiving(self):
        self.receiver.stop()
        self.receiver.join()
        self.receiver = None

    ## Quit function, close the recv thread, database connection, and main gui window
    def menu_bye(self):
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
        sock = None # we'll provide the connection error after the gui loads
    except TimeoutError:
        sock = None # we'll provide the connection error after the gui loads

    app = App(sock)
    app.mainloop()

if __name__ == '__main__':
    main()
