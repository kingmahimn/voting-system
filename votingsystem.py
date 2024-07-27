import firebase_admin
from firebase_admin import credentials, firestore
import threading
import time
import cmd
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import os
from datetime import datetime, timedelta
import schedule
from twilio.rest import Client
from colorama import init, Fore, Back, Style


os.environ["GRPC_VERBOSITY"] = "NONE"
# Initialize Firebase
cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com" # Input email you want to use for sending emails
SMTP_PASSWORD = "your-app-password"  # Use an app password, not your regular password

# Twilio configuration for SMS
TWILIO_ACCOUNT_SID = "your-account-sid"
TWILIO_AUTH_TOKEN = "your-auth-token"
TWILIO_PHONE_NUMBER = "your-twilio-phone-number"
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class VotingSystem(cmd.Cmd):
    intro = f"{Fore.CYAN}{Style.BRIGHT}Welcome to the Enhanced Voting System. Type 'help' for commands.{Style.RESET_ALL}"
    prompt = f"{Fore.GREEN}(voting) {Style.RESET_ALL}"

    def __init__(self):
        super().__init__()
        self.live_update_thread = None
        self.stop_live_update = threading.Event()
        self.voting_date = None
        self.reminder_thread = None

    def do_import_voters(self, arg):
        """Import voters from an Excel file: import_voters <file_path>"""
        file_path = arg.strip()
        if not os.path.exists(file_path):
            print(f"{Fore.RED}File not found: {file_path}{Style.RESET_ALL}")
            return

        try:
            df = pd.read_excel(file_path)
            required_columns = ['First Name', 'Last Name', 'Street#', 'Street Name', 'City', 
                                'Postal Code', 'Phone', 'Email']
            if not all(col in df.columns for col in required_columns):
                print(f"{Fore.RED}Excel file is missing required columns.{Style.RESET_ALL}")
                return

            for _, row in df.iterrows():
                voter_data = {
                    'first_name': row['First Name'],
                    'last_name': row['Last Name'],
                    'street_number': row['Street#'],
                    'street_name': row['Street Name'],
                    'city': row['City'],
                    'postal_code': row['Postal Code'],
                    'phone': row['Phone'],
                    'email': row['Email'],
                    'has_voted': False,
                    'vote_choice': None
                }
                db.collection('voters').document(row['Email']).set(voter_data)

            print(f"{Fore.GREEN}Successfully imported {len(df)} voters.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error importing voters: {str(e)}{Style.RESET_ALL}")

    def do_record_vote(self, arg):
        """Record a vote: record_vote <email> <choice>"""
        args = arg.split()
        if len(args) == 2:
            email, choice = args
            voter_ref = db.collection('voters').document(email)
            voter = voter_ref.get()
            if voter.exists:
                voter_data = voter.to_dict()
                voter_ref.update({
                    'has_voted': True,
                    'vote_choice': choice
                })
                print(f"{Fore.GREEN}Vote recorded for {email}: {choice}{Style.RESET_ALL}")
                self.send_vote_confirmation(voter_data, choice)
            else:
                print(f"{Fore.RED}Voter {email} not found.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Please provide both email and vote choice.{Style.RESET_ALL}")
    
    def send_vote_confirmation(self, voter, choice):
        self.send_confirmation_email(voter, choice)
        self.send_confirmation_sms(voter, choice)

    def send_confirmation_email(self, voter, choice):
        subject = "Voting Confirmation"
        body = f"Dear {voter['first_name']} {voter['last_name']},\n\n" \
               f"This email confirms that your vote for {choice} has been recorded.\n\n" \
               f"Thank you for participating in the voting process.\n\n" \
               f"Best regards,\nVoting System Team"

        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = voter['email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            print(f"{Fore.CYAN}Confirmation email sent to {voter['email']}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error sending email to {voter['email']}: {str(e)}{Style.RESET_ALL}")

    def send_confirmation_sms(self, voter, choice):
        message = f"Voting Confirmation: Dear {voter['first_name']}, your vote for {choice} has been recorded. Thank you for participating."

        try:
            twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=voter['phone']
            )
            print(f"{Fore.CYAN}Confirmation SMS sent to {voter['phone']}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error sending SMS to {voter['phone']}: {str(e)}{Style.RESET_ALL}")

    def do_get_voter_status(self, arg):
        """Get voter status: get_voter_status <email>"""
        email = arg.strip()
        if email:
            voter = db.collection('voters').document(email).get()
            if voter.exists:
                data = voter.to_dict()
                print(f"{Fore.CYAN}Voter Information:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Name: {Style.BRIGHT}{data['first_name']} {data['last_name']}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Email: {Style.BRIGHT}{email}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Address: {Style.BRIGHT}{data['street_number']} {data['street_name']}, {data['city']}, {data['postal_code']}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Phone: {Style.BRIGHT}{data['phone']}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Has voted: {Style.BRIGHT}{Fore.GREEN if data['has_voted'] else Fore.RED}{data['has_voted']}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Vote choice: {Style.BRIGHT}{data['vote_choice'] if data['vote_choice'] else 'N/A'}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Voter {email} not found.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Please provide an email address.{Style.RESET_ALL}")

    def do_live_voting(self, arg):
        """Start live voting updates"""
        if self.live_update_thread and self.live_update_thread.is_alive():
            print(f"{Fore.YELLOW}Live voting is already running.{Style.RESET_ALL}")
            return

        self.stop_live_update.clear()
        self.live_update_thread = threading.Thread(target=self.live_voting_update)
        self.live_update_thread.start()
        print(f"{Fore.GREEN}Live voting updates started. Press Enter to stop.{Style.RESET_ALL}")

    def live_voting_update(self):
        while not self.stop_live_update.is_set():
            votes = db.collection('voters').where('has_voted', '==', True).get()
            vote_count = len(votes)
            print(f"\r{Fore.CYAN}Current vote count: {Style.BRIGHT}{vote_count}{Style.RESET_ALL}", end="", flush=True)
            time.sleep(1)

    def do_stop_live_voting(self, arg):
        """Stop live voting updates"""
        if self.live_update_thread and self.live_update_thread.is_alive():
            self.stop_live_update.set()
            self.live_update_thread.join()
            print(f"\n{Fore.GREEN}Live voting updates stopped.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Live voting is not currently running.{Style.RESET_ALL}")
    
    def do_set_voting_date(self, arg):
        """Set the voting date and schedule reminders: set_voting_date YYYY-MM-DD"""
        try:
            self.voting_date = datetime.strptime(arg.strip(), "%Y-%m-%d")
            self.schedule_reminders()
            print(f"{Fore.GREEN}Voting date set to {self.voting_date.date()}. Reminders scheduled.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid date format. Please use YYYY-MM-DD.{Style.RESET_ALL}")

    def schedule_reminders(self):
        if not self.voting_date:
            print("Voting date not set. Use set_voting_date command first.")
            return

        # Schedule immediate reminder
        schedule.every(1).seconds.do(self.send_reminders, reminder_type="Initial reminder")

        # Schedule reminder 3 days before
        three_days_before = self.voting_date - timedelta(days=3)
        schedule.every().day.at("09:00").do(self.send_reminders, reminder_type="3-day reminder").tag(f"3day_{self.voting_date.date()}")

        # Schedule reminder on voting day
        schedule.every().day.at("07:00").do(self.send_reminders, reminder_type="Voting day reminder").tag(f"votingday_{self.voting_date.date()}")

        # Start the reminder thread
        self.reminder_thread = threading.Thread(target=self.run_reminders)
        self.reminder_thread.start()

    def run_reminders(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_reminders(self, reminder_type):
        voters = db.collection('voters').get()
        for voter in voters:
            voter_data = voter.to_dict()
            if not voter_data['has_voted']:
                self.send_reminder_email(voter_data, reminder_type)
                self.send_reminder_sms(voter_data, reminder_type)

        if reminder_type == "Voting day reminder":
            schedule.clear(f"votingday_{self.voting_date.date()}")
        elif reminder_type == "3-day reminder":
            schedule.clear(f"3day_{self.voting_date.date()}")
        elif reminder_type == "Initial reminder":
            return schedule.CancelJob

        print(f"{Fore.GREEN}{reminder_type} sent to all non-voted voters.{Style.RESET_ALL}")

    def send_reminder_email(self, voter, reminder_type):
        subject = f"Voting Reminder: {reminder_type}"
        body = f"Dear {voter['first_name']} {voter['last_name']},\n\n" \
               f"This is a {reminder_type} for the upcoming voting event on {self.voting_date.date()}.\n\n" \
               f"Your participation is important. Please remember to cast your vote.\n\n" \
               f"Voting Location: [Insert Voting Location Here]\n" \
               f"Voting Time: [Insert Voting Time Here]\n\n" \
               f"Don't forget to bring a valid ID.\n\n" \
               f"If you have any questions, please don't hesitate to contact us.\n\n" \
               f"Thank you for your participation in this important process.\n\n" \
               f"Best regards,\nVoting System Team"

        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = voter['email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            print(f"{Fore.CYAN}Reminder email sent to {voter['email']}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error sending email to {voter['email']}: {str(e)}{Style.RESET_ALL}")

    def send_reminder_sms(self, voter, reminder_type):
        message = f"Voting {reminder_type}: Dear {voter['first_name']}, remember to vote on {self.voting_date.date()}. " \
                  f"Your participation matters!"

        try:
            twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=voter['phone']
            )
            print(f"{Fore.CYAN}Reminder SMS sent to {voter['phone']}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error sending SMS to {voter['phone']}: {str(e)}{Style.RESET_ALL}")


    def do_list_voters(self, arg):
        """List all voters"""
        voters = db.collection('voters').get()
        print(f"{Fore.CYAN}Voter List:{Style.RESET_ALL}")
        for voter in voters:
            data = voter.to_dict()
            vote_status = f"{Fore.GREEN}Yes{Style.RESET_ALL}" if data['has_voted'] else f"{Fore.RED}No{Style.RESET_ALL}"
            print(f"{Fore.WHITE}{data['first_name']} {data['last_name']} - {data['email']}, Voted: {vote_status}")

    def do_exit(self, arg):
        """Exit the program"""
        print(f"{Fore.YELLOW}Thank you for using the Enhanced Voting System.{Style.RESET_ALL}")
        self.stop_live_update.set()
        if self.live_update_thread:
            self.live_update_thread.join()
        return True

if __name__ == '__main__':
    VotingSystem().cmdloop()