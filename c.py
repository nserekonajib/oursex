from flask import Flask, jsonify
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pytz
import json
import os

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

# --- Config ---
email_sender = 'nserekonajib3@gmail.com'
email_password = 'gvai uawu evwn hqfr'  # USE ENV IN PROD!
recipients = ['nclenza@gmail.com', 'zayyanclenza@gmail.com']
wife_name = "Mrs. Nsereko Nabirah"
your_name = "Nsereko Najib"
cycle_length = 28
period_length = 5

# --- Timezone ---
uganda_tz = pytz.timezone("Africa/Kampala")

# --- File-based Cycle Start Persistence ---
CYCLE_FILE = 'cycle_data.json'

def load_cycle_data():
    if os.path.exists(CYCLE_FILE):
        with open(CYCLE_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_period_start"])
    else:
        # Default start date if file not found
        initial_start = datetime(2025, 7, 22, tzinfo=uganda_tz)
        save_cycle_data(initial_start)
        return initial_start

def save_cycle_data(new_start_date):
    with open(CYCLE_FILE, 'w') as f:
        json.dump({"last_period_start": new_start_date.isoformat()}, f)

# --- Logic to Auto-Adjust Start Date ---
def get_current_period_start():
    last_start = load_cycle_data()
    today = datetime.now(uganda_tz)

    while (today - last_start).days >= cycle_length:
        last_start += timedelta(days=cycle_length)
        save_cycle_data(last_start)

    return last_start

# --- Cycle Info Logic ---
def get_cycle_info():
    today = datetime.now(uganda_tz)
    current_start = get_current_period_start()

    days_since_period = (today - current_start).days
    day_in_cycle = days_since_period % cycle_length
    days_until_next = cycle_length - day_in_cycle

    ovulation_day = 14
    fertile_window = range(ovulation_day - 5, ovulation_day + 2)
    is_period_day = day_in_cycle < period_length
    is_fertile_day = day_in_cycle in fertile_window

    if is_period_day:
        status = "Menstruation (Period Ongoing)"
        note = "We are not having sex today, my soulmate."
    elif is_fertile_day:
        status = "Fertile Day 🌸"
        note = "My love, today we can have a baby. Let's make special love."
    else:
        status = "Safe Day ✅"
        note = "Low chance of pregnancy, but we’re still going to have our special love."

    return {
        "today": today.strftime("%A, %d %B %Y"),
        "day_in_cycle": day_in_cycle + 1,
        "days_until_next": days_until_next,
        "status": status,
        "note": note
    }

# --- Email Body ---
def create_email_body(info):
    return f"""
    <html>
    <body style="font-family: Arial; line-height: 1.6;">
        <h2>Good Morning {wife_name}, 🌞</h2>
        <p>Here's your menstrual cycle update for <b>{info['today']}</b>:</p>
        <ul>
            <li><b>Day in Cycle:</b> {info['day_in_cycle']} of {cycle_length}</li>
            <li><b>Status:</b> {info['status']}</li>
            <li><b>Message:</b> {info['note']}</li>
            <li><b>Days Remaining to Next Period:</b> {info['days_until_next']}</li>
        </ul>
        <p style="margin-top: 40px;">With all my love ❤️,<br><b>Your loving husband,<br>{your_name}</b></p>
    </body>
    </html>
    """

# --- Send Email ---
def send_email():
    info = get_cycle_info()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "💌 Daily Cycle Update"
    msg["From"] = email_sender
    msg["To"] = ", ".join(recipients)

    html = create_email_body(info)
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_sender, email_password)
            server.sendmail(email_sender, recipients, msg.as_string())
        return True, info
    except Exception as e:
        return False, str(e)

# --- Flask Route ---
@app.route('/send-cycle-email', methods=['GET'])
def trigger_email():
    success, result = send_email()
    if success:
        return jsonify({"status": "success", "message": "Email sent", "data": result})
    else:
        return jsonify({"status": "error", "message": f"Failed to send email: {result}"}), 500

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)
