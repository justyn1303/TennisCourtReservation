import unittest
import sqlite3
from unittest.mock import patch
from io import StringIO
from datetime import timedelta
from main import ReservationSystem


class TestReservationSystem(unittest.TestCase):

    def test_show_menu(self):
        with patch('sys.stdout', new=StringIO()) as test_output:
            ReservationSystem.show_menu()
            expected_output = "What do you want to do:" \
                              "\n1. Make a reservation" \
                              "\n2. Cancel a reservation" \
                              "\n3. Print schedule" \
                              "\n4. Save schedule to a file" \
                              "\n5. Exit\n"
            self.assertEqual(test_output.getvalue(), expected_output)

    def setUp(self):
        self.rs = ReservationSystem()
        self.conn = sqlite3.connect('reservations.db')
        self.c = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_reservation_valid_input(self):
        with patch('builtins.input', side_effect=['Jan', '27.03.2023 20:00', '2']):
            self.rs.reservation()
            self.c.execute("SELECT * FROM reservations WHERE name = 'Jan'")
            rows = self.c.fetchall()
            self.assertEqual(len(rows), 1)

    def test_reservation_invalid_time_input(self):
        with patch('builtins.input', side_effect=['Jan', '27.03.2023 20:00', '2']):
            self.rs.reservation()
            self.c.execute("SELECT * FROM reservations WHERE name = 'Jan'")
            rows = self.c.fetchall()
            self.assertEqual(len(rows), 0)

    def test_reservation_invalid_duration_input(self):
        with patch('builtins.input', side_effect=['Jan', '28.03.2023 14:00', '4']):
            self.rs.reservation()
            self.c.execute("SELECT * FROM reservations WHERE name = 'Jan'")
            rows = self.c.fetchall()
            self.assertEqual(len(rows), 0)

    def test_cancel_reservation(self):
        with patch('builtins.input', side_effect=['Jan', '29.03.2023 14:00']):
            self.rs.reservation()
        with patch('builtins.input', side_effect=['Jan', '29.03.2023 14:00']):
            self.rs.cancel_reservation()
            self.c.execute("SELECT * FROM reservations WHERE" " name = 'Jan' AND start_time = '27-03-2023 14:00:00'")
            self.assertIsNone(self.c.fetchone())

    def test_print_schedule(self):
        self.c.execute('''INSERT INTO reservations(name, start_time, end_time) 
                        VALUES(?,?,?)''', ("Jan Nowak", self.week_start, self.week_start + timedelta(hours=1)))
        self.db_conn.commit()

        expected_output = f"{self.week_start.strftime('%d-%m-%Y')}:\n" \
                          f"{self.week_start.strftime('%H:%M')} - " \
                          f"{(self.week_start + timedelta(hours=1)).strftime('%H:%M')}" \
                          f" Jan Nowak\n"
        with patch('sys.stdout', new=StringIO()) as test_output:
            self.rs.print_schedule()
            self.assertEqual(test_output.getvalue(), expected_output)


if __name__ == '__main__':
    unittest.main()
