from hackmeter.client import WorkmeterClient
import yaml
from yaml.loader import SafeLoader


def start():
    # Read the configuration
    with open('./hackmeter/configuration.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)

    client = WorkmeterClient(
        username=data['UserConfiguration']['username'],
        password=data['UserConfiguration']['password'],
        start_day=data['DatesConfiguration']['startDay'],
        holidays=data['Holidays'],
        timetables=data['TimeTables']
    )
    client.get_reported_days()
    client.get_expected_calendar()
    client.report()
