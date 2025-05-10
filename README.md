# Automated Email Sender

A Python script to schedule and send emails automatically using Gmail and Google Sheets.

##Features
- Reads recipient info and message from a Google Sheet
- Schedules emails in IST
- Sends admin failure reports

##Setup
- Create a Google service account key (JSON)
- Replace dummy `sample_key.json` with your own
- Enable Gmail API access

##Technologies Used
- Python
- Google Sheets API (gspread)
- Gmail SMTP
- Colab / Chromebook compatible

##Credentials
Do not share real keys or passwords. Use `.env` or upload dummy files like `sample_key.json`.
