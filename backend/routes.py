from flask import Blueprint, render_template, request, jsonify, redirect, url_for, Response
from database import db
from database.models import Student, AttendanceLog
import qrcode
import io
import base64
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    now = datetime.now()
    today = now.date()
    all_students = Student.query.all()
    todays_logs = AttendanceLog.query.filter_by(date=today).all()
    
    log_map = {}
    for log in todays_logs:
        if log.student_id not in log_map:
            log_map[log.student_id] = {}
        log_map[log.student_id][log.session] = True
        
    return render_template('index.html', students=all_students, log_map=log_map, today=today, now=now)

@main.route('/history')
def history():
    dates_obj = db.session.query(AttendanceLog.date).distinct().order_by(AttendanceLog.date.desc()).all()
    dates = [d[0] for d in dates_obj]
    
    selected_date_str = request.args.get('date')
    selected_date = None
    log_map = {}
    all_students = []
    
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        logs = AttendanceLog.query.filter_by(date=selected_date).all()
        all_students = Student.query.all()
        for log in logs:
            if log.student_id not in log_map:
                log_map[log.student_id] = {}
            log_map[log.student_id][log.session] = True

    return render_template('history.html', dates=dates, selected_date=selected_date, students=all_students, log_map=log_map)

@main.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        course = request.form.get('course')

        if Student.query.filter_by(student_id=student_id).first():
            return render_template('register.html', error="Student ID already exists!")

        new_student = Student(student_id=student_id, name=name, course=course)
        db.session.add(new_student)
        db.session.commit()

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(student_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return render_template('register.html', success="Student registered successfully!", qr_code=qr_code_base64, name=name)
    return render_template('register.html')

@main.route('/student/<int:id>/edit', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.course = request.form.get('course')
        db.session.commit()
        return redirect(url_for('main.students'))
    return render_template('edit.html', student=student)

@main.route('/student/<int:id>/delete', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    AttendanceLog.query.filter_by(student_id=student.student_id).delete()
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('main.students'))

@main.route('/student/<int:id>/qrcode')
def student_qrcode(id):
    student = Student.query.get_or_404(id)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(student.student_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return render_template('view_qrcode.html', student=student, qr_code=qr_code_base64)

@main.route('/scan')
def scan():
    return render_template('scan.html')

@main.route('/api/attend', methods=['POST'])
def attend():
    data = request.json
    student_id = data.get('student_id')
    if not student_id:
        return jsonify({'success': False, 'message': 'Invalid QR Code'})
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found in database'})

    now = datetime.now()
    if now.weekday() == 5:
        return jsonify({'success': False, 'message': "It's a Saturday"})
    elif now.weekday() == 6:
        return jsonify({'success': False, 'message': "It's a Sunday"})

    current_hour = now.hour
    session = None
    if 8 <= current_hour < 13:
        session = 'Morning'
    elif 13 <= current_hour < 18:
        session = 'Afternoon'
    else:
        return jsonify({'success': False, 'message': 'Class has Ended'})

    existing_log = AttendanceLog.query.filter_by(student_id=student_id, date=now.date(), session=session).first()
    if existing_log:
         return jsonify({'success': False, 'message': "Already check", 'already_checked': True})

    new_log = AttendanceLog(
        student_id=student_id,
        name=student.name,
        date=now.date(),
        session=session
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({'success': True, 'message': f"{session} attendance recorded for {student.name}"})
@main.route('/export_csv')
def export_csv():
    import csv
    from io import StringIO
    selected_date_str = request.args.get('date')
    if not selected_date_str:
        return redirect(url_for('main.history'))
    
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    logs = AttendanceLog.query.filter_by(date=selected_date).all()
    all_students = Student.query.all()
    
    log_map = {}
    for log in logs:
        if log.student_id not in log_map:
            log_map[log.student_id] = {}
        log_map[log.student_id][log.session] = True

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student ID', 'Name', 'Morning Session', 'Afternoon Session'])
    
    for student in all_students:
        morning = 'Present' if log_map.get(student.student_id, {}).get('Morning') else 'Absent'
        afternoon = 'Present' if log_map.get(student.student_id, {}).get('Afternoon') else 'Absent'
        cw.writerow([student.student_id, student.name, morning, afternoon])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_{selected_date_str}.csv"}
    )
