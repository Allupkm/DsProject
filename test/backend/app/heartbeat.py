from flask import Blueprint, jsonify
from app.models import Heartbeat
from app import db
from datetime import datetime, timedelta
import socket
import requests
import time
from app.utils import scheduler
from apscheduler.schedulers.background import BackgroundScheduler

heartbeat = Blueprint('heartbeat', __name__)

def check_server_heartbeat():
    try:
        heartbeat = Heartbeat(
            component='server',
            status='up',
            message='Server is running'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return True
    except Exception as e:
        heartbeat = Heartbeat(
            component='server',
            status='down',
            message=f'Server error: {str(e)}'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return False

def check_database_heartbeat():
    try:
        result = db.session.execute('SELECT 1').fetchone()
        if result and result[0] == 1:
            heartbeat = Heartbeat(
                component='database',
                status='up',
                message='Database is responsive'
            )
            db.session.add(heartbeat)
            db.session.commit()
            return True
    except Exception as e:
        heartbeat = Heartbeat(
            component='database',
            status='down',
            message=f'Database error: {str(e)}'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return False

def check_client_heartbeat(client_ip):
    try:
        heartbeat = Heartbeat(
            component='client',
            status='up',
            message=f'Client {client_ip} last seen'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return True
    except Exception as e:
        heartbeat = Heartbeat(
            component='client',
            status='down',
            message=f'Client error: {str(e)}'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return False

@heartbeat.route('/api/heartbeat/server', methods=['GET'])
def server_heartbeat():
    status = check_server_heartbeat()
    return jsonify({
        'status': 'up' if status else 'down',
        'timestamp': datetime.utcnow().isoformat()
    })

@heartbeat.route('/api/heartbeat/database', methods=['GET'])
def database_heartbeat():
    status = check_database_heartbeat()
    return jsonify({
        'status': 'up' if status else 'down',
        'timestamp': datetime.utcnow().isoformat()
    })

@heartbeat.route('/api/heartbeat/client/<client_ip>', methods=['GET'])
def client_heartbeat(client_ip):
    status = check_client_heartbeat(client_ip)
    return jsonify({
        'status': 'up' if status else 'down',
        'timestamp': datetime.utcnow().isoformat()
    })

def init_scheduled_heartbeats():
    scheduler = BackgroundScheduler()
    

    scheduler.add_job(
        func=check_server_heartbeat,
        trigger='interval',
        minutes=5,
        id='server_heartbeat',
        name='Check server status every 5 minutes',
        replace_existing=True
    )
    

    scheduler.add_job(
        func=check_database_heartbeat,
        trigger='interval',
        minutes=5,
        id='database_heartbeat',
        name='Check database status every 5 minutes',
        replace_existing=True
    )
    
    scheduler.start()