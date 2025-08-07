# rawrand


## overview

a sensitivity randomiser piggy-backing off of rawaccel's mouse driver

(i am australian i will be spelling randomiser with an 's', not a 'z')

this was primarily developed for valorant, however due to the nature of it piggy-backing off of rawaccel, it will work in any game that also allows rawaccel (overwatch, cs, etc.)


## how it works

random base sensitivity multipliers are generated and then written to the rawaccel mouse driver using rawaccel's 'writer.exe'


## caveats

- your actual cursor sensitivity changes with the 'random' sensitivity. this makes your sensitivity in ui's very inconsistent, which might make it a bit jarring to due things such as buy items or properly align smokes on someone like clove or brimstone in valorant.
    - there is no fix for this. this is just the caveat of how rawaccel works.

- when using keybind and game state mode, there is a 1 second delay between event/keybind press and your sens changing, due to rawaccels built-in delay
    - again, there is no fix for this


## known issues

- sometimes when stopping the program your sens doesn't auto reset due to the multithreading added by the twitch integration.
    - i'm not sure where exactly this stems from, so it might take some time until it's fixed
    - however, closing the program will collectly reset your sens


## features

- realtime twitch chat integration
    - allows for your chat to control your sens for you (still keeping it within your predefined range to avoid abuse)

- different sensitivity randomisation methods:

    - 1. true random

    - 2. truncated normal distribution
        - should have the average sensitivity closer to your base sens

    - 3. fixed mean randomisation
        - keeps the mean of the generated sensitivities very close to your base sens, within 5%

    - 4. log normal

    - 5. full range
        - adds the entire min-max range, where num becomes the accuracy

- time based and keybind triggers (key, mouse button or scrollwheel) for sens change

- sensitivity interpolation, smoothing out transitions between each sens

- anticheat compliant (assuming the anticheat allows rawaccel)

- game agnostic, due to it only needing a base sens, and min/max sens range
    - in theory this will work in any game that allows rawaccel to run, no need for sens converters or anything

- intuitive use

- a graph showing upcoming senses


## planned features

- [ ] game state monitoring
    - possibly leveraging overwolf's api, monitor the game's gamestate to allow for sensitivity changes to happen at the end of each round

- [ ] installer and (embedded python OR rewrite in a different language)
    - just so you don't have to manually install everything, should quicken the process dramatically
    - rewriting in a different language would in theory speed it up, but computers are fast enough nowadays and this program is pretty lightweight so i don't think it's necessary

- [ ] built-in writer
    - as of right now, the program just uses rawaccel's writer.exe to write the new senses to the driver, however having a built-in one would reduce dependencies and overhead (i think)

- [ ] custom built mouse driver without delay
    - not much planning behind this, as this is something that will take a lot of work
    - the main reason i would want something like this is to eliminate the 1s delay in rawaccel, but i think that's intentionally in place to prevent abuse, so more thinking is required


## installation

1. install [git for windows](https://git-scm.com/downloads/win)

2. install python (i'm using [3.11.7](https://www.python.org/downloads/release/python-3117/))

    - be sure to tick the "add python to environment variables" checkbox

3. install [rawaccel](https://github.com/a1xd/rawaccel) and run it at least once so that `settings.json` is generated

4. clone the repo into your rawaccel folder

```sh
git clone https://github.com/hxmid/rawrand.git
```

the folder structure should look something like this:

```sh
rawaccel/
    rawrand/
        rawrand.pyw
        ...
    rawaccel.exe
    writer.exe
    ...
```

5. cd into the rawrand folder and install the pip packages

```sh
cd rawrand
pip install -r requirements.txt
```

6. copy the `settings.json` file from the rawaccel folder into the `rawrand` folder

```bat
copy ..\settings.json .
```

7. run the randomiser from the bat file included, `rawrand.bat`


## twitch integration

1. for twitch integration, click the twitch button in the main menu

2. specify your twitch channel, then go to [this website](https://twitchtokengenerator.com/)

3. enable the `chat:read` scope (it's the only scope we need)

4. generate the token and copy the whole thing into the oauth field, including the `oauth:` part

5. regenerate and start


### format

right now, the only thing chatters can do is add a sens to the pool, with the following format

```
.sens <sens>
```

e.g.

```
.sens .5
```

note that a chatted sens will be ignored if it is outside of your sens range


## updating

just run the `update.bat` file, it'll pull the latest version from the github repo and install any pip packages required

make sure to read the readme file, there might be some other changes / new features


## reporting issues

just make an issue here on the github page. if you can include any steps to reproduce that'd be great

if you have a problem where your sens didn't reset after closing, just run `reset.bat`


