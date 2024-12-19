import asyncio
from collections import deque
import enum
import math
import os
import sys
from time import sleep
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random
import json
import subprocess
from matplotlib import pyplot as plt
import matplotlib
from scipy.interpolate import interp1d
import statistics
from typing import Dict, List, Union
from scipy import stats
import numpy as np
import itertools
import shutil
from pynput import keyboard, mouse
from twitchio.ext import commands
import threading
from PIL import Image, ImageTk
import datetime
from cryptography.fernet import Fernet
from twitchio.errors import *

SENSES = None
RAWACCEL_DELAY = 1100
reset = lambda : subprocess.Popen("reset.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
sens_lock = threading.Lock()

class trigger_devs(enum.Enum):
    NONE = 0
    KEYBOARD = 1
    MOUSE = 2
    SCROLL = 3


def log_dump(s : str):
    s = "".join([f"[{datetime.datetime.now().strftime('%H:%M:%S')}] -> ", s])
    print(s)
    with open("latest-dump.log", "a") as f:
        print(s, file=f)


def on_exit(code = 0):
    if app.running and app.dt < RAWACCEL_DELAY:
        sleep(float(RAWACCEL_DELAY - app.dt) / 1000.0)
    reset()
    root.quit()
    sys.exit(code)


class sens_t(object):
    BASE_SENS : float = 1.0

    @staticmethod
    def get_multi(sens : float) -> float:
        return sens / sens_t.BASE_SENS

    @staticmethod
    def scaled_sens(multi) -> float:
        return multi * sens_t.BASE_SENS

    def __init__(self, sens : float, time : float, author : Union[str, None] = None):
        self.sens : float = sens
        self.time : float = time
        self.author : str = author

    def __str__(self) -> str:
        return f"<sens_t>(sens: {self.sens}, time: {self.time}, author: {self.author})"


def set_sens(x : float) -> None:
    global rawaccel

    try:
        with open("settings.json", "r") as settings_json:
            settings = dict(json.load(settings_json))
            settings["profiles"][0]["Sensitivity multiplier"] = x * DEFAULT_MULT

    except:
        shutil.copy("../settings.json", "./settings.json")
        messagebox.showerror("error", "copied settings.json from parent folder.\nrestart the program")
        sys.exit(1)

    with open("settings.json", "w") as settings_json:
        json.dump(settings, settings_json, indent=2)

    subprocess.Popen("../writer.exe settings.json")


def fixed_mean_rand(bias : float, minimum : float, maximum : float, count : int):
    data : List[float] = [minimum, maximum, bias]
    new = bias

    for i in range(count):
        if not i % 3:
            new = random.uniform(minimum, maximum)

        elif i & 1:
            mean = statistics.mean(data)

            if (abs(bias - mean) <= 1e-6):
                new = random.uniform(minimum, maximum)
            elif (mean < bias):
                new = random.uniform(bias, maximum)
            elif (mean > bias):
                new = random.uniform(minimum, bias)

        else:
           new = (len(data) + 1) / sum(data)

        data.append(new)

    random.shuffle(data)
    return data


def interpolate_senses(senses : List[float]) -> List[float]:
    senses.append(senses[0])
    indices = np.arange(len(senses))
    distances = np.diff(senses)
    interp = interp1d(indices, senses, kind = "linear")
    new_indices = []

    for i, dist in enumerate(distances):
        num_points = int(abs(dist) * 10) + 2
        new_interval = np.linspace(indices[i], indices[i + 1], num=num_points)
        new_indices.extend(new_interval)

    new_indices = np.array(new_indices)
    senses = list(interp(new_indices))
    return senses


class twitch_listener(commands.Bot):

    def __init__(self, token, channel, sens_min, sens_max, sens_time):
        self.token = token
        self.channel = channel
        self.min = sens_min
        self.max = sens_max
        self.max = sens_max
        self.time = sens_time
        super().__init__(token=self.token, prefix="", initial_channels=[self.channel])

    async def start(self):
        try:
            await super().start()
        except AuthenticationError:
            messagebox.showerror("error", "invalid twitch oauth key")
            app.force_stop()

    async def event_ready(self):
        log_dump(f"connected to twitch channel <{self.channel}>")

    async def event_message(self, message):
        if message.content[:4] == "sens":
            try:
                args : str = message.content[4:].split(" ")[1]
                sens = float(args)

                if self.min > sens:
                    return
                if self.max < sens:
                    return

                s = sens_t(sens_t.get_multi(sens), self.time, message.author.display_name)
                with sens_lock:
                    if s.author == self.channel:
                        SENSES.appendleft(s)
                        return
                        
                    for i in range(len(SENSES)):
                        if SENSES[i].author == s.author:
                            return
                            
                        if SENSES[i].author is None:
                            log_dump(f"added {s} at index {i}")
                            SENSES.insert(i, s)
                            return
            except:
                return


class key_t(object):
    def __init__(self, key_file=".key"):
        self.key_file = key_file
        self.key = self.load_or_generate_key()

    def load_or_generate_key(self):
        # Check if the key file exists; if not, generate a new key
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key
        else:
            # Load the existing key from the file
            with open(self.key_file, "rb") as f:
                return f.read()

    def encrypt_password(self, password):
        fernet = Fernet(self.key)
        return fernet.encrypt(password.encode())

    def decrypt_password(self, encrypted_password):
        fernet = Fernet(self.key)
        return fernet.decrypt(encrypted_password).decode()

    def save_password(self, password, file_name):
        encrypted_password = self.encrypt_password(password)
        with open(file_name, "wb") as f:
            f.write(encrypted_password)

    def load_password(self, file_name):
        if not os.path.exists(file_name):
            return None
        with open(file_name, "rb") as f:
            encrypted_password = f.read()
        return self.decrypt_password(encrypted_password)


class rawrand:

    def __init__(self, root : tk.Tk, config: Dict, twitch_oauth : Union[None, str]):
        self.root = root
        self.root.title("rawrand by hamid")

        # window size
        self.root.iconbitmap("assets/dice.ico")
        self.root.geometry("515x315")
        self.root.resizable(False, False)

        # main frame
        main_frame = ttk.Frame(root, padding = "10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # left frame
        input_frame = ttk.LabelFrame(main_frame, text = "config", padding = "5")
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.N)

        # base sens
        ttk.Label(input_frame, text = "base:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.base_var = tk.StringVar(value=str(config.get("base", 1)))
        self.base_entry = ttk.Entry(input_frame, textvariable=self.base_var, width=15)
        self.base_entry.grid(row=0, column=1, padx=5, pady=2)

        # min sens
        ttk.Label(input_frame, text = "min:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.min_var = tk.StringVar(value=str(config.get("min", .5)))
        self.min_entry = ttk.Entry(input_frame, textvariable=self.min_var, width=15)
        self.min_entry.grid(row=1, column=1, padx=5, pady=2)

        # max sens
        ttk.Label(input_frame, text = "max:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.max_var = tk.StringVar(value=str(config.get("max", 2)))
        self.max_entry = ttk.Entry(input_frame, textvariable=self.max_var, width=15)
        self.max_entry.grid(row=2, column=1, padx=5, pady=2)

        # num senses
        ttk.Label(input_frame, text = "count / precision:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        self.num_var = tk.StringVar(value=str(config.get("num", 500)))
        self.num_entry = ttk.Entry(input_frame, textvariable=self.num_var, width=15)
        self.num_entry.grid(row=3, column=1, padx=5, pady=2)

        # trigger mode
        ttk.Label(input_frame, text = "trigger:").grid(row=4, column=0, padx=5, pady=2, sticky=tk.W)
        self.trigger_mode_var = tk.StringVar(value=str(config.get("trigger", "time")))
        self.trigger_mode_combo = ttk.Combobox(input_frame,
                                      textvariable=self.trigger_mode_var,
                                      values=[ "time", "keybind", "game state" ],
                                      width=12,
                                      state = "readonly")
        self.trigger_mode_combo.grid(row=4, column=1, padx=5, pady=2)
        self.trigger_mode_combo.bind('<<ComboboxSelected>>', lambda e: self.update_leftside())

        # trigger sub-label
        self.trigger_sublabel = ttk.Label(input_frame, text = "time (s):")
        self.trigger_sublabel.grid(row=5, column=0, padx=5, pady=2, sticky=tk.W)

        # keybind
        self.keybind = tk.StringVar(value=str(config.get("keybind", "<null>")))
        self.keybind_button = tk.Button(input_frame, text = self.keybind.get(), command=self.bind_key, width = 12, height = 1, padx = 0, pady=0)
        self.keybind_button.grid(row=5, column=1, padx=5, pady=1)

        # time
        # TODO(hamid): add random time intervals
        self.time_var = tk.StringVar(value=str(config.get("time", 10000)/1000))
        self.time_entry = ttk.Entry(input_frame, textvariable=self.time_var, width=15)
        self.time_entry.grid(row=5, column=1, padx=5, pady=2)

        # generation mode
        ttk.Label(input_frame, text = "gen. mode:").grid(row=6, column=0, padx=5, pady=2, sticky=tk.W)
        self.gen_mode_var = tk.StringVar(value=str(config.get("mode", "random")))
        self.gen_mode_combo = ttk.Combobox(input_frame,
                                      textvariable=self.gen_mode_var,
                                      values=[ "random", "trunc. norm-dist", "fixed mean", "lognormal", "full range" ],
                                      width=12,
                                      state = "readonly")
        self.gen_mode_combo.grid(row=6, column=1, padx=5, pady=2)
        self.gen_mode_combo.bind('<<ComboboxSelected>>', lambda e: self.update_leftside())

        self.shuffle_var = tk.BooleanVar(value=bool(config.get("shuffle", True)))
        self.shuffle_checkbox = ttk.Checkbutton(input_frame,
                                      text = "shuffle",
                                      variable=self.shuffle_var)
        self.shuffle_checkbox.grid(row=7, column=0, pady=5, sticky=tk.W)

        self.interpolation_var = tk.BooleanVar(value=bool(config.get("interp", False)))
        self.interp_checkbox = ttk.Checkbutton(input_frame,
                                      text = "interpolate",
                                      variable=self.interpolation_var)
        self.interp_checkbox.grid(row=7, column=1, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=8, columnspan=2, padx=5, pady=5, sticky = "ns")

        # twitch button
        self.twitch_icon = ImageTk.PhotoImage(Image.open("assets/twitch.ico").resize((20, 20), Image.Resampling.LANCZOS))
        self.twitch_button = tk.Button(button_frame, image=self.twitch_icon, command=self.twitch_menu, padx = 0, pady=0)
        self.twitch_button.grid(row=0, column=0, pady=5, padx = (0, 5), sticky='ew')

        # graph button
        self.graph_button = ttk.Button(button_frame, text = "graph", command=self.show_graph)
        self.graph_button.grid(row=0, column=1, pady=5, padx = (0, 5), sticky='ew')

        # apply button
        self.apply_button = ttk.Button(button_frame, text = "regenerate", command=self.apply_settings)
        self.apply_button.grid(row=0, column=2, pady=5, padx = (5, 5), sticky='ew')

        # start/stop button
        self.running = False
        self.toggle_button = ttk.Button(button_frame, text = "start", command=self.toggle_rawrand, state=tk.DISABLED)
        self.toggle_button.grid(row=0, column=3, pady=5, padx = (5, 0), sticky='ew')

        # display
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=0, column=1, padx=10, pady=5, sticky = "ns")

        self.prev_label = ttk.Label(display_frame, text = "", font=('Consolas', 22), anchor = "center")
        self.prev_label.pack(expand=True, fill = "both", padx=10, pady=10)

        self.label = ttk.Label(display_frame, text = "", font=('Consolas', 36), anchor = "center")
        self.label.pack(expand=True, fill = "both", padx=10, pady=10)

        self.time_left = ttk.Label(display_frame, text = "", font=('Consolas', 22), anchor = "center")
        self.time_left.pack(expand=True, fill = "both", padx=10, pady=10)

        self.update_interval = int(float(self.time_var.get()) * 1000)

        # init
        self.dt = -1
        self.average = 0
        self.sens = self.prev = self.prev2 = sens_t(1.0, 0.0)
        self.trigger_mode = self.trigger_mode_var.get()
        self.trigger_dev = trigger_devs.NONE
        self.mouse_listener = None
        self.twitch_window = None
        self.bind_listener = None
        self.graph_window = None
        self.graph_upd = None
        self.after_id = None

        # twitch integration
        self.twitch_enabled = tk.BooleanVar(value=bool(config.get("twitch", {}).get("enabled", False)))
        self.twitch_channel_var = tk.StringVar(value=str(config.get("twitch", {}).get("channel", "")))
        self.twitch_oauth_var = tk.StringVar(value=str("" if twitch_oauth is None else twitch_oauth))
        self.twitch_listener = None
        self.twitch_loop = None
        self.twitch_thread = None

        self.update_leftside()


    def update_twitch_menu(self):
        if self.twitch_enabled.get():
            self.twitch_channel_entry.config(state=tk.NORMAL)
            self.twitch_oauth_entry.config(state=tk.NORMAL)

        else:
            self.twitch_channel_entry.config(state=tk.DISABLED)
            self.twitch_oauth_entry.config(state=tk.DISABLED)


    def twitch_menu(self):
        if self.twitch_window and self.twitch_window.winfo_exists():
            return

        self.twitch_window = tk.Toplevel(self.root)
        self.twitch_window.title("chat")
        self.twitch_window.geometry("215x215")
        self.twitch_window.iconbitmap("assets/pinkdice.ico")

        twitch_frame = ttk.LabelFrame(self.twitch_window, text="twitch integration", padding = "10")
        twitch_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.N)

        self.shuffle_checkbox = ttk.Checkbutton(twitch_frame, text = "enabled", variable=self.twitch_enabled, command=self.update_twitch_menu)
        self.shuffle_checkbox.grid(row=0, column=0, pady=0, sticky=tk.W)

        ttk.Label(twitch_frame, text = "channel:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.twitch_channel_entry = ttk.Entry(twitch_frame, textvariable=self.twitch_channel_var, width=15)
        self.twitch_channel_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(twitch_frame, text = "oauth:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.twitch_oauth_entry = ttk.Entry(twitch_frame, textvariable=self.twitch_oauth_var, width=15, show="•")
        self.twitch_oauth_entry.grid(row=2, column=1, padx=5, pady=2)

        # format frame
        twitch_format_frame = ttk.Frame(self.twitch_window, padding = "10")
        twitch_format_frame.grid(row=1, column=0, padx=10, pady=5, sticky=tk.N)

        ttk.Label(twitch_format_frame, text = "format:").grid(row=10, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(twitch_format_frame, text = ".sens <sens>").grid(row=10, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Label(twitch_format_frame, text = "example:").grid(row=11, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(twitch_format_frame, text = ".sens 0.5").grid(row=11, column=1, padx=5, pady=2, sticky=tk.W)

        self.update_twitch_menu()


    def stop_listeners(self):
        try:
            self.mouse_listener.stop()
            self.mouse_listener = None
            self.bind_listener.stop()
            self.bind_listener = None
        except:
            pass


    def capture_scroll(self, x, y, dx, dy):
        if dy == 1:
            key = "mwup"
        elif dy == -1:
            key = "mwdown"
        elif dx == 1:
            key = "mwright"
        elif dx == -1:
            key = "mwleft"
        else:
            return

        self.stop_listeners()

        self.keybind.set(key)
        self.keybind_button.config(text = key)

        self.update_leftside()


    def capture_button(self, x, y, button, pressed):
        if (not pressed):
            return

        self.stop_listeners()

        key = str(button)[7:]
        if key[0] == 'x':
            key = "mouse" + str(int(key[-1]) + 3)

        self.keybind.set(key)
        self.keybind_button.config(text = self.keybind.get())

        self.update_leftside()


    def capture_key(self, key):
        self.stop_listeners()

        self.keybind.set( key.char if hasattr(key, 'char') else str(key)[4:] )
        self.keybind_button.config(text = self.keybind.get())

        self.update_leftside()


    def bind_key(self):
        self.keybind_button.config(text = "press key...")

        if (not self.bind_listener):
            self.bind_listener = keyboard.Listener(on_press=self.capture_key)
            self.bind_listener.start()

        if (not self.mouse_listener):
            self.mouse_listener = mouse.Listener(on_click=self.capture_button, on_scroll=self.capture_scroll)
            self.mouse_listener.start()


    def show_graph(self):
        if self.graph_window and self.graph_window.winfo_exists():
            self.redraw_graph()
            return

        self.graph_window = tk.Toplevel(self.root)
        self.graph_window.title("senses")
        self.graph_window.geometry("600x400")
        self.graph_window.iconbitmap("assets/dice.ico")

        self.fig, self.ax = plt.subplots(facecolor = "black")
        self.fig.subplots_adjust(left=0.1, right=1, top=0.95, bottom=0.05)
        self.ax.set_title("senses")
        self.ax.set_ylabel("sens")
        self.ax.tick_params(axis='x', which='both', bottom=False, top=False)
        self.ax.tick_params(axis='y', which='both', left=False, right=False)

        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self.graph_window)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.redraw_graph()


    def redraw_graph(self):
        if self.graph_window == None:
            return

        if self.ax:
            self.ax.clear()

        self.ax.set_facecolor("black")

        # running
        if self.running:
            self.ax.set_ylim( math.floor(self.min * 10) / 10, math.ceil(self.max * 10) / 10 )
            self.ax.set_xticks([])
            sensitivities = [ sens_t.scaled_sens(self.prev2.sens), sens_t.scaled_sens(self.prev.sens), sens_t.scaled_sens(self.sens.sens) ]
            sensitivities.extend([ sens_t.scaled_sens(sens.sens) for sens in list(itertools.islice(SENSES, 0, 5)) ])

            self.ax.plot(
                sensitivities,
                marker = "o",
                linestyle = "-",
                color = "#cccccc",
                markerfacecolor='white',
                markeredgecolor='white',
                label = "sens",
            )

            self.ax.scatter(
                2, sens_t.scaled_sens(self.sens.sens),
                marker = "o",
                color = "#ffb300",
                zorder = 5
            )

            self.ax.axhline(y = sens_t.scaled_sens(self.sens.sens), color = "#ffb300", linestyle=':', linewidth=1)
            self.ax.axhline(y = self.base, color = "#555555", linestyle=':', linewidth=1)
            self.ax.set_ylabel("sens")

        # regeneration
        if SENSES and not self.running:
            sensitivities = [sens.sens for sens in SENSES]

            self.ax.plot(
                sensitivities,
                linestyle = "-",
                color = "white",
                label = "sens",
            )

            self.ax.axhline(y = sens_t.get_multi(self.base), color = "#555555", linestyle=':', linewidth = 2)
            self.ax.axhline(y = self.average, color = "#ffb300", linestyle=':', linewidth = 2)
            self.ax.set_ylabel("multiplier")
            self.ax.set_facecolor("black")

        self.canvas.draw()


    def generate_senses(self):
        global SENSES
        if self.gen_mode == "random":
            senses = [ random.uniform( sens_t.get_multi(self.min), sens_t.get_multi(self.max) ) for _ in range(self.num) ]

        elif self.gen_mode == "trunc. norm-dist":
            senses = stats.truncnorm( sens_t.get_multi(self.min) - 1, sens_t.get_multi(self.max) - 1, loc = 1, scale = 1 ).rvs(self.num)

        elif self.gen_mode == "fixed mean":
            senses = fixed_mean_rand( 1, sens_t.get_multi(self.min), sens_t.get_multi(self.max), self.num )

        elif self.gen_mode == "lognormal":
            senses = [ sens for sens in stats.lognorm(loc = .5, s = .5, scale = .5).rvs(self.num) if sens <= sens_t.get_multi(self.max) and sens_t.get_multi(self.min) <= sens ]

        elif self.gen_mode == "full range":
            increment = .1 ** self.num
            senses = list(np.arange(sens_t.get_multi(self.min), sens_t.get_multi(self.max) + increment, increment))

        if self.shuffle_var.get() == True:
            random.shuffle(senses)

        if self.interpolation_var.get() == True:
            senses = interpolate_senses(senses)

        senses = [ round(sens, 5) for sens in senses ]
        self.average = statistics.mean(senses)
        SENSES = deque([ sens_t(sens, self.update_interval if self.trigger_mode == "time" else RAWACCEL_DELAY / 1000) for sens in senses ])


    def force_stop(self):
        self.running = True
        self.toggle_rawrand()


    def save(self):
        d = {
            "base": self.base,
            "min": self.min,
            "max": self.max,
            "num": self.num,
            "trigger": self.trigger_mode,
            "time": self.update_interval,
            "keybind": self.keybind.get(),
            "mode": self.gen_mode,
            "shuffle": self.shuffle_var.get(),
            "interp": self.interpolation_var.get(),
            "twitch": {
                "enabled": self.twitch_enabled.get(),
                "channel": self.twitch_channel_var.get()
            }
        }

        try:
            with open("config.json", "w") as f:
                json.dump(d, f, indent=2)
        except:
            messagebox.showerror("error", "could not save config")

        key = key_t()
        key.save_password(self.twitch_oauth_var.get(), "./.twitch_oauth")


    def update_leftside(self):
        if self.trigger_mode_var.get() == "time":
            self.trigger_sublabel.config(text = "time (s):")
            self.keybind_button.grid_forget()
            self.time_entry.grid(row=5, column=1, padx=5, pady=2)

        elif self.trigger_mode_var.get() == "keybind":
            self.keybind_button.config(text = self.keybind.get())
            self.trigger_sublabel.config(text = "key:")
            self.time_entry.grid_forget()
            self.keybind_button.grid(row=5, column=1, padx=5, pady=1)

        elif self.trigger_mode_var.get() == "game state":
            messagebox.showerror("error", "game state is not implemented yet.")


    def update_display(self):
        if self.dt >= RAWACCEL_DELAY:
            self.label.config(text=f"{sens_t.scaled_sens(self.sens.sens):.3f}")
            self.prev_label.config(text=f"{sens_t.scaled_sens(self.prev.sens):.3f}")

            if self.trigger_mode == "time":
                self.time_left.config(text=f"{(self.sens.time - self.dt + RAWACCEL_DELAY - 100)/1000:.1f}s")

            elif self.trigger_mode == "keybind":
                grace = RAWACCEL_DELAY - self.dt - 100

                if grace - 100 > 0:
                    self.time_left.config(text=f"{grace/1000 :.1f}s")
                else:
                    self.time_left.config(text=f"<{self.keybind.get()}>")

        else:
            self.label.config(text=f"{sens_t.scaled_sens(self.prev.sens):.3f}")
            self.prev_label.config(text=f"{sens_t.scaled_sens(self.prev2.sens):.3f}")
            self.time_left.config(text=f"{(RAWACCEL_DELAY - self.dt - 100)/1000:.1f}s")


    def apply_settings(self):
        try:
            self.base = float(self.base_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid base sens")
            return False

        try:
            self.min = float(self.min_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid min. sens")
            return False

        try:
            self.max = float(self.max_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid max. sens")
            return False

        try:
            self.num = int(self.num_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid generation num")
            return False

        self.trigger_mode = self.trigger_mode_var.get()
        self.gen_mode = self.gen_mode_var.get()

        if (self.trigger_mode == "time"):
            try:
                self.update_interval = int(float(self.time_var.get()) * 1000)
            except ValueError:
                messagebox.showerror("error", "invalid time interval")
                return False

            if (self.update_interval < RAWACCEL_DELAY):
                messagebox.showerror("error", "time must be >= 1.1 seconds")
                return False

        elif (self.trigger_mode == "keybind"):
            if self.keybind.get() == "<null>":
                messagebox.showerror("error", "bind a key to use keybind mode")
                return False

        if (self.base < self.min):
            messagebox.showerror("error", "current sens must be >= desired minimum sens")
            return False

        if (self.base > self.max):
            messagebox.showerror("error", "current sens must be <= desired maximum sens")
            return False

        if (self.gen_mode != "full range" and self.num < 5):
            messagebox.showerror("error", "sens count should be >= 5")
            return False

        elif (self.gen_mode == "full range" and (self.num > 3 or self.num < 0)):
            messagebox.showerror("error", "keep your precision in the range [0, 3] when using \"full range\"")
            return False

        sens_t.BASE_SENS = self.base
        self.generate_senses()
        self.update_display()
        self.redraw_graph()
        self.toggle_button.config(state=tk.NORMAL)
        self.save()
        return True


    def run_twitch_listener(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.twitch_loop = asyncio.get_event_loop()
        self.twitch_listener = twitch_listener(self.twitch_oauth_var.get(), self.twitch_channel_var.get(), self.min, self.max, self.update_interval)
        self.twitch_loop.run_until_complete(self.twitch_listener.start())


    def toggle_rawrand(self):
        if SENSES == None:
            self.apply_settings()

        self.running = not self.running

        if self.running:
            self.running = self.apply_settings()
            if not self.running:
                return

            if self.twitch_window:
                self.twitch_window.destroy()
                self.twitch_window = None

            self.dt = -1
            self.toggle_button.config(text = "stop")
            self.apply_button.config(state=tk.DISABLED)
            self.keybind_button.config(state=tk.DISABLED)
            self.twitch_button.config(state=tk.DISABLED)

            if (self.twitch_enabled.get()):
                self.twitch_thread = threading.Thread(target=self.run_twitch_listener, daemon = True)
                self.twitch_thread.start()


            if (self.trigger_mode == "keybind"):
                if (self.keybind.get() in [ "left", "right", "middle", "mouse4", "mouse5"]):
                    self.trigger_dev = trigger_devs.MOUSE

                elif (self.keybind.get() in [ "mwdown", "mwup", "mwleft", "mwright"]):
                    self.trigger_dev = trigger_devs.SCROLL

                else:
                    self.trigger_dev = trigger_devs.KEYBOARD

            self.update_loop()

        elif not self.running:

            if self.graph_upd:
                self.root.after_cancel(self.graph_upd)
                self.graph_upd = None

            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None

            if self.bind_listener:
                self.bind_listener.stop()
                self.bind_listener = None

            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None

            if self.twitch_loop:
                self.twitch_loop.call_soon(lambda: asyncio.create_task(self.twitch_listener.close()))
                self.twitch_loop = None

            if self.twitch_thread:
                self.twitch_thread = None

            self.trigger_dev = trigger_devs.NONE
            self.toggle_button.config(text = "start")
            self.apply_button.config(state=tk.NORMAL)
            self.keybind_button.config(state=tk.NORMAL)
            self.twitch_button.config(state=tk.NORMAL)

            if self.dt < RAWACCEL_DELAY:
                self.root.after(float(RAWACCEL_DELAY - self.dt), reset)
            else:
                reset()
            self.redraw_graph()


    def keybind_trigger(self, a, _ = 0, x = 0, y = 0):
        if self.dt < RAWACCEL_DELAY:
            return

        if (self.trigger_dev == trigger_devs.KEYBOARD):
            key = a.char if hasattr(a, "char") else str(a)[4:]

        elif (self.trigger_dev == trigger_devs.MOUSE):
            if (not y):
                return

            key = str(x)[7:]

            if key[0] == 'x':
                key = "mouse" + str(int(key[-1]) + 3)

        elif (self.trigger_dev == trigger_devs.SCROLL):
            if y == 1:
                key = "mwup"
            elif y == -1:
                key = "mwdown"
            elif x == 1:
                key = "mwright"
            elif x == -1:
                key = "mwleft"

        if key == self.keybind.get():
            self.update_sens()


    def update_sens(self):
        self.graph_upd = self.root.after(RAWACCEL_DELAY, self.redraw_graph)
        self.dt = 0
        self.prev2 = self.prev
        self.prev = self.sens
        with sens_lock:
            self.sens = SENSES.popleft()
            SENSES.append(self.sens)
        set_sens(self.sens.sens)


    def update_loop(self):
        if self.running:
            if self.dt == -1:
                self.update_sens()
                self.redraw_graph()

                if (self.trigger_mode == "keybind"):
                    if (self.trigger_dev == trigger_devs.KEYBOARD):
                        self.bind_listener = keyboard.Listener(on_press=self.keybind_trigger)
                        self.bind_listener.start()

                    elif (self.trigger_dev == trigger_devs.MOUSE):
                        self.mouse_listener = mouse.Listener(on_click=self.keybind_trigger)
                        self.mouse_listener.start()

                    elif (self.trigger_dev == trigger_devs.SCROLL):
                        self.mouse_listener = mouse.Listener(on_scroll=self.keybind_trigger)
                        self.mouse_listener.start()

            if self.trigger_mode == "time":
                if self.dt >= self.sens.time:
                    self.update_sens()

            self.update_display()
            self.dt += 100
            self.after_id = self.root.after(100, self.update_loop)


if __name__ == "__main__":
    global DEFAULT_MULT

    with open("latest-dump.log", "w") as l:
        l.write("")

    plt.rcParams["text.color"] = "white"
    plt.rcParams["axes.labelcolor"] = "white"
    plt.rcParams["xtick.color"] = "white"
    plt.rcParams["ytick.color"] = "white"
    plt.rcParams["axes.titlecolor"] = "white"
    plt.rcParams["legend.edgecolor"] = "white"

    try:
        with open("../settings.json", "r") as settings_json:
            DEFAULT_MULT = dict(json.load(settings_json))["profiles"][0]["Sensitivity multiplier"]
    except:
        messagebox.showerror("error", "could not find rawaccel's settings.json in parent directory. make sure you've run it at least once to generate settings.json")
        sys.exit(1)

    try:
        with open("./config.json", "r") as config:
            config = dict(json.load(config))
    except:
        config = { }

    key = key_t()

    try:
        twitch_oauth = key.load_password("./.twitch_oauth")
    except:
        twitch_oauth = None

    root : tk.Tk = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_exit)
    app = rawrand(root, config, twitch_oauth)

    try:
        root.mainloop()

    except KeyboardInterrupt:
        on_exit()

    except Exception as e:
        app.force_stop()
        log_dump(e)
        messagebox.showerror("error", f"{e}")
        on_exit(1)
