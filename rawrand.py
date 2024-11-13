import json
import random
import subprocess
from time import sleep
from typing import List
import numpy as np
from scipy.interpolate import interp1d
from scipy import stats
import atexit
import statistics
import argparse
from collections import deque


class sens_t(object):
    BASE_SENS : float = 1.0

    @staticmethod
    def get_multi(sens : float) -> float:
        return sens / sens_t.BASE_SENS

    @staticmethod
    def game_sens(sens) -> float:
        return sens * sens_t.BASE_SENS

    def __init__(self, sens : float, time : float):
        self.sens : float = sens
        self.time : float = time

    def __repr__(self) -> str:
        return f"<sens_t>(sens: {self.sens}, time: {self.time})"

    def __str__(self) -> str:
        return f"{self.sens :.3f} for {self.time :.1f}s"


def set_sens(x : float) -> None:
    global rawaccel

    with open("settings.json", "r") as settings_json:
        settings = dict(json.load(settings_json))
        settings["profiles"][0]["Sensitivity multiplier"] = x * DEFAULT_MULT

    with open("settings.json", "w") as settings_json:
        json.dump(settings, settings_json)

    subprocess.Popen("../writer.exe settings.json")


def do_interp(senses : List[float]) -> List[float]:
    senses.append(senses[0])
    indices = np.arange(len(senses))
    distances = np.diff(senses)
    new_indices = []

    for i, dist in enumerate(distances):
        num_points = int(abs(dist) * 10) + 2
        new_interval = np.linspace(indices[i], indices[i + 1], num=num_points)
        new_indices.extend(new_interval)

    new_indices = np.array(new_indices)
    senses = list(interp1d(indices, senses, kind = "linear")(new_indices))
    return senses


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


parser = argparse.ArgumentParser(description = "uses rawaccel to randomise your sens")

parser.add_argument("--interp", "-i", action = "store_true",  dest = "interp", help = "enable interpolation to make sens changes less jarring")
parser.add_argument("--sens",   "-s", dest = "sens",    type = float,   default = 0.300,    required = True,    help = "your current in-game sens")
parser.add_argument("--min",          dest = "min",     type = float,   default = 0.200,    required = True,    help = "the minimum sens you want the randomiser to set your sens to")
parser.add_argument("--max",          dest = "max",     type = float,   default = 0.800,    required = True,    help = "the maximum sens you want the randomiser to set your sens to")
parser.add_argument("--num",    "-n", dest = "num",     type = int,     default =   250,    required = False,   help = "the number of senses you want to be generated")
parser.add_argument("--time",   "-t", dest = "time",    type = float,   default =    15,    required = False,   help = "how long (in seconds) each sens should be set for (min. 1.5)")
parser.add_argument("--mode",   "-m", dest = "mode",    type = int,     default =     0,    required = False,
                        help = "changes the mode of sens generation [ 0: random (default), 1: truncated normal dist, 2: fixed mean random, 3: lognormal ]",
                        choices = [0, 1, 2, 3]
                    )

args = parser.parse_args()

if (args.sens < args.min):
    raise ValueError("current sens must be >= desired minimum sens")

if (args.sens > args.max):
    raise ValueError("current sens must be <= desired maximum sens")

if (args.num < 5):
    raise ValueError("sens count should be >= 5")

if (args.time < 1.5):
    raise ValueError("time must be >= 1.5 seconds")

sens_t.BASE_SENS = args.sens


def main() -> None:
    global DEFAULT_MULT

    senses = []

    with open("../settings.json", "r") as settings_json:
        DEFAULT_MULT = dict(json.load(settings_json))["profiles"][0]["Sensitivity multiplier"]

    if args.mode == 0:
        senses = [ random.uniform( sens_t.get_multi(args.min), sens_t.get_multi(args.max) ) for _ in range(args.num) ]

    elif args.mode == 1:
        senses = stats.truncnorm( sens_t.get_multi(args.min) - 1, sens_t.get_multi(args.max) - 1, loc = 1, scale = 1 ).rvs(args.num)

    elif args.mode == 2:
        senses = fixed_mean_rand( 1, sens_t.get_multi(args.min), sens_t.get_multi(args.max), args.num )

    elif args.mode == 3:
        senses = [ sens for sens in stats.lognorm(loc = .5, s = .5, scale = .5).rvs(args.num) if sens <= sens_t.get_multi(args.max) and sens_t.get_multi(args.min) <= sens ]

    random.shuffle(senses)

    if args.interp is True:
        senses = do_interp(senses)

    senses = [ round(sens, 5) for sens in senses ]

    print( f"generated {len(senses)} senses:" )
    mean = statistics.mean(senses)
    print( f"avg -> {sens_t.game_sens(mean) :.3f}  [{sens_t.BASE_SENS} {'-' if mean < 0 else '+'} {(abs(mean - 1) * 100):.1f}%]" )
    print( f"max -> {sens_t.game_sens(max(senses)) :.3f}" )
    print( f"min -> {sens_t.game_sens(min(senses)) :.3f}" )

    senses = [ sens_t(sens, args.time) for sens in senses ]
    senses = deque(senses)

    try:
        while True:
            sens = senses.popleft()
            senses.append(sens)

            set_sens(sens.sens)
            sleep(1) # gotta account for rawaccel's built in delay

            print(f"\tcurrent in-game sens: {sens_t.game_sens(sens.sens) :.3f} for {sens.time:.1f}s", end = "\r")
            sleep(sens.time - 1)

    except KeyboardInterrupt:
        return


def on_exit() -> None:
    subprocess.run("reset.bat", stdout = subprocess.DEVNULL);
atexit.register(on_exit)


if __name__ == "__main__":
    main()
