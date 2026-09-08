from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app import db
from . import bp
from .forms import SettingsForm, UserCreateForm, UserEditForm
from models import AppSettings, User
from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def index():
    users = User.query.all()
    settings_form = SettingsForm(obj=AppSettings.get_current())
    return render_template('admin/index.html', users=users, settings_form=settings_form)


@bp.route('/settings', methods=['POST'])
@login_required
@admin_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        current_settings = AppSettings.get_current()
        current_settings.npm_bin_path = form.npm_bin_path.data or None
        current_settings.node_path = form.node_path.data or None
        current_settings.python_env_path = form.python_env_path.data or None
        db.session.commit()
        flash('Rutas globales actualizadas correctamente.', 'success')
    else:
        flash('No se pudieron guardar las rutas globales.', 'danger')
    return redirect(url_for('admin.index'))


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new():
    form = UserCreateForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/new.html', title='Nuevo usuario', form=form)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    user = User.query.get_or_404(id)
    form = UserEditForm()
    # Set original values for validation
    form.original_username = user.username
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Usuario actualizado correctamente.', 'success')
        return redirect(url_for('admin.index'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.role.data = user.role
        form.is_active.data = user.is_active
    return render_template('admin/edit.html', title='Editar usuario', form=form, user=user)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    user = User.query.get_or_404(id)
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('admin.index'))
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('admin.index'))
