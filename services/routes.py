from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app import db
from . import bp
from .forms import ServiceForm
from models import AppSettings, Service, User
import os
import sys
from datetime import datetime
from .utils import is_process_running, start_process, terminate_process

# We'll create a simple service manager class for starting/stopping services


class ServiceManager:
    @staticmethod
    def start_service(service):
        """Start a service and update its PID and status"""
        try:
            # Prepare environment
            env = os.environ.copy()
            if service.env_vars_dict:
                env.update(service.env_vars_dict)

            # Set custom paths if provided
            settings = AppSettings.get_current()
            if settings.npm_bin_path:
                npm_bin_dir = os.path.dirname(settings.npm_bin_path)
                if npm_bin_dir:
                    env['PATH'] = npm_bin_dir + \
                        os.pathsep + env.get('PATH', '')
            if settings.node_path:
                node_dir = os.path.dirname(settings.node_path)
                if node_dir:
                    env['PATH'] = node_dir + os.pathsep + env.get('PATH', '')
            if settings.python_env_path:
                env['VIRTUAL_ENV'] = settings.python_env_path
                python_bin_dir = os.path.join(
                    settings.python_env_path,
                    'Scripts' if sys.platform == 'win32' else 'bin'
                )
                env['PATH'] = python_bin_dir + os.pathsep + env.get('PATH', '')

            success, pid, message = start_process(
                service.command, service.working_directory, env
            )
            if not success:
                raise RuntimeError(message)

            # Update service with PID and status
            service.pid = pid
            service.status = 'running'
            service.updated_at = datetime.utcnow()
            db.session.commit()
            return True, f'Servicio iniciado correctamente. PID: {pid}'
        except Exception as e:
            service.status = 'error'
            service.updated_at = datetime.utcnow()
            db.session.commit()
            return False, f"No se pudo iniciar el servicio: {str(e)}"

    @staticmethod
    def stop_service(service):
        """Stop a service and update its status"""
        try:
            if service.pid:
                if not terminate_process(service.pid):
                    raise RuntimeError(
                        f'Could not terminate process {service.pid}')

            # Update service
            service.pid = None
            service.status = 'stopped'
            service.updated_at = datetime.utcnow()
            db.session.commit()
            return True, "Servicio detenido correctamente."
        except Exception as e:
            service.status = 'error'
            service.updated_at = datetime.utcnow()
            db.session.commit()
            return False, f"No se pudo detener el servicio: {str(e)}"

    @staticmethod
    def restart_service(service):
        """Restart a service"""
        success, msg = ServiceManager.stop_service(service)
        if success:
            return ServiceManager.start_service(service)
        return success, msg

    @staticmethod
    def pause_service(service):
        """Pause a service (if supported)"""
        # For simplicity, we'll just stop it. In a real app, you might send SIGSTOP.
        return ServiceManager.stop_service(service)

    @staticmethod
    def check_service_status(service):
        """Check if a service is running by PID and update status"""
        if not service.pid:
            service.status = 'stopped'
            service.updated_at = datetime.utcnow()
            db.session.commit()
            return service.status

        service.status = 'running' if is_process_running(
            service.pid) else 'stopped'

        service.updated_at = datetime.utcnow()
        db.session.commit()
        return service.status


@bp.route('/')
@login_required
def index():
    services = Service.query.filter_by(user_id=current_user.id).all()
    return render_template('services/index.html', services=services)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            description=form.description.data,
            command=form.command.data,
            working_directory=form.working_directory.data,
            port=form.port.data,
            user_id=current_user.id
        )
        # Handle environment variables (we'll store as JSON string)
        # For now, we'll leave it empty; we can extend the form later if needed
        db.session.add(service)
        db.session.commit()
        flash('Servicio creado correctamente.', 'success')
        return redirect(url_for('services.index'))
    return render_template('services/new.html', title='Nuevo servicio', form=form)


@bp.route('/<int:id>')
@login_required
def detail(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('services/detail.html', service=service)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    form = ServiceForm()
    if form.validate_on_submit():
        service.name = form.name.data
        service.description = form.description.data
        service.command = form.command.data
        service.working_directory = form.working_directory.data
        service.port = form.port.data
        service.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Servicio actualizado correctamente.', 'success')
        return redirect(url_for('services.detail', id=service.id))
    elif request.method == 'GET':
        form.name.data = service.name
        form.description.data = service.description
        form.command.data = service.command
        form.working_directory.data = service.working_directory
        form.port.data = service.port
    return render_template('services/edit.html', title='Editar servicio', form=form, service=service)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    # Stop the service if running
    if service.status == 'running':
        ServiceManager.stop_service(service)
    db.session.delete(service)
    db.session.commit()
    flash('Servicio eliminado correctamente.', 'success')
    return redirect(url_for('services.index'))


@bp.route('/<int:id>/start', methods=['POST'])
@login_required
def start(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    success, message = ServiceManager.start_service(service)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('services.detail', id=service.id))


@bp.route('/<int:id>/stop', methods=['POST'])
@login_required
def stop(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    success, message = ServiceManager.stop_service(service)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('services.detail', id=service.id))


@bp.route('/<int:id>/restart', methods=['POST'])
@login_required
def restart(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    success, message = ServiceManager.restart_service(service)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('services.detail', id=service.id))


@bp.route('/<int:id>/pause', methods=['POST'])
@login_required
def pause(id):
    service = Service.query.get_or_404(id)
    if service.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    success, message = ServiceManager.pause_service(service)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('services.detail', id=service.id))
