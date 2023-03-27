import sqlite3
import csv
import json
from datetime import datetime, timedelta, date


class ReservationSystem:
    def __init__(self):
        self.__switch = None
        self.__db_conn = sqlite3.connect('reservations.db')
        self.__db_cursor = self.__db_conn.cursor()
        self.__create_table()

    def __create_table(self):
        self.__db_cursor.execute('''CREATE TABLE IF NOT EXISTS reservations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL)''')

    @staticmethod
    def show_menu():
        print("What do you want to do:")
        print("1. Make a reservation")
        print("2. Cancel a reservation")
        print("3. Print schedule")
        print("4. Save schedule to a file")
        print("5. Exit")

    def reservation(self):
        print("What's your name?")
        name = input()

        # check if user has more than 2 reservations in the current week
        week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        self.__db_cursor.execute('''SELECT COUNT(*) FROM reservations WHERE name = ? 
                                                AND start_time BETWEEN ? AND ?''',
                                 (name, week_start.strftime('%Y-%m-%d %H:%M:%S'),
                                  week_end.strftime('%Y-%m-%d %H:%M:%S')))
        num_reservations = self.__db_cursor.fetchone()[0]
        if num_reservations >= 2:
            print("You cannot make more than 2 reservations in a week.")
            return

        print("When would you like to book? (DD.MM.YYYY HH:MM)")
        booking_time_str = input()

        # convert user input to datetime object
        booking_time = datetime.strptime(booking_time_str, "%d.%m.%Y %H:%M")

        # check if booking time is in the future
        if booking_time <= datetime.now():
            print("The time you chose has already passed.")
            return

        # check if booking time is less than 1 hour from current time
        time_diff = booking_time - datetime.now()
        if time_diff.total_seconds() < 3600:
            print("You cannot make a reservation less than 1 hour in advance.")
            return

        # check if booking time is available
        while True:
            self.__db_cursor.execute('''SELECT start_time, end_time FROM reservations 
                                            WHERE date(start_time) = ?''',
                                     (booking_time.date(),))
            rows = self.__db_cursor.fetchall()
            for row in rows:
                row_start_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                row_end_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                if booking_time >= row_start_time and booking_time < row_end_time:
                    print("The time you chose is unavailable.")
                    while True:
                        print(
                            f"Would you like to make a reservation for "
                            f"{row_end_time.strftime('%d.%m.%Y %H:%M')} instead? (yes/no)")
                        choice = input()
                        if choice.lower() == "yes":
                            booking_time = row_end_time
                            break
                        elif choice.lower() == "no":
                            print("Returning to previous step...")
                            return
                        else:
                            print("Invalid option. Try again.")
            else:
                break

        # limit the booking options if booking time is after 17:00
        if booking_time.hour >= 17:
            print("How long would you like to book court?")
            print("1) 30 Minutes")
            print("2) 60 Minutes")
            options = ["1", "2"]
        else:
            print("How long would you like to book court?")
            print("1) 30 Minutes")
            print("2) 60 Minutes")
            print("3) 90 Minutes")
            options = ["1", "2", "3"]

        # get user input for booking duration
        while True:
            choice = input("Enter a number: ")
            if choice in options:
                break
            else:
                print("Invalid option. Try again.")

        # calculate end time based on booking duration
        if choice == "1":
            duration = timedelta(minutes=30)
        elif choice == "2":
            duration = timedelta(hours=1)
        else:
            duration = timedelta(minutes=90)

        end_time = booking_time + duration

        # save reservation in the database
        self.__db_cursor.execute('''INSERT INTO reservations(name, start_time, end_time) 
                                         VALUES(?,?,?)''', (name, booking_time, end_time))
        self.__db_conn.commit()

    def cancel_reservation(self):
        print("What's your name?")
        name = input()
        print("What's the start time of the reservation you want to cancel? (DD.MM.YYYY HH:MM)")
        start_time_str = input()

        # convert user input to datetime object
        start_time = datetime.strptime(start_time_str, "%d.%m.%Y %H:%M")

        # check if reservation exists
        self.__db_cursor.execute('''SELECT * FROM reservations WHERE name = ? AND start_time = ?''', (name, start_time))
        reservation_exists = self.__db_cursor.fetchone()
        if reservation_exists is None:
            print("No reservation found with the given name and date.")
            return

        # check if booking time is less than 1 hour from current time
        time_diff = start_time - datetime.now()
        if time_diff.total_seconds() < 3600:
            print("You cannot cancel a reservation less than 1 hour before it starts.")
            return

        # delete reservation from database
        self.__db_cursor.execute('''DELETE FROM reservations WHERE name = ? AND start_time = ?''', (name, start_time))
        self.__db_conn.commit()
        print("Reservation cancelled successfully.")

    def print_schedule(self):
        while True:
            try:
                print("Enter start date (DD.MM.YYYY):")
                start_date_str = input()
                print("Enter end date (DD.MM.YYYY):")
                end_date_str = input()

                # convert user input to datetime objects
                start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
                end_date = datetime.strptime(end_date_str, "%d.%m.%Y")

                # loop through dates and print schedule for each day
                while start_date <= end_date:
                    print(" ")
                    if start_date.date() == date.today():
                        print("Today:")
                    elif start_date.date() == date.today() + timedelta(days=1):
                        print("Tomorrow:")
                    else:
                        print(f"{start_date.strftime('%A')}:")

                    # retrieve reservations for current date
                    self.__db_cursor.execute('''SELECT name, start_time, end_time FROM reservations
                                                 WHERE date(start_time) = ?''',
                                             (start_date.strftime('%Y-%m-%d'),))
                    rows = self.__db_cursor.fetchall()

                    # print reservations for current date
                    if len(rows) == 0:
                        print("No Reservations")
                    else:
                        for row in rows:
                            name = row[0]
                            start_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                            end_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
                            print(
                                f"* {name} {start_time.strftime('%Y-%m-%d %H:%M')} - "
                                f"{end_time.strftime('%Y-%m-%d %H:%M')}")
                    start_date += timedelta(days=1)
                break  # exit loop if all inputs are valid
            except ValueError as e:
                print(f"Invalid input: {e}. Please try again.")

    def save_to_file(self):
        try:
            print("Enter start date (DD.MM.YYYY): ")
            start_date = input()
            print("Enter end date (DD.MM.YYYY): ")
            end_date = input()
            print("Enter file format (csv/json): ")
            file_format = input()
            print("Enter file name: ")
            file_name = input()

            # convert start and end dates to datetime objects
            start_date_obj = datetime.strptime(start_date, "%d.%m.%Y")
            end_date_obj = datetime.strptime(end_date, "%d.%m.%Y")

            # get reservations between start and end dates
            self.__db_cursor.execute(
                '''SELECT name, start_time, end_time FROM reservations
                WHERE date(start_time) BETWEEN ? AND ? ORDER BY start_time''',
                (start_date_obj.date(), end_date_obj.date()))
            rows = self.__db_cursor.fetchall()
            reservations = {}

            # add reservations to dictionary
            for row in rows:
                row_start_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
                row_end_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
                date_str = row_start_time.strftime('%d.%m.%Y')

                if date_str not in reservations:
                    reservations[date_str] = []

                reservations[date_str].append({
                    "name": row[0],
                    "start_time": row_start_time.strftime('%H:%M'),
                    "end_time": row_end_time.strftime('%H:%M')
                })

            # add empty reservations for missing dates
            delta = end_date_obj.date() - start_date_obj.date()
            for i in range(delta.days + 1):
                empty_date = (start_date_obj + timedelta(days=i)).strftime('%d.%m.%Y')
                if empty_date not in reservations:
                    reservations[empty_date] = []

            # sort reservations by start time
            reservations = dict(sorted(reservations.items(), key=lambda x: datetime.strptime(x[0], '%d.%m.%Y')))

            # save reservations to file in chosen format
            if file_format == "csv":
                with open(file_name, "w", newline="") as file:
                    writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(["name", "start_time", "end_time"])

                    for empty_date, date_reservations in reservations.items():
                        for reservation_courts in date_reservations:
                            start_time = datetime.strptime(empty_date + " " + reservation_courts["start_time"],
                                                           '%d.%m.%Y %H:%M').strftime('%d.%m.%Y %H:%M')\
                                                            .replace(",", ", ")
                            end_time = datetime.strptime(empty_date + " " + reservation_courts["end_time"],
                                                         '%d.%m.%Y %H:%M').strftime(
                                '%d.%m.%Y %H:%M').replace(",", ", ")
                            writer.writerow([reservation_courts["name"], start_time, end_time])

            elif file_format == "json":
                with open(file_name, "w") as file:
                    json.dump(reservations, file, indent=4, default=str)

            print(f"Schedule saved to {file_name} in {file_format} format.")

        except ValueError as e:
            print(f"Error: {str(e)}. Please try again.")

    def start_program(self):
        while True:
            self.show_menu()
            switch = input("Enter a number: ")
            if switch == "1":
                self.reservation()
            elif switch == "2":
                self.cancel_reservation()
            elif switch == "3":
                self.print_schedule()
            elif switch == "4":
                self.save_to_file()
            elif switch == "5":
                self.__db_conn.close()
                break
            else:
                print("Invalid option. Try again")
                continue
            print()


reservation = ReservationSystem()
reservation.start_program()
