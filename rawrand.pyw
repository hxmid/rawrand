from collections import deque
import sys
from time import sleep
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random
import json
import subprocess
from scipy.interpolate import interp1d
import statistics
from typing import Dict, List
from scipy import stats
import numpy as np


class sens_t(object):
    BASE_SENS : float = 1.0

    @staticmethod
    def get_multi(sens : float) -> float:
        return sens / sens_t.BASE_SENS

    @staticmethod
    def scaled_sens(sens) -> float:
        return sens * sens_t.BASE_SENS

    def __init__(self, sens : float, time : float):
        self.sens : float = sens
        self.time : float = time


def set_sens(x : float) -> None:
    global rawaccel

    with open("settings.json", "r") as settings_json:
        settings = dict(json.load(settings_json))
        settings["profiles"][0]["Sensitivity multiplier"] = x * DEFAULT_MULT

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

RAWACCEL_DELAY = 1100

def reset():
    subprocess.Popen("reset.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

class rawrand:
    def __init__(self, root, config: Dict):
        self.root = root
        self.root.title("rawrand")

        # window size
        self.root.geometry("425x300")
        self.root.resizable(False, False)

        # main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # left frame
        input_frame = ttk.LabelFrame(main_frame, text="config", padding="5")
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.N)

        # base sens
        ttk.Label(input_frame, text="base:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.base_var = tk.StringVar(value=config.get("base"))
        self.base_entry = ttk.Entry(input_frame, textvariable=self.base_var, width=15)
        self.base_entry.grid(row=0, column=1, padx=5, pady=2)

        # min sens
        ttk.Label(input_frame, text="min:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.min_var = tk.StringVar(value=config.get("min"))
        self.min_entry = ttk.Entry(input_frame, textvariable=self.min_var, width=15)
        self.min_entry.grid(row=1, column=1, padx=5, pady=2)

        # max sens
        ttk.Label(input_frame, text="max:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.max_var = tk.StringVar(value=config.get("max"))
        self.max_entry = ttk.Entry(input_frame, textvariable=self.max_var, width=15)
        self.max_entry.grid(row=2, column=1, padx=5, pady=2)

        # num senses
        ttk.Label(input_frame, text="count:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        self.num_var = tk.StringVar(value=config.get("num"))
        self.num_entry = ttk.Entry(input_frame, textvariable=self.num_var, width=15)
        self.num_entry.grid(row=3, column=1, padx=5, pady=2)

        # sens time
        ttk.Label(input_frame, text="time (s):").grid(row=4, column=0, padx=5, pady=2, sticky=tk.W)
        self.time_var = tk.StringVar(value=config.get("time")/1000)
        self.time_entry = ttk.Entry(input_frame, textvariable=self.time_var, width=15)
        self.time_entry.grid(row=4, column=1, padx=5, pady=2)

        # generation mode
        ttk.Label(input_frame, text="gen. mode:").grid(row=5, column=0, padx=5, pady=2, sticky=tk.W)
        self.gen_mode = tk.StringVar(value=config.get("mode"))
        self.gen_mode_combo = ttk.Combobox(input_frame,
                                      textvariable=self.gen_mode,
                                      values=[ "random", "trunc. norm-dist", "fixed mean", "lognormal" ],
                                      width=12,
                                      state="readonly")
        self.gen_mode_combo.grid(row=5, column=1, padx=5, pady=2)
        self.gen_mode_combo.bind('<<ComboboxSelected>>', lambda e: self.update_display())

        self.interpolation_var = tk.BooleanVar(value=config.get("interp"))
        self.interp_checkbox = ttk.Checkbutton(input_frame,
                                      text="interpolate",
                                      variable=self.interpolation_var)
        self.interp_checkbox.grid(row=6, column=0, columnspan=2, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=7, columnspan=2, padx=10, pady=5, sticky="ns")

        # apply button
        self.apply_button = ttk.Button(button_frame, text="regenerate", command=self.apply_settings)
        self.apply_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky='ew')

        # start/stop button
        self.running = False
        self.toggle_button = ttk.Button(button_frame, text="start", command=self.toggle_rawrand, state=tk.DISABLED)
        self.toggle_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky='ew')

        # init
        self.sens = self.prev = self.prev2 = sens_t(1.0, 0.0)
        self.senses = None
        self.dt = -1

        # display
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ns")

        self.prev_label = ttk.Label(display_frame, text="", font=('Arial', 24), anchor="center")
        self.prev_label.pack(expand=True, fill="both", padx=10, pady=10)

        self.label = ttk.Label(display_frame, text="", font=('Arial', 36), anchor="center")
        self.label.pack(expand=True, fill="both", padx=10, pady=10)

        self.time_left = ttk.Label(display_frame, text="", font=('Arial', 24), anchor="center")
        self.time_left.pack(expand=True, fill="both", padx=10, pady=10)

        self.update_interval = 1500
        self.after_id = None

    def generate_senses(self):
        gen_mode = self.gen_mode.get()

        if gen_mode == "random":
            senses = [ random.uniform( sens_t.get_multi(self.min), sens_t.get_multi(self.max) ) for _ in range(self.num) ]

        elif gen_mode == "trunc. norm-dist":
            senses = stats.truncnorm( sens_t.get_multi(self.min) - 1, sens_t.get_multi(self.max) - 1, loc = 1, scale = 1 ).rvs(self.num)

        elif gen_mode == "fixed mean":
            senses = fixed_mean_rand( 1, sens_t.get_multi(self.min), sens_t.get_multi(self.max), self.num )

        elif gen_mode == "lognormal":
            senses = [ sens for sens in stats.lognorm(loc = .5, s = .5, scale = .5).rvs(self.num) if sens <= sens_t.get_multi(self.max) and sens_t.get_multi(self.min) <= sens ]

        random.shuffle(senses)

        if self.interpolation_var.get() == True:
            senses = interpolate_senses(senses)

        print(f"generated {len(senses)} senses")

        senses = [ round(sens, 5) for sens in senses ]
        self.senses = deque([ sens_t(sens, self.update_interval) for sens in senses ])

    def save(self):
        d = {
            "base": self.base,
            "min": self.min,
            "max": self.max,
            "num": self.num,
            "time": self.update_interval,
            "mode": self.gen_mode.get(),
            "interp": self.interpolation_var.get()
        }
        print("CAN I HIT THIS PLEASE")
        try:
            with open("config.json", "w") as f:
                json.dump(d, f, indent=2)
        except:
            messagebox.showerror("error", "could not save config")

    def update_display(self):
        if self.dt > RAWACCEL_DELAY:
            self.label.config(text=f"{sens_t.scaled_sens(self.sens.sens):.3f}")
            self.prev_label.config(text=f"{sens_t.scaled_sens(self.prev.sens):.3f}")
            self.time_left.config(text=f"{(self.sens.time - self.dt + RAWACCEL_DELAY)/1000:.1f}s")

        else:
            self.label.config(text=f"{sens_t.scaled_sens(self.prev.sens):.3f}")
            self.prev_label.config(text=f"{sens_t.scaled_sens(self.prev2.sens):.3f}")
            self.time_left.config(text=f"{(RAWACCEL_DELAY - self.dt)/1000:.1f}s")


    def apply_settings(self):
        try:
            self.base = float(self.base_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid base sens")

        try:
            self.min = float(self.min_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid min. sens")

        try:
            self.max = float(self.max_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid max. sens")

        try:
            self.num = int(self.num_var.get())
        except ValueError:
            messagebox.showerror("error", "invalid generation num")

        try:
            self.update_interval = int(float(self.time_var.get()) * 1000)
        except ValueError:
            messagebox.showerror("error", "invalid time interval")

        if (self.base < self.min):
            messagebox.showerror("error", "current sens must be >= desired minimum sens")

        if (self.base > self.max):
            messagebox.showerror("error", "current sens must be <= desired maximum sens")

        if (self.num < 5):
            messagebox.showerror("error", "sens count should be >= 5")

        if (self.update_interval < 1.5):
            messagebox.showerror("error", "time must be >= 1.5 seconds")

        sens_t.BASE_SENS = self.base

        self.generate_senses()

        self.update_display()

        self.toggle_button.config(state=tk.NORMAL)

        self.save()



    def toggle_rawrand(self):
        if self.senses == None:
            self.apply_settings()

        self.running = not self.running

        if self.running:
            self.toggle_button.config(text="stop")
            self.update_loop()
            self.apply_button.config(state=tk.DISABLED)

        else:
            self.toggle_button.config(text="start")
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.apply_button.config(state=tk.NORMAL)
            self.toggle_button.config(state=tk.DISABLED)
            self.root.after(RAWACCEL_DELAY, reset)

    def update_loop(self):
        if self.running:
            if self.dt == -1 or self.dt >= self.sens.time:
                self.dt = 0
                self.prev2 = self.prev
                self.prev = self.sens
                self.sens = self.senses.popleft()
                self.senses.append(self.sens)
                set_sens(self.sens.sens)

            self.update_display()
            self.dt += 100
            self.after_id = self.root.after(100, self.update_loop)





def on_exit():
    sleep(float(RAWACCEL_DELAY)/1000.0)
    reset()
    root.quit()
    sys.exit(0)



if __name__ == "__main__":
    global DEFAULT_MULT

    try:
        with open("../settings.json", "r") as settings_json:
            DEFAULT_MULT = dict(json.load(settings_json))["profiles"][0]["Sensitivity multiplier"]
    except:
        messagebox.showerror("could not find rawaccel's settings.json in parent directory")
    try:
        with open("./config.json", "r") as config:
            config = dict(json.load(config))
    except:
        config = {"base": .45, "min": .2, "max": .97, "num": 500, "time": 5000, "mode": "random", "interp": False}
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_exit)
    app = rawrand(root, config)
    root.mainloop()