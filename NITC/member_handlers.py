from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Member, Base
from .config import DATABASE_URL
from .time_utils import sydney_time_now
import pytz

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def handle_member_record(session, registration_number, current_time, check_in=True):
    member_record = session.query(Member).filter_by(
        member_number=registration_number).order_by(Member.id.desc()).first()
    if check_in:
        if member_record is None or member_record.end_date is not None:
            member_record = Member(
                member_number=registration_number, start_date=current_time, end_date=None)
            session.add(member_record)
            session.commit()
            return {"status": "success", "message": "Check-in time captured"}
        else:
            return {"status": "error", "message": "Member is already checked in"}
    else:
        if member_record and member_record.end_date is None:
            member_record.end_date = current_time
            session.commit()
            return {"status": "success", "message": "Check-out time captured"}
        else:
            return {"status": "error", "message": "Member is not checked in or already checked out"}
