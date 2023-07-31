import datetime
import random
from unittest import mock
from unittest import TestCase

from hackmeter.client import WorkmeterClient

DATE_FORMAT = '%Y-%m-%d'


class ClientTest(TestCase):
    def setUp(self) -> None:
        self.username = 'test_username'
        self.password = 'test_password'
        self.start_day = '2022-01-01'
        self.holidays = ['2022-08-08', '2022-07-28']
        self.timetables = {
            250: [['06:00', '21:59'], ]  # Welcome to the bank
        }

    def test_creation(self):
        with mock.patch.object(
            WorkmeterClient, 'login'
        ) as mock_login, mock.patch.object(
            WorkmeterClient, 'get_current_user'
        ) as mock_get_current_user:
            WorkmeterClient(
                username=self.username,
                password=self.password,
                start_day=self.start_day,
                holidays=self.holidays,
                timetables=self.timetables
            )
        self.assertEqual(mock_login.call_count, 1)
        self.assertEqual(
            mock_login.call_args,
            mock.call(
                username=self.username,
                password=self.password
            )
        )
        self.assertEqual(mock_get_current_user.call_count, 1)

    def test_login(self):
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        with mock.patch('requests.post') as mock_post:
            response = mock.MagicMock()
            response.status_code = 200
            response.content = b'{"access_token": "test_token"}'
            mock_post.return_value = response
            client.login(username=self.username, password=self.password)
            self.assertEqual(client.token, 'test_token')
            self.assertEqual(client.headers['Authorization'], 'Bearer test_token')

    def test_login_status_code_not_200_raise_exception(self):
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        with mock.patch(
            'requests.post'
        ) as mock_post, self.assertRaises(
            Exception
        ):
            response = mock.MagicMock()
            response.status_code = 400
            mock_post.return_value = response
            client.login(username=self.username, password=self.password)

    def test_get_current_user(self):
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        with mock.patch(
            'requests.get'
        ) as mock_get:
            response = mock.MagicMock()
            response.status_code = 200
            response.content = b'[{"usrid": 1994}]'
            mock_get.return_value = response
            client.get_current_user()
            self.assertEqual(client.userid, 1994)

    def test_get_current_user_status_code_not_200_raise_exception(self):
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        with mock.patch(
            'requests.get'
        ) as mock_get, self.assertRaises(
            Exception
        ):
            response = mock.MagicMock()
            response.status_code = 400
            mock_get.return_value = response
            client.get_current_user()

    def test_report_day(self):
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        client.reported_days = []
        client.userid = 1234
        day = '1994-08-08'
        expected_minutes = list(self.timetables.keys())[0]
        with mock.patch(
            'requests.post'
        ) as mock_post:
            response = mock.MagicMock()
            response.status_code = 200
            mock_post.return_value = response

            client.report_day(day, expected_minutes)
            expected_body = {
                'action': 'ADD',
                'appid': 0,
                'dateStart': f'{day}T08:00:00.000Z',
                'dateEnd': f'{day}T23:59:00.000Z',
            }
            self.assertEqual(
                mock_post.call_args,
                mock.call(
                    f'{client.base_url}/api/EditData/ManualReporting',
                    expected_body,
                    headers=client.headers
                )
            )
            self.assertEqual(client.reported_days, [day, ])

    def test_report_day_status_code_not_200_raise_exception(self):
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        day = '1994-08-08'
        expected_minutes = list(self.timetables.keys())[0]
        with mock.patch(
            'requests.post'
        ) as mock_post, self.assertRaises(
            Exception
        ):
            response = mock.MagicMock()
            response.status_code = 400
            mock_post.return_value = response

            client.report_day(day, expected_minutes)

    def test_check_day_reporting(self):
        day = datetime.date(year=1994, month=8, day=8)

        test_data_list = [
            [
                b'['
                b'{"date": "08/08/1994", "tasks": []}'
                b']',
                []
            ],
            [
                b'['
                b'{"date": "08/08/1994", "tasks": [{"from": "1970-01-01T08:00:00Z", "to": "1970-01-01T23:59:00Z"}]} '
                b']',
                ['1994-08-08']
            ],
            [
                b'['
                b'{"date": "08/08/1994", "tasks": [{"from": "1970-01-01T08:00:00Z", "to": "1970-01-01T23:59:00Z"}]}, '
                b'{"date": "08/08/1994", "tasks": [{"from": "1970-01-01T08:00:00Z", "to": "1970-01-01T23:59:00Z"}]} '
                b']',
                ['1994-08-08']
            ],
            [
                b'['
                b'{"date": "08/08/1994", "tasks": [{"from": "1970-01-01T08:00:00Z", "to": "1970-01-01T23:59:00Z"}]}, '
                b'{"date": "28/07/1994", "tasks": [{"from": "1970-01-01T08:00:00Z", "to": "1970-01-01T23:59:00Z"}]} '
                b']',
                ['1994-08-08', '1994-07-28']
            ],
        ]

        '[["date": "08/08/1994", "tasks": []] ]'
        for test_data in test_data_list:
            with self.subTest(
                test_data=test_data
            ), mock.patch(
                'requests.get'
            ) as mock_get:
                response_content, expected_reported_days = test_data
                client = WorkmeterClient(
                    start_day=self.start_day,
                    holidays=self.holidays,
                    timetables=self.timetables,
                    with_login=False
                )
                response = mock.MagicMock()
                response.status_code = 200
                response.content = response_content
                mock_get.return_value = response
                client.check_day_reporting(day)
                self.assertEqual(set(client.reported_days), set(expected_reported_days))

    def test_check_day_reporting_status_code_not_200_raise_exception(self):
        day = datetime.date(year=1994, month=8, day=8)
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        with mock.patch(
            'requests.post'
        ) as mock_post, self.assertRaises(
            Exception
        ):
            response = mock.MagicMock()
            response.status_code = 400
            mock_post.return_value = response
            client.check_day_reporting(day)

    def test_get_reported_days(self):
        total_days = random.randint(1, 10)
        end_day = datetime.datetime.strptime(self.start_day, DATE_FORMAT).date() + datetime.timedelta(days=total_days)
        client = WorkmeterClient(
            start_day=self.start_day,
            holidays=self.holidays,
            timetables=self.timetables,
            with_login=False
        )
        with mock.patch.object(WorkmeterClient, 'check_day_reporting') as mock_check_day_reporting:
            client.get_reported_days(end_day)

            self.assertEqual(mock_check_day_reporting.call_count, total_days)

    def test_get_expected_calendar(self):
        test_data_list = [
            [
                '1994-08-08',
                [],
                1994,
                datetime.date(year=1994, month=8, day=8),
                b'[{"date": "1994-08-08T00:00:00Z", "expected": 1440}]',
                {'1994-08-08': 1440}
            ],
            [
                '1994-08-08',
                [],
                1994,
                datetime.date(year=1994, month=7, day=28),
                b'[{"date": "1994-08-08T00:00:00Z", "expected": 1440}]',
                {}
            ],
            [
                '2022-08-08',
                [],
                1994,
                datetime.date(year=1994, month=7, day=28),
                b'[{"date": "1994-08-08T00:00:00Z", "expected": 1440}]',
                {}
            ],
            [
                '1994-08-08',
                ['1994-08-08', ],
                1994,
                datetime.date(year=1994, month=8, day=8),
                b'[{"date": "1994-08-08T00:00:00Z", "expected": 1440}]',
                {}
            ],
        ]
        for test_data in test_data_list:
            with self.subTest(
                test_data=test_data
            ), mock.patch(
                'requests.get'
            ) as mock_get:
                start_day, holidays, year, until, response_content, expected_days = test_data
                client = WorkmeterClient(
                    start_day=start_day,
                    holidays=holidays,
                    timetables=self.timetables,
                    with_login=False
                )
                client.expected_days = {}
                response = mock.MagicMock()
                response.status_code = 200
                response.content = response_content
                mock_get.return_value = response
                client.get_expected_calendar(year, until)
                self.assertEqual(client.expected_days, expected_days)

    def test_get_expected_calendar_status_code_not_200_raise_exception(self):
        year = 1994
        until = datetime.date(year=1994, month=8, day=8)
        with mock.patch(
            'requests.get'
        ) as mock_get, self.assertRaises(
            Exception
        ):
            client = WorkmeterClient(
                start_day=self.start_day,
                holidays=self.holidays,
                timetables=self.timetables,
                with_login=False
            )
            client.expected_days = {}
            response = mock.MagicMock()
            response.status_code = 400
            mock_get.return_value = response
            client.get_expected_calendar(year, until)

    def test_report(self):

        test_data_list = [
            [{'1994-08-08': 1440}, [], 1],
            [{'1994-08-08': 1440, '1994-07-28': 1440}, [], 2],
            [{'1994-08-08': 1440, '1994-07-28': 1440}, ['1994-08-08'], 1],
        ]
        for test_data in test_data_list:
            with self.subTest(
                test_data=test_data
            ), mock.patch.object(
                WorkmeterClient, 'report_day'
            ) as mock_expected_days:
                expected_days, reported_days, call_count_expected = test_data

                client = WorkmeterClient(
                    start_day=self.start_day,
                    holidays=self.holidays,
                    timetables=self.timetables,
                    with_login=False
                )
                client.expected_days = expected_days
                client.reported_days = reported_days
                client.report()
                self.assertEqual(mock_expected_days.call_count, call_count_expected)
