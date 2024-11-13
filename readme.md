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
        - (possibly leveraging overwolf,) monitor the game's gamestate to allow for sensitivity changes to happen at the end of each round

    - [ ] a proper user interface, similar to rawaccel's
        - [ ] learn how to make ui (no idea how at this point in time LOL)
        - [ ] input values on left side, (e.g. min, max, time interval, etc)
        - [ ] plotted graph of generated senses on right side (like how rawaccel has a visualisation of your curve)

## installation

1. install git for windows

2. install python (i'm using 3.11.7)

3. clone the repo into your rawaccel folder
```
rawaccel/
```

the folder structure should look something like this:

```
rawaccel/
    rawrand/
        rawrand.py
        ...
    rawaccel.exe
    writer.exe
    ...
```

4. cd into the rawrand folder and install the pip packages

```
cd rawrand
pip install requirements.txt
```
