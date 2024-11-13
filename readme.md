# rawrand

## overview

a sensitivity randomiser piggy-backing off of rawaccel's mouse driver

(i am australian i will be spelling randomiser with an 's', not a 'z')

this was primarily developed for valorant, however due to the nature of it piggy-backing off of rawaccel, it will work in any game that also allows rawaccel (overwatch, cs, etc.)

## how it works

random base sensitivity multipliers are generated and then written to the rawaccel mouse driver using rawaccel's 'writer.exe'

## known issues

- your actual cursor sensitivity changes with the 'random' sensitivity. this makes your sensitivity in ui's very inconsistent, which might make it hard to due things such as by items or properly align smokes on some one like clove or brimstone in valorant.
    - there is no fix for this. this is just the caveat of how the randomiser works.

- if you close the terminal window instead of pressing ctrl+c to exit the program it will **NOT** revert your sensitivity to normal
    - i'm just going to add a wrapper program which runs in the background and handles all the resetting. pretty simple fix.

## features

- different sensitivity randomisation methods:

    - 0. true random

    - 1. truncated normal distribution
        - should have the average sensitivity closer to your base sens

    - 2. fixed mean randomisation
        - keeps the mean of the generated sensitivities very close to your base sens, within 5%

    - 3. log normal

- sensitivity interpolation, smoothing out transitions between each sens

- anticheat compliant (assuming the anticheat allows for rawaccel to be run)

- (relatively) intuitive use

## planned features

- [ ] key press triggered sensitivity switch
    - rather than having the sensitivities switch on time interval, have it mapped to a keybind. this will make it less jarring mid-round or mid-gunfight

- [ ] twitch integration
    - allow chatters to give a sens and it to automatically set your sens to that for x seconds

- [ ] game state monitoring
    - (possibly leveraging overwolf) monitor the game's gamestate to allow for sensitivity changes to happen at the end of each round

- [ ] a proper user interface, similar to rawaccel's
    - [ ] learn how to make ui (no idea how at this point in time LOL)
    - [ ] input values on left side, (e.g. min, max, time interval, etc)
    - [ ] plotted graph of generated senses on right side (like how rawaccel has a visualisation of your curve)

- [ ] installer embedded python
    - just so you don't have to manually install everything, should quicken the process dramatically

## installation

1. install git for windows

2. install python (i'm using 3.11.7)

3. install rawaccel

4. clone the repo into your rawaccel folder
```
git clone https://github.com/hxmid/rawrand.git
```

the folder structure should look something like this:

```
rawaccel/
    rawrand/
        rawrand.py
        wrapper.py
        ...
    rawaccel.exe
    writer.exe
    ...
```

5. cd into the rawrand folder and install the pip packages

```
cd rawrand
pip install -r requirements.txt
```

6. run rawaccel at least once so that settings.json is generated and then copy it into the `rawrand` folder

7. run the randomiser from the `rawrand` folder with python


```
python rawrand.py <args>
```

for an overview on arguments you can use the `--help` argument

```
$ python rawrand.py --help
usage: rawrand.py [-h] [--interp] --sens SENS --min MIN --max MAX [--num NUM] [--time TIME] [--mode {0,1,2,3}]

uses rawaccel to randomise your sens

options:
  -h, --help            show this help message and exit
  --interp, -i          enable interpolation to make sens changes less jarring
  --sens SENS, -s SENS  your current in-game sens
  --min MIN             the minimum sens you want the randomiser to set your sens to
  --max MAX             the maximum sens you want the randomiser to set your sens to
  --num NUM, -n NUM     the number of senses you want to be generated
  --time TIME, -t TIME  how long (in seconds) each sens should be set for (min. 1.5)
  --mode {0,1,2,3}, -m {0,1,2,3}
                        changes the mode of sens generation [ 0: random (default), 1: truncated normal dist, 2: fixed mean random, 3: lognormal ]
```

this is my current config (as of 13th november 2024)

```
python rawrand.py --sens .45 --min .2 --max .97 --time 5 --mode 0
```

once you find some settings that you like, just make a .bat file and run using the `wrapper.pyw` file instead of the actual `rawrand.py` file

we use a wrapper so that your sens auto-resets after you close the program, regardless of whether you accidentally close the terminal window instead of

```bat
@echo off
start /B "" "pythonw" "wrapper.pyw" --sens .45 --min .2 --max .97 --time 5 --mode 0
```
