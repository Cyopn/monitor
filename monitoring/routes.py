from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from app import db
from . import bp
from models import Service
from services.utils import get_process_info, get_system_resources
from datetime import datetime
import threading
import time
import os

# Background service monitoring


def monitor_services(app):
    """Background thread to monitor services and restart if needed"""
    while True:
        try:
            with app.app_context():
                # Get all services that should be running
                services = Service.query.filter_by(status='running').all()
                for service in services:
                    # Check if service is actually running
                    from services.utils import is_process_running
                    if service.pid and not is_process_running(service.pid):
                        # Service died, restart it
                        service.status = 'error'
                        service.updated_at = datetime.utcnow()
                        db.session.commit()
                        # Try to restart
                        from services.routes import ServiceManager
                        ServiceManager.start_service(service)
                    elif service.pid:
                        # Service is running, update status
                        service.status = 'running'
                        service.updated_at = datetime.utcnow()
                        db.session.commit()
                time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            # Log error but keep monitoring
            print(f"Monitoring error: {e}")
            time.sleep(30)


monitor_thread = None


def start_monitoring_thread(app):
    global monitor_thread
    if monitor_thread is None or not monitor_thread.is_alive():
        monitor_thread = threading.Thread(
            target=monitor_services, args=(app,), daemon=True)
        monitor_thread.start()


@bp.route('/')
@login_required
def index():
    # Get services based on user role
    if current_user.is_admin:
        services = Service.query.all()
    else:
        services = Service.query.filter_by(user_id=current_user.id).all()
    return render_template('monitoring/index.html', services=services)


@bp.route('/api/status')
@login_required
def api_status():
    """API endpoint for getting service status (for AJAX updates)"""
    if current_user.is_admin:
        services = Service.query.all()
    else:
        services = Service.query.filter_by(user_id=current_user.id).all()

    services_data = []
    for service in services:
        process_info = get_process_info(service.pid) if service.pid else None
        services_data.append({
            'id': service.id,
            'name': service.name,
            'status': service.status,
            'pid': service.pid,
            'updated_at': service.updated_at.isoformat() if service.updated_at else None,
            'cpu_percent': process_info['cpu_percent'] if process_info else None,
            'memory_percent': process_info['memory_percent'] if process_info else None,
            'memory_bytes': process_info['memory_bytes'] if process_info else None,
        })

    return jsonify({'services': services_data})


@bp.route('/api/resources')
@login_required
def api_resources():
    """Return system and service resource usage for the dashboard."""
    if current_user.is_admin:
        services = Service.query.all()
    else:
        services = Service.query.filter_by(user_id=current_user.id).all()

    service_resources = {}
    for service in services:
        if service.pid:
            process_info = get_process_info(service.pid)
            if process_info:
                service_resources[str(service.id)] = {
                    'cpu_percent': process_info['cpu_percent'],
                    'memory_percent': process_info['memory_percent'],
                    'memory_bytes': process_info['memory_bytes'],
                }

    return jsonify({
        'system': get_system_resources(),
        'services': service_resources,
    })


@bp.route('/api/service/<int:id>/start', methods=['POST'])
@login_required
def api_start_service(id):
    """API endpoint to start a service"""
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    from services.routes import ServiceManager
    success, message = ServiceManager.start_service(service)
    return jsonify({'success': success, 'message': message})


@bp.route('/api/service/<int:id>/stop', methods=['POST'])
@login_required
def api_stop_service(id):
    """API endpoint to stop a service"""
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    from services.routes import ServiceManager
    success, message = ServiceManager.stop_service(service)
    return jsonify({'success': success, 'message': message})


def init_monitoring(app):
    # Flask's development reloader starts the factory twice.
    if app.testing or (app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true'):
        return
    start_monitoring_thread(app)
