from flask import Flask, request, jsonify, render_template, session as flask_session, redirect, url_for
from .config import SECRET_KEY
from .models import Base, Member
from sqlalchemy import create_engine
from .api_utils import search_member_by_reg_num, search_member_by_last_name_api, get_api_token, send_api_payload
from .member_handlers import handle_member_record, Session
from .time_utils import sydney_time_now
from dev import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
app.secret_key = SECRET_KEY

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)



if __name__ == '__main__':
    app
