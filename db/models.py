from database import db
from datetime import datetime, date

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    session = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'date', 'session', name='_student_date_session_uc'),)