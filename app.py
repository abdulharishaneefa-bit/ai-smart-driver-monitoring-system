from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from models import db, Driver, Session, Event
from detector import start_detection

import smtplib
from email.mime.text import MIMEText


# ---------------- EMAIL SETTINGS ----------------
# Change these 3 values with your real details
SENDER_EMAIL = "abdulharishaneefa@gmail.com"
APP_PASSWORD = "pxusgqhomuzwykee"
RECEIVER_EMAIL = "abdulharishaneefa@gmail.com"


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


def send_email_alert(driver_name, vehicle_number, drowsy_count, phone_count):
    subject = "Driver Safety Alert"

    body = f"""
Driver Safety Alert!

Driver Name: {driver_name}
Vehicle Number: {vehicle_number}

Drowsy Events Detected: {drowsy_count}
Phone Usage Events Detected: {phone_count}

Please take necessary action immediately.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email alert sent successfully.")
    except Exception as e:
        print("Email sending failed:", e)


@app.route("/")
def index():
    total_drivers = Driver.query.count()
    total_sessions = Session.query.count()
    total_events = Event.query.count()

    return render_template(
        "index.html",
        total_drivers=total_drivers,
        total_sessions=total_sessions,
        total_events=total_events
    )


@app.route("/add_driver", methods=["GET", "POST"])
def add_driver():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        vehicle_number = request.form["vehicle_number"]

        new_driver = Driver(
            name=name,
            age=int(age),
            vehicle_number=vehicle_number
        )

        db.session.add(new_driver)
        db.session.commit()

        return redirect(url_for("drivers"))

    return render_template("add_driver.html")


@app.route("/drivers")
def drivers():
    all_drivers = Driver.query.order_by(Driver.created_at.desc()).all()
    return render_template("drivers.html", drivers=all_drivers)


@app.route("/driver/<int:driver_id>")
def driver_dashboard(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    sessions = Session.query.filter_by(driver_id=driver.id).order_by(Session.start_time.desc()).all()

    return render_template("dashboard.html", driver=driver, sessions=sessions)


@app.route("/start_detection/<int:driver_id>")
def start_detection_route(driver_id):
    driver = Driver.query.get_or_404(driver_id)

    new_session = Session(
        driver_id=driver.id,
        start_time=datetime.utcnow(),
        total_drowsy_events=0,
        total_phone_events=0
    )

    db.session.add(new_session)
    db.session.commit()

    result = start_detection()

    drowsy_count = result.get("total_drowsy_events", 0)
    phone_count = result.get("total_phone_events", 0)

    new_session.end_time = datetime.utcnow()
    new_session.total_drowsy_events = drowsy_count
    new_session.total_phone_events = phone_count

    db.session.commit()

    for _ in range(drowsy_count):
        event = Event(
            session_id=new_session.id,
            event_type="drowsy",
            status="drowsy"
        )
        db.session.add(event)

    for _ in range(phone_count):
        event = Event(
            session_id=new_session.id,
            event_type="phone_usage",
            status="using_phone"
        )
        db.session.add(event)

    db.session.commit()

    print("Drowsy:", drowsy_count, "Phone:", phone_count)

    if drowsy_count > 0 or phone_count > 0:
        print("Triggering email alert...")
        send_email_alert(
            driver.name,
            driver.vehicle_number,
            drowsy_count,
            phone_count
        )

    return redirect(url_for("driver_dashboard", driver_id=driver_id))


@app.route("/end_session/<int:session_id>", methods=["POST"])
def end_session(session_id):
    session = Session.query.get_or_404(session_id)

    if session.end_time is None:
        session.end_time = datetime.utcnow()
        db.session.commit()

    return redirect(url_for("driver_dashboard", driver_id=session.driver_id))


@app.route("/reports")
def reports():
    drivers = Driver.query.all()

    total_drowsy_all = 0
    total_phone_all = 0

    for driver in drivers:
        sessions = Session.query.filter_by(driver_id=driver.id).all()

        total_drowsy_all += sum(s.total_drowsy_events for s in sessions)
        total_phone_all += sum(s.total_phone_events for s in sessions)

    total_events = total_drowsy_all + total_phone_all
    max_value = max(total_drowsy_all, total_phone_all, 1)

    return render_template(
        "reports.html",
        total_drowsy_all=total_drowsy_all,
        total_phone_all=total_phone_all,
        total_events=total_events,
        max_value=max_value
    )


if __name__ == "__main__":
    app.run(debug=True)