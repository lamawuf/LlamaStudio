#!/usr/bin/env python3
"""
LlamaStudio — CRM для лидов
PostgreSQL + SQLAlchemy
"""

import os
from functools import wraps
from flask import Flask, render_template, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# ============== АВТОРИЗАЦИЯ ==============
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'llamastudio2024')

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        'Требуется авторизация', 401,
        {'WWW-Authenticate': 'Basic realm="LlamaStudio Admin"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# PostgreSQL (Railway) или SQLite (локально)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = f'sqlite:///{os.path.join(BASE_DIR, "data", "leads.db")}'
DATABASE_URL = os.environ.get('DATABASE_URL', DEFAULT_DB)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============== МОДЕЛИ ==============

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    leads = db.relationship('Lead', backref='city', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    leads = db.relationship('Lead', backref='category', lazy=True)

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    phones = db.Column(db.Text)  # Несколько телефонов через запятую
    social = db.Column(db.String(200))
    url_2gis = db.Column(db.Text, unique=True)  # Уникальность по 2GIS URL

    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    status = db.Column(db.String(20), default='waiting')  # waiting, callback, rejected, working, completed
    source = db.Column(db.String(50), default='2gis')  # 2gis, avito, yandex
    portfolio_used = db.Column(db.Boolean, default=False)  # Использован для портфолио (звонить последним)

    notes = db.Column(db.Text)
    result = db.Column(db.String(50))
    contact_phone = db.Column(db.String(50))  # Номер ЛПР/начальника

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    called_at = db.Column(db.DateTime)

    history = db.relationship('LeadHistory', backref='lead', lazy=True, order_by='LeadHistory.created_at.desc()')

class LeadHistory(db.Model):
    __tablename__ = 'lead_history'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    action = db.Column(db.String(50))  # called, status_changed, note_added
    old_value = db.Column(db.String(100))
    new_value = db.Column(db.String(100))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============== ROUTES ==============

@app.route('/')
@requires_auth
def index():
    response = app.make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/stats')
@requires_auth
def stats():
    city_id = request.args.get('city_id', type=int)
    category_id = request.args.get('category_id', type=int)

    query = Lead.query
    if city_id:
        query = query.filter_by(city_id=city_id)
    if category_id:
        query = query.filter_by(category_id=category_id)

    return jsonify({
        'total': query.count(),
        'waiting': query.filter_by(status='waiting').count(),
        'no_answer': query.filter_by(status='no_answer').count(),
        'callback': query.filter_by(status='callback').count(),
        'rejected': query.filter_by(status='rejected').count(),
        'working': query.filter_by(status='working').count(),
        'completed': query.filter_by(status='completed').count(),
    })

@app.route('/api/cities')
@requires_auth
def get_cities():
    cities = City.query.order_by(City.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'count': len(c.leads)} for c in cities])

@app.route('/api/categories')
@requires_auth
def get_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'count': len(c.leads)} for c in categories])

@app.route('/api/leads')
@requires_auth
def get_leads():
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    city_id = request.args.get('city_id', type=int)
    category_id = request.args.get('category_id', type=int)

    query = Lead.query

    if status:
        query = query.filter_by(status=status)
    if city_id:
        query = query.filter_by(city_id=city_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(
            db.or_(
                Lead.name.ilike(f'%{search}%'),
                Lead.phones.ilike(f'%{search}%')
            )
        )

    leads = query.order_by(Lead.created_at.desc()).limit(500).all()

    return jsonify([{
        'id': l.id,
        'name': l.name,
        'phones': l.phones,
        'social': l.social,
        'url_2gis': l.url_2gis,
        'city': l.city.name if l.city else None,
        'category': l.category.name if l.category else None,
        'status': l.status,
        'notes': l.notes,
        'result': l.result,
        'contact_phone': l.contact_phone,
        'created_at': l.created_at.isoformat() if l.created_at else None,
        'called_at': l.called_at.isoformat() if l.called_at else None,
    } for l in leads])

@app.route('/api/leads/<int:lead_id>', methods=['PATCH'])
@requires_auth
def update_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    data = request.json

    # Логируем изменения
    if 'status' in data and data['status'] != lead.status:
        history = LeadHistory(
            lead_id=lead.id,
            action='status_changed',
            old_value=lead.status,
            new_value=data['status']
        )
        db.session.add(history)
        lead.status = data['status']
        if data['status'] in ['no_answer', 'callback', 'rejected', 'working', 'completed']:
            lead.called_at = datetime.utcnow()

    if 'notes' in data:
        if data['notes'] != lead.notes:
            history = LeadHistory(
                lead_id=lead.id,
                action='note_added',
                note=data['notes']
            )
            db.session.add(history)
        lead.notes = data['notes']

    if 'result' in data:
        lead.result = data['result']

    if 'contact_phone' in data:
        lead.contact_phone = data['contact_phone']

    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/leads/<int:lead_id>/history')
@requires_auth
def get_lead_history(lead_id):
    history = LeadHistory.query.filter_by(lead_id=lead_id).order_by(LeadHistory.created_at.desc()).all()
    return jsonify([{
        'id': h.id,
        'action': h.action,
        'old_value': h.old_value,
        'new_value': h.new_value,
        'note': h.note,
        'created_at': h.created_at.isoformat()
    } for h in history])

@app.route('/api/export/vcard')
@requires_auth
def export_vcard():
    """Экспорт всех лидов в vCard для импорта в телефон"""
    import re

    # Фильтры (опционально)
    city_id = request.args.get('city_id', type=int)
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', '')

    query = Lead.query
    if city_id:
        query = query.filter_by(city_id=city_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)

    leads = query.all()

    vcards = []
    for lead in leads:
        if not lead.phones:
            continue

        # Название контакта: "Ремонт - Компания" или просто имя
        category_prefix = lead.category.name[:6] if lead.category else "Лид"
        contact_name = f"{category_prefix} - {lead.name}" if lead.name else f"{category_prefix} #{lead.id}"

        # Парсим телефоны (могут быть через запятую)
        phones = [p.strip() for p in lead.phones.split(',') if p.strip()]

        vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
ORG:{lead.name or ''}"""

        # Добавляем все телефоны
        for phone in phones:
            # Нормализуем номер
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if phone_clean:
                vcard += f"\nTEL;TYPE=WORK:{phone_clean}"

        # Добавляем заметку с городом
        if lead.city:
            vcard += f"\nNOTE:Город: {lead.city.name}"

        vcard += "\nEND:VCARD"
        vcards.append(vcard)

    # Собираем все vCards в один файл
    vcf_content = "\n".join(vcards)

    return Response(
        vcf_content,
        mimetype='text/vcard',
        headers={'Content-Disposition': 'attachment; filename=leads_contacts.vcf'}
    )

# ============== ENRICH SOCIALS ==============

@app.route('/api/enrich')
@requires_auth
def enrich_socials():
    """Обогащает лидов соцсетями из 2GIS API по имени компании"""
    import requests as req
    import time as time_module

    API_KEY = 'rurbbn3446'

    def search_2gis(name, city_name):
        """Поиск компании в 2GIS и получение соцсетей"""
        city_ids = {
            'краснодар': 36, 'москва': 32, 'сочи': 1061,
            'ростов-на-дону': 39, 'новороссийск': 4,
        }
        region_id = city_ids.get(city_name.lower() if city_name else '', 36)

        try:
            url = "https://catalog.api.2gis.com/3.0/items"
            params = {
                'q': name,
                'region_id': region_id,
                'page_size': 1,
                'fields': 'items.contact_groups',
                'key': API_KEY
            }
            resp = req.get(url, params=params, timeout=10)
            data = resp.json()
            items = data.get('result', {}).get('items', [])
            if not items:
                return None, None

            item = items[0]
            item_id = item.get('id', '')
            socials = []

            for group in item.get('contact_groups', []):
                for contact in group.get('contacts', []):
                    t = contact.get('type', '')
                    if t == 'whatsapp': socials.append('WhatsApp')
                    elif t == 'telegram': socials.append('Telegram')
                    elif t == 'viber': socials.append('Viber')
                    elif t == 'vkontakte': socials.append('VK')
                    elif t == 'instagram': socials.append('Instagram')

            url_2gis = f"https://2gis.ru/firm/{item_id}" if item_id else None
            social_str = ', '.join(sorted(set(socials))) if socials else None
            return social_str, url_2gis
        except Exception as e:
            return None, None

    # Получаем лидов без соцсетей
    leads = Lead.query.filter(
        (Lead.social.is_(None) | (Lead.social == ''))
    ).limit(10).all()

    updated = 0
    for lead in leads:
        city_name = lead.city.name if lead.city else 'Краснодар'
        social, url_2gis = search_2gis(lead.name, city_name)

        if social:
            lead.social = social
            if url_2gis and not lead.url_2gis:
                lead.url_2gis = url_2gis
            updated += 1

        time_module.sleep(0.2)

    db.session.commit()

    remaining = Lead.query.filter(
        (Lead.social.is_(None) | (Lead.social == ''))
    ).count()

    return jsonify({
        'updated': updated,
        'remaining': remaining,
        'message': f'Обновлено {updated} лидов. Осталось без соцсетей: {remaining}'
    })

# ============== INIT ==============

def init_db():
    """Создаём таблицы и базовые данные"""
    db.create_all()

    # Миграция: добавляем contact_phone если его нет
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50)"))
            conn.commit()
    except Exception as e:
        pass  # Столбец уже существует или SQLite

    # Дефолтные города
    default_cities = ['Краснодар', 'Москва', 'Сочи', 'Ростов-на-Дону', 'Новороссийск']
    for city_name in default_cities:
        if not City.query.filter_by(name=city_name).first():
            db.session.add(City(name=city_name))

    # Дефолтные категории
    default_categories = ['Ремонт квартир', 'Стоматология', 'Автосервис', 'Салон красоты', 'Юристы']
    for cat_name in default_categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))

    db.session.commit()

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=True, host='0.0.0.0', port=port)
