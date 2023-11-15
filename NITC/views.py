# In views.py
from flask import Flask, Blueprint, render_template, request, session as flask_session, redirect, url_for, jsonify, flash
from .api_utils import search_member_by_reg_num
# from flask import Flask, request, , render_template, session as flask_session, redirect, url_for
from .config import SECRET_KEY, USERNAME, BEACON_URL
from .models import Base, Member
from sqlalchemy import create_engine
from .api_utils import search_member_by_reg_num, search_member_by_last_name, get_token, send_api_payload
from .member_handlers import handle_member_record, Session
from .time_utils import sydney_time_now
import json
from NITC import create_app
from flask import current_app
from datetime import datetime
import pytz
import pandas as pd

main = Blueprint('main', __name__)

# Route for login page
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passcode = request.form.get('passcode')
        if passcode == '1325':
            flask_session['logged_in'] = True
            flask_session['beacon_token'] = get_token()
            flask_session['username'] = USERNAME
            flask_session['trainbeacon'] = BEACON_URL.find("train")>=0
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error="Incorrect passcode"), 401
    return render_template('login.html')
    # if request.method == 'POST':
    #     username = request.form.get('username')
    #     password = request.form.get('password')
    #     flask_session['beacon_token'] = get_token(username, password)
    #     if flask_session['beacon_token'] is None:
    #         return render_template('login_beacon.html', error="Incorrect username or password"), 401
    #     flask_session['username'] = username
    #     flask_session['trainbeacon'] = BEACON_URL.find("train")>=0
    #     flask_session['logged_in'] = True
    #     return redirect(url_for('main.index'))
    # return render_template('login_beacon.html')

# Route for logout page
@main.route('/logout', methods=['GET', 'POST'])
def logout():
    flask_session['logged_in'] = False
    flask_session.pop('username', None)
    flask_session.pop('logged_in', None)
    flask_session.pop('trainbeacon', None)
    flask_session.pop('beacon_url', None)
    return render_template('logout.html', message="You have successfully logged out"), 200

@main.route('/', methods=['GET'])
def index():
    if 'logged_in' not in flask_session or not flask_session['logged_in']:
        return redirect(url_for('main.login'))
    return render_template('index.html')

@main.before_request
def require_login():
    if request.endpoint not in ['main.login', 'static'] and ('logged_in' not in flask_session or not flask_session['logged_in']):
        return redirect(url_for('main.login'))
    
@main.route('/check_in_status', methods=['GET'])
def check_in_status():
    registration_number = request.args.get('registrationNumber')
    session = Session()

    try:
        # Query the latest record for the member
        member_record = session.query(Member).filter_by(member_number=registration_number).order_by(Member.id.desc()).first()

        # Check if the member is currently checked in
        # This logic might depend on how you track the check-in and check-out times
        # For example, if the latest record has no end_date, it might mean the member is still checked in
        is_checked_in = member_record is not None and member_record.end_date is None

        return jsonify({"isCheckedIn": is_checked_in})
    except Exception as e:
        current_app.logger.error('Error checking in status', exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()
        

@main.route('/search_member', methods=['GET'])
def search_person():
    registrationNumber = request.args.get('registrationNumber')
    LastName = request.args.get('LastName')
    if registrationNumber:
        member_data, _ = search_member_by_reg_num(registrationNumber, flask_session['beacon_token'])
        if member_data:
            return jsonify(member_data)
        else:
            return jsonify({"status": "error", "message": "Member not found"}), 404
    elif LastName:
        member_data, _ = search_member_by_last_name(LastName, flask_session['beacon_token'])
        if member_data:
            return jsonify(member_data)
        else:
            return jsonify({"status": "error", "message": "Member not found"}), 404
    else:
        return jsonify({"status": "error", "message": "Either registrationNumber or LastName must be provided"}), 400
    
@main.route('/get_items_by_taggroupid')
def get_items_by_taggroupid():
    tag_group_id = request.args.get('tagGroupId', type=int)
    df = pd.read_csv('NITC/static/items.csv')
    filtered_df = df[df['tagGroupId'] == tag_group_id]  # Correct column name case

    data = filtered_df.to_dict(orient='records')
    return jsonify(data)

@main.route('/check_in', methods=['POST'])
def check_in():
    registration_number = request.form.get('registrationNumber')
    tag_ids_json = request.form.get('TagIds')
    tag_ids = json.loads(tag_ids_json) if tag_ids_json else []
    current_time = sydney_time_now()

 #   tag_ids_json = request.form.get('TagIds')
 #  tag_ids = json.loads(tag_ids_json) if tag_ids_json else []
    
    # Create a new session object
    session = Session()
    
    try:
        result = handle_member_record(session, registration_number, current_time, check_in=True)
    finally:
        # Close the session after you're done with it
        session.close()
    
    return jsonify(result)


# Route for check_out
@main.route('/check_out', methods=['POST'])
def check_out():
    registration_number = request.form.get('registrationNumber')
    tag_ids_json = request.form.get('TagIds')
    tag_ids = json.loads(tag_ids_json) if tag_ids_json else []
    
    session = Session()
    try:
        member_data, person_id = search_member_by_reg_num(registration_number, flask_session['beacon_token'])
        if not member_data:
            return jsonify({"status": "error", "message": "Member not found"}), 404
        
        # Check out the member and get the result
        result = handle_member_record(session, registration_number, sydney_time_now(), check_in=False)
        if result['status'] == 'success':
            # Fetch the member record to get start_date and end_date
            member_record = session.query(Member).filter_by(member_number=registration_number).order_by(Member.id.desc()).first()
            if member_record and member_record.end_date:
                api_result = send_api_payload(person_id, member_record.start_date, member_record.end_date, tag_ids, flask_session['beacon_token'])
                return jsonify(api_result)
            else:
                return jsonify({"status": "error", "message": "Member record not found or check-out not completed"}), 404
        else:
            # If there was an error checking out, return the error
            return jsonify(result)
    except Exception as e:
        current_app.logger.error('Error during check-out', exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()