# In views.py
from flask import Blueprint, render_template, request, session as flask_session, redirect, url_for, jsonify
from .api_utils import search_member_by_reg_num
# from flask import Flask, request, , render_template, session as flask_session, redirect, url_for
from .config import SECRET_KEY
from .models import Base, Member
from sqlalchemy import create_engine
from .api_utils import search_member_by_reg_num, search_member_by_last_name_api, get_api_token, send_api_payload
from .member_handlers import handle_member_record, Session
from .time_utils import sydney_time_now
import json
from NITC import create_app
from flask import current_app
from datetime import datetime
import pytz

main = Blueprint('main', __name__)

# Route for login page
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passcode = request.form.get('passcode')
        if passcode == '1325':
            flask_session['logged_in'] = True
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', message="Incorrect passcode"), 401
    return render_template('login.html')

@main.route('/', methods=['GET'])
def index():
    if 'logged_in' not in flask_session or not flask_session['logged_in']:
        return redirect(url_for('main.login'))
    return render_template('index.html')

@main.before_request
def require_login():
    if request.endpoint not in ['main.login', 'static'] and ('logged_in' not in flask_session or not flask_session['logged_in']):
        return redirect(url_for('main.login'))

@main.route('/search_member', methods=['GET'])
def search_person():
    registrationNumber = request.args.get('registrationNumber')
    LastName = request.args.get('LastName')
    if registrationNumber:
        member_data, _ = search_member_by_reg_num(registrationNumber)
        if member_data:
            return jsonify(member_data)
        else:
            return jsonify({"status": "error", "message": "Member not found"}), 404
    elif LastName:
        member_data, _ = search_member_by_last_name_api(LastName)
        if member_data:
            return jsonify(member_data)
        else:
            return jsonify({"status": "error", "message": "Member not found"}), 404
    else:
        return jsonify({"status": "error", "message": "Either registrationNumber or LastName must be provided"}), 400

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
        member_data, person_id = search_member_by_reg_num(registration_number)
        if not member_data:
            return jsonify({"status": "error", "message": "Member not found"}), 404
        
        # Check out the member and get the result
        result = handle_member_record(session, registration_number, sydney_time_now(), check_in=False)
        if result['status'] == 'success':
            # Fetch the member record to get start_date and end_date
            member_record = session.query(Member).filter_by(member_number=registration_number).order_by(Member.id.desc()).first()
            if member_record and member_record.end_date:
                token = get_api_token()
                api_result = send_api_payload(person_id, member_record.start_date, member_record.end_date, tag_ids, token)
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