"""
Email Agent for Tennis Club Outreach
Sends emails to clubs with missing data
"""

import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EmailAgent:
    def __init__(self):
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))

        if not self.email_address or not self.email_password:
            logger.warning("Email credentials not found in .env file. Email sending will be disabled.")

    def generate_email_template(self, club_name: str, missing_fields: List[str]) -> str:
        """Generate personalized email template"""

        template = f"""
Dear {club_name} Team,

I hope this message finds you well. I am currently compiling a comprehensive database of tennis clubs in the Greater Toronto Area to help tennis enthusiasts find the right club for their needs.

I visited your website but was unable to find some information about your club. Would you be able to provide the following details?

Missing Information:
"""

        for field in missing_fields:
            template += f"  - {field}\n"

        template += """
Additionally, if you could share:
  - Current membership status (Open/Waitlist/Closed)
  - Waitlist length (if applicable)
  - Number of tennis courts
  - Court surface type
  - Operating season

I would greatly appreciate your help in making this database as accurate and helpful as possible for the tennis community.

Thank you for your time, and I look forward to hearing from you.

Best regards,
[Your Name]
[Your Contact Information]
"""

        return template

    def identify_clubs_with_missing_data(self, scraped_data_file: str,
                                        threshold: int = 3) -> List[Dict]:
        """
        Identify clubs that have significant missing data

        Args:
            scraped_data_file: Path to JSON file with scraped data
            threshold: Minimum number of N/A fields to trigger email
        """
        with open(scraped_data_file, 'r', encoding='utf-8') as f:
            clubs = json.load(f)

        clubs_needing_outreach = []

        for club in clubs:
            # Fields to check for completeness
            important_fields = [
                'Location', 'Email', 'Club Type', 'Membership Status',
                'Current Waitlist Length', 'Number of Courts',
                'Court Surface', 'Operating Season'
            ]

            missing_fields = [field for field in important_fields
                            if club.get(field) == 'N/A']

            # If email is missing or we have many N/A fields, add to outreach list
            if club.get('Email') == 'N/A' or len(missing_fields) >= threshold:
                clubs_needing_outreach.append({
                    'club': club,
                    'missing_fields': missing_fields
                })

        logger.info(f"Found {len(clubs_needing_outreach)} clubs needing email outreach")
        return clubs_needing_outreach

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email"""

        if not self.email_address or not self.email_password:
            logger.error("Email credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)

            # Send email
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_outreach_emails(self, scraped_data_file: str,
                           output_log: str = "results/email_log.json",
                           dry_run: bool = True):
        """
        Send outreach emails to clubs with missing data

        Args:
            scraped_data_file: Path to JSON file with scraped data
            output_log: Path to save email log
            dry_run: If True, only generate emails without sending
        """

        clubs_needing_outreach = self.identify_clubs_with_missing_data(scraped_data_file)

        email_log = []

        for item in clubs_needing_outreach:
            club = item['club']
            missing_fields = item['missing_fields']
            club_name = club['Club Name']

            # Generate email
            email_body = self.generate_email_template(club_name, missing_fields)

            email_record = {
                'club_name': club_name,
                'email': club.get('Email', 'N/A'),
                'missing_fields': missing_fields,
                'email_body': email_body,
                'sent': False,
                'timestamp': None
            }

            if dry_run:
                logger.info(f"[DRY RUN] Would send email to {club_name}")
                print(f"\n{'='*60}")
                print(f"Email for: {club_name}")
                print(f"To: {club.get('Email', 'MISSING EMAIL')}")
                print(f"{'='*60}")
                print(email_body)
                print(f"{'='*60}\n")

            else:
                # Only send if we have an email address
                if club.get('Email') != 'N/A':
                    subject = f"Information Request - {club_name} Tennis Club Database"
                    success = self.send_email(club['Email'], subject, email_body)

                    if success:
                        email_record['sent'] = True
                        email_record['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')

                    # Be polite - wait between emails
                    time.sleep(5)
                else:
                    logger.warning(f"No email address for {club_name} - skipping")

            email_log.append(email_record)

        # Save email log
        with open(output_log, 'w', encoding='utf-8') as f:
            json.dump(email_log, f, indent=2, ensure_ascii=False)

        logger.info(f"Email outreach complete. Log saved to {output_log}")

        # Summary
        total = len(email_log)
        with_email = sum(1 for e in email_log if e['email'] != 'N/A')
        sent = sum(1 for e in email_log if e['sent'])

        print(f"\n{'='*60}")
        print(f"Email Outreach Summary")
        print(f"{'='*60}")
        print(f"Total clubs needing outreach: {total}")
        print(f"Clubs with email addresses: {with_email}")
        print(f"Emails sent: {sent}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Test email generation (dry run)
    agent = EmailAgent()

    # Create dummy data for testing
    test_data = [
        {
            "Club Name": "Test Tennis Club",
            "Location": "Toronto",
            "Email": "N/A",
            "Club Type": "N/A",
            "Membership Status": "N/A",
            "Current Waitlist Length": "N/A",
            "Number of Courts": "N/A",
            "Court Surface": "N/A",
            "Operating Season": "N/A",
            "Website URL": "http://example.com",
            "Scrape Status": "Success"
        }
    ]

    # Save test data
    with open("results/test_scraped_data.json", 'w') as f:
        json.dump(test_data, f)

    # Run dry run
    agent.send_outreach_emails("results/test_scraped_data.json", dry_run=True)
