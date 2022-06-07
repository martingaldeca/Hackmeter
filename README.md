# Hackmeter

The perfect tool for easy reporting

Are you in a bank?, do they make you report with a "notwithstanding the foregoing" tool that you have to have open for it to record your hours?, does the tool work like shit and if you get up to pee it's like you haven't worked?

![](https://www.memecreator.org/static/images/memes/5417035.jpg)

Don't worry, Hackmeter, your ideal tool, is here!

## Installation

Just need the following:
* Python3
* Poetry

## Configuration

There is a file named `configuration.yaml` inside the hackmeter folder. You just must set your username and your password for workmeter.

Also, you can add your holidays in order to not report that days too.

Additionally, you can configure your timetables with the following format:
```yaml
TimeTables:
    MINUTES_TO_REPORT_0: [
      ['FROM', 'TO'],
      ['FROM', 'TO']
    ],
    MINUTES_TO_REPORT_1: [
      ['FROM', 'TO'],
      ['FROM', 'TO']
    ],
  ...
```

## Running the program
Once you have installed python3 and poetry and all the configuration done, just go to the project folder and run the following command:
```shell
poetry run hack
```

And that's all, the magic will start.

![](https://c.tenor.com/4lMPHnN8oeQAAAAM/guy-long-hair.gif)

## Comments

The changes will be reflected in 1 minute in your Workmeter panel after the end of the execution.

