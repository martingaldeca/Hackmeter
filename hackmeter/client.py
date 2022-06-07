import logging
import hashlib
import json
import datetime
import requests
DATE_FORMAT = '%Y-%m-%d'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class WorkmeterClient:
    host = 'timework.workmeter.com'
    base_url = 'https://timework.workmeter.com'
    client_id = 'manualApp'
    grant_type = 'password'
    headers = None
    token = None
    reported_days = []
    expected_days = {}
    holidays = []
    start_day = None
    timetables = {}
    userid = None

    def __init__(
        self,
        start_day: str,
        holidays: list,
        timetables: dict,
        with_login: bool = True,
        username: str = None,
        password: str = None,
    ) -> None:
        self.start_day = datetime.datetime.strptime(start_day, DATE_FORMAT).date()
        self.timetables = timetables
        self.holidays = holidays
        self.headers = {
            'Host': self.host,
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/App/Index'
        }
        if with_login and username and password:
            self.login(username=username, password=password)
            self.get_current_user()

    def login(self, username: str, password: str) -> None:
        body = {
            'grant_type': self.grant_type,
            'client_id': self.client_id,
            'username': username,
            'password': hashlib.md5(password.encode()).hexdigest(),
            'hashed': '1'
        }
        logging.info(f'Trying to connect to workmeter with user {username}')
        response = requests.post(f'{self.base_url}/Token', body, headers=self.headers)
        if response.status_code == 200:
            logging.info('Login complete')
            self.token = json.loads(response.content.decode()).get('access_token')
            self.headers['Authorization'] = f'Bearer {self.token}'
        else:
            raise Exception('Login failed')

    def get_current_user(self):
        logging.info('Trying to obtain user extra info')
        response = requests.get(f'{self.base_url}/api/Proposal/current-user', headers=self.headers)
        if response.status_code == 200:
            logging.info('Info obtained')
            self.userid = json.loads(response.content.decode())[0].get('usrid')
        else:
            raise Exception('error obtaining info')

    def report_day(self, day: str, expected_minutes: int):

        timetable = self.timetables[expected_minutes]
        for start_time, end_time in timetable:

            # Must add 2 hours in Spain
            start_time_datetime = datetime.datetime.strptime(start_time, '%H:%M')
            start_time_datetime += datetime.timedelta(hours=2)
            end_time_datetime = datetime.datetime.strptime(end_time, '%H:%M')
            end_time_datetime += datetime.timedelta(hours=2)

            body = {
                'action': 'ADD',
                'appid': 0,
                'dateStart': f'{day}T{start_time_datetime.strftime("%H:%M")}:00.000Z',
                'dateEnd': f'{day}T{end_time_datetime.strftime("%H:%M")}:00.000Z',
            }
            response = requests.post(f'{self.base_url}/api/EditData/ManualReporting', body, headers=self.headers)
            if response.status_code == 200:
                self.reported_days.append(day)
            else:
                raise Exception(f'Problem reporting {expected_minutes} for the day {day}')
        logging.info(f'{expected_minutes} minutes have been reported for the day {day}')

    def check_day_reporting(self, day: datetime.date):
        end_day = day + datetime.timedelta(days=1)
        logging.info(f'Trying to obtain day report for {day.isoformat()}')
        response = requests.get(
            f'{self.base_url}/api/DataReader/TimeControlScheduleDataUser/{self.userid}?'
            f'startdate={day.strftime(DATE_FORMAT)}&'
            f'enddate={end_day.strftime(DATE_FORMAT)}&fillblanks=true',
            headers=self.headers
        )
        if response.status_code == 200:
            logging.info(f'Day report obtained for {day.isoformat()}')
            day_report = json.loads(response.content.decode())
            for report in day_report:

                # TODO in the future calculate the reported time and optimize the reports
                date_reported = report['date']
                date_reported = f'{date_reported[6:]}-{date_reported[3:5]}-{date_reported[:2]}'
                if report.get('tasks') and date_reported not in self.reported_days:
                    self.reported_days.append(date_reported)
                    logging.info(f'Day {date_reported} was previously reported')

            self.reported_days = list(set(self.reported_days))

        else:
            raise Exception(f'Day {day.isoformat()} problem.')

    def get_reported_days(
        self,
        end_day: datetime.date = datetime.date.today()
    ) -> None:
        for n in range(int((end_day - self.start_day).days)):
            self.check_day_reporting(day=self.start_day + datetime.timedelta(days=n))

    def get_expected_calendar(
        self,
        year: int = datetime.date.today().year,
        until: datetime.date = datetime.date.today() - datetime.timedelta(days=1)
    ):
        logging.info(f'Obtaining calendar for year {year}')
        response = requests.get(
            f'{self.base_url}/api/Calendar/{year}/User/{self.userid}',
            headers=self.headers
        )
        if response.status_code == 200:
            logging.info(f'Calendar obtained for year {year}')
            calendar = json.loads(response.content.decode())
            for day in calendar:
                if (
                    (expected_day := day['date'][:10]) and
                    until.isoformat() >= expected_day >= self.start_day.isoformat() and
                    expected_day not in self.holidays and
                    (expected_minutes := day.get('expected'))
                ):
                    self.expected_days[day['date'][:10]] = expected_minutes
        else:
            raise Exception(f'Error obtaining calendar for year "{year}".')

    def report(self):
        logging.info('Reporting all ')
        for expected_day, expected_minutes in self.expected_days.items():
            if expected_day not in self.reported_days:
                self.report_day(day=expected_day, expected_minutes=expected_minutes)
