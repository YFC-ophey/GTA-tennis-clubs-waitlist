#!/usr/bin/env python3
"""
Email Agent for Tennis Club Outreach
Sends professional emails to clubs requesting missing information
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmailAgent:
    def __init__(self):
        """Initialize email agent with credentials from environment"""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.sender_name = os.getenv('SENDER_NAME', 'Tennis Club Research')

        if not self.sender_email or not self.sender_password:
            raise ValueError(
                "Email credentials not configured. "
                "Please set SENDER_EMAIL and SENDER_PASSWORD in .env file"
            )

    def generate_email(self, club_data: Dict, template: str = None) -> Tuple[str, str]:
        """
        Generate email subject and body for a club

        Args:
            club_data: Dictionary containing club information
            template: Custom email template (optional)

        Returns:
            Tuple of (subject, body)
        """
        club_name = club_data.get('Club Name', 'Tennis Club')

        # Default subject
        subject = f"Inquiry About {club_name} Membership Information"

        # Use custom template or default
        if template:
            body = template.replace('{club_name}', club_name)
        else:
            body = f"""Dear {club_name} Team,

I hope this message finds you well. I am currently researching tennis clubs in the Greater Toronto Area and came across your organization.

I would greatly appreciate if you could provide some information about your club:

• Current membership status (open/waitlist)
• Waitlist length (if applicable)
• Court facilities and availability
• Any other relevant details about joining

Thank you for your time and assistance!

Best regards,
{self.sender_name}"""

        return subject, body

    def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """
        Send an email

        Args:
            recipient_email: Email address to send to
            subject: Email subject
            body: Email body text

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"✓ Email sent to {recipient_email}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email to {recipient_email}: {str(e)}")
            return False

    def send_bulk_emails(self, clubs_data: list, template: str = None, dry_run: bool = True):
        """
        Send emails to multiple clubs

        Args:
            clubs_data: List of club data dictionaries
            template: Custom email template
            dry_run: If True, only print what would be sent
        """
        sent_count = 0
        failed_count = 0

        for club in clubs_data:
            email = club.get('Email')

            # Skip if no email
            if not email or email == 'N/A':
                continue

            # Skip if we already have complete data
            if (club.get('Waitlist Length') != 'N/A' and
                club.get('Membership Status') != 'N/A'):
                continue

            subject, body = self.generate_email(club, template)

            if dry_run:
                print(f"\n--- DRY RUN: Would send to {club['Club Name']} ({email}) ---")
                print(f"Subject: {subject}")
                print(f"Body:\n{body}\n")
                sent_count += 1
            else:
                if self.send_email(email, subject, body):
                    sent_count += 1
                else:
                    failed_count += 1

        print(f"\n{'DRY RUN ' if dry_run else ''}Summary:")
        print(f"  Sent: {sent_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Total: {sent_count + failed_count}")


if __name__ == '__main__':
    # Test the email agent
    try:
        agent = EmailAgent()
        print("Email agent initialized successfully!")
        print(f"Sender: {agent.sender_email}")

        # Test email generation
        test_club = {
            'Club Name': 'Test Tennis Club',
            'Email': 'test@example.com',
            'Waitlist Length': 'N/A',
            'Membership Status': 'N/A'
        }

        subject, body = agent.generate_email(test_club)
        print(f"\nTest Email:")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease create a .env file with:")
        print("  SENDER_EMAIL=your-email@gmail.com")
        print("  SENDER_PASSWORD=your-app-password")
