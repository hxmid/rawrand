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

## features

- different sensitivity randomisation methods:

    - 1. true random

    - 2. truncated normal distribution
        - should have the average sensitivity closer to your base sens

    - 3. fixed mean randomisation
        - keeps the mean of the generated sensitivities very close to your base sens, within 5%

    - 4. log normal

    - 5. full range
        - adds the entire min-max range, where num becomes the accuracy

- sensitivity interpolation, smoothing out transitions between each sens

- anticheat compliant (assuming the anticheat allows rawaccel)

- game agnostic, due to it only needing a base sens, and min/max sens range

- intuitive use

- a graph showing upcoming senses

## planned features

- [ ] key press triggered sensitivity switch
    - rather than having the sensitivities switch on time interval, have it mapped to a keybind. this will make it less jarring mid-round or mid-gunfight

- [ ] twitch integration
    - allow chatters to give a sens and it to automatically set your sens to that for x seconds

- [ ] game state monitoring
    - possibly leveraging overwolf's api, monitor the game's gamestate to allow for sensitivity changes to happen at the end of each round

- [ ] installer and (embedded python OR rewrite in a different language)
    - just so you don't have to manually install everything, should quicken the process dramatically
    - rewriting in a different language would in theory speed it up, but computers are fast enough nowadays and this program is pretty lightweight so i don't think it's necessary

## installation

1. install [git for windows](https://git-scm.com/downloads/win)

2. install python (i'm using [3.11.7](https://www.python.org/downloads/release/python-3117/))

3. install [rawaccel](https://github.com/a1xd/rawaccel) and run it at least once so that `settings.json` is generated

4. clone the repo into your rawaccel folder
```
git clone https://github.com/hxmid/rawrand.git
```

the folder structure should look something like this:

```
rawaccel/
    rawrand/
        rawrand.pyw
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

6. copy the `settings.json` file from the rawaccel folder into the `rawrand` folder

7. run the randomiser from the bat file included, `rawrand.bat`

## updating

just run the `update.bat` file, it'll pull the latest version from the github repo and install any pip packages required

make sure to read the readme file, there might be some other changes / new features
