# -*- coding: utf-8 -*-
"""Email_Bot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_1FdAF0yfT4UMQzjhMJd5jMlTJnhT2PD
"""

!pip install --upgrade gspread gspread_dataframe oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime
import pytz
import time
import re

# 1. Connect to Google Sheets
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("email_sender_key.json.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Emails").sheet1
    print("Google Sheet connected successfully.")
except FileNotFoundError:
    print("Error: Service account JSON file not found.")
    raise
except Exception as e:
    print(f"Error connecting to Google Sheet: {e}")
    raise

# 2. Email Credentials
sender_email = "youremail@gmail.com"
app_password = "app_password"
admin_email = sender_email  # Admin receives notifications

# 3. Read the sheet rows
try:
    rows = sheet.get_all_records()
    if not rows:
        print("The sheet is empty!")
except Exception as e:
    print(f"Failed to read data from the sheet: {e}")
    raise

failed_emails = []

# 4. Loop through each row with validation
for row in rows:
    try:
        name = row.get('Name', '').strip()
        email = row.get('Email', '').strip()
        role = row.get('Group', '').strip()
        send_time_str = row.get('Send Time (IST)', '').strip()
        message_text = row.get('Message', '').strip()
        subject = row.get('Subject', '').strip()

        if not name or not email or not role or not send_time_str or not message_text:
            print(f"Skipping row with missing data: {row}")
            failed_emails.append((name, email, role, "Missing data"))
            continue

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            print(f"Invalid email format for {name}: {email}")
            failed_emails.append((name, email, role, "Invalid email format"))
            continue

        try:
            send_time = datetime.strptime(send_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Invalid time format for {name}: '{send_time_str}'. Expected format: YYYY-MM-DD HH:MM:SS")
            failed_emails.append((name, email, role, "Invalid time format"))
            continue

        local_tz = pytz.timezone("Asia/Kolkata")
        send_time_local = local_tz.localize(send_time)
        send_time_utc = send_time_local.astimezone(pytz.utc)

        print(f"{name}'s email scheduled at (IST): {send_time_local.strftime('%Y-%m-%d %H:%M:%S')} | (UTC): {send_time_utc.strftime('%Y-%m-%d %H:%M:%S')}")

        while datetime.now(pytz.utc) < send_time_utc:
            print(f"Waiting to send to {name}... Current UTC: {datetime.now(pytz.utc).strftime('%H:%M:%S')}")
            time.sleep(10)

        # Compose the email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = email
        message["Subject"] = subject or f"Automated Email for {role}"
        body = f"Dear {name},\n\n{message_text}\n\nRegards,\nYour Company"
        message.attach(MIMEText(body, "plain"))

        # Send the email
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, app_password)
                result = server.sendmail(sender_email, email, message.as_string())

                if result:  # If sendmail doesn't return an empty dict, sending failed
                    print(f"Failed to send email to {name} ({email}) without error.")
                    failed_emails.append((name, email, role, "Unknown failure"))
                else:
                    print(f"Email sent to {name} ({role}) at {email}")
        except smtplib.SMTPAuthenticationError:
            print("Authentication failed. Please check your sender email or app password.")
            break
        except smtplib.SMTPException as smtp_error:
            print(f"SMTP error while sending to {email}: {smtp_error}")
            failed_emails.append((name, email, role, f"SMTP error: {smtp_error}"))
        except Exception as e:
            print(f"Unexpected error while sending to {email}: {e}")
            failed_emails.append((name, email, role, f"Unexpected error: {e}"))

    except Exception as outer_error:
        print(f"Unknown error in row {row}: {outer_error}")
        failed_emails.append((name, email, role, f"Outer error: {outer_error}"))

# 5. Admin notification for failed emails
if failed_emails:
    try:
        admin_message = MIMEMultipart()
        admin_message["From"] = sender_email
        admin_message["To"] = admin_email
        admin_message["Subject"] = "Email Sending Failure Report"

        body_lines = ["The following emails failed to send:\n"]
        for name, email, role, reason in failed_emails:
            body_lines.append(f"- {name} ({role}) at {email}: {reason}")
        admin_body = "\n".join(body_lines)

        admin_message.attach(MIMEText(admin_body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, admin_email, admin_message.as_string())
            print("\nFailure report sent to admin.")

    except Exception as admin_err:
        print(f"Failed to send failure report to admin: {admin_err}")
else:
    print("\nAll emails sent successfully.")

