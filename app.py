from enum import Enum
from flask import Flask, request, send_file, jsonify
from flask.json import JSONEncoder
from flask_restless import APIManager
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
from models import db, Company, Tag, CompanyName, TagName
from serializers import CompanySchema


class CustomJSONEncoder(JSONEncoder):
    """
    Enum 타입의 JSON serialization을 위한 custom JSON encoder 정의
    """
    def default(self, obj):
        if issubclass(type(obj), Enum):
            return obj.name
        return JSONEncoder.default(self, obj)


def create_app():
    application = Flask(__name__)
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arrested.sqlite'
    application.json_encoder = CustomJSONEncoder
    return application


def setup_db(application):
    db.init_app(application)
    migrate = Migrate(application, db)
    with application.app_context():
        db.create_all()


def setup_endpoints(application):
    with application.app_context():
        manager = APIManager(application, flask_sqlalchemy_db=db)
        manager.create_api(
            Company,
            methods=['GET', 'POST', 'OPTIONS'],
            include_columns=['id', 'name', 'tags'],
            include_methods=['name', 'lang_code'],
        )
        manager.create_api(
            Tag,
            methods=['GET', 'OPTIONS'],
            exclude_columns=['names', 'companies.tags'],
            include_methods=['name', 'lang_code'],
        )
        
        
def setup_swagger_ui(application):
    swagger_url = '/api/docs'
    swaggerui_blueprint = get_swaggerui_blueprint(
        swagger_url,
        'http://127.0.0.1:5000/api/swagger.json',    # API_URL
        config={
            'app_name': 'Arrested',
        }
    )
    application.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)


app = create_app()
setup_db(app)
setup_endpoints(app)
setup_swagger_ui(app)


@app.route('/api/swagger.json', methods=['GET'])
def send_swagger_json():
    return send_file('swagger.json')


@app.route('/api/company/<int:company_id>/name', methods=['POST', 'DELETE'])
def add_company_name(company_id):
    company = Company.query.get(company_id)
    company_name = request.json.get('company_name')
    lang_code = request.json.get('lang_code', 'ko')
    sess = db.session
    company_name_obj = CompanyName.query.filter_by(company_id, lang_code=lang_code).first()
    if 'POST' == request.method:
        if company_name_obj is None:
            company_name_obj = CompanyName(company_id=company_id, name=company_name, lang_code=lang_code)
            sess.add(company_name_obj)
        else:
            company_name_obj.name = company_name
        sess.commit()
        return 'Created', 200
    elif 'DELETE' == request.method:
        if company_name_obj is not None:
            try:
                company.names.remove(company_name_obj)
            except ValueError:
                pass
            sess.delete(company_name_obj)
            sess.commit()
        return 'Removed', 204
    

@app.route('/api/company/<int:company_id>/tag', methods=['POST', 'DELETE'])
def tag_for_company(company_id):
    company = Company.query.get(company_id)
    tag_name = request.json.get('tag_name')
    lang_code = request.json.get('lang_code', 'ko')
    sess = db.session
    tag_name_obj = TagName.query.filter_by(name=tag_name).first()
    if 'POST' == request.method:
        if tag_name_obj is None:
            tag = Tag()
            tag._name = tag_name
            tag._lang_code = lang_code
            sess.add(tag)
        else:
            tag = tag_name_obj.tag
        tag.companies.append(company)
        sess.commit()
        return 'Linked', 201
    elif 'DELETE' == request.method:
        if tag_name_obj is not None:
            tag = tag_name_obj.tag
            try:
                tag.companies.remove(company)
                sess.commit()
            except ValueError:
                pass
        return 'UnLinked', 204
    

@app.route('/api/company/search_by_name', methods=['GET'])
def search_company_by_name():
    if 'company_name' not in request.args:
        return jsonify([]), 200
    
    company_name = request.args.get('company_name')
    companies = Company.query \
        .filter(Company.id == CompanyName.company_id) \
        .filter(CompanyName.name.ilike(f'%{company_name}%')) \
        .all()
    return jsonify(CompanySchema().dump(companies, many=True)), 200


@app.route('/api/company/search_by_tag', methods=['GET'])
def search_company_by_tag():
    if 'tag_name' not in request.args:
        return jsonify([]), 200
    
    tag_name = request.args.get('tag_name')
    tags = Tag.query \
        .filter(Tag.id == TagName.tag_id) \
        .filter(TagName.name.ilike(f'%{tag_name}%')) \
        .all()
    company_id_set = set()
    for tag in tags:
        company_id_set.update([company.id for company in tag.companies])
    companies = Company.query \
        .filter(Company.id.in_(list(company_id_set))) \
        .all()
    return jsonify(CompanySchema().dump(companies, many=True)), 200


@app.route('/api/tag/<int:tag_id>/name', methods=['POST', 'DELETE'])
def add_tag_name(tag_id):
    tag = Tag.query.get(tag_id)
    tag_name = request.json.get('tag_name')
    lang_code = request.json.get('lang_code', 'ko')
    sess = db.session
    tag_name_obj = TagName.query.filter_by(tag_id=tag_id, lang_code=lang_code).first()
    if 'POST' == request.method:
        if tag_name_obj is None:
            tag_name_obj = TagName(tag_id=tag_id, name=tag_name, lang_code=lang_code)
            sess.add(tag_name_obj)
        else:
            tag_name_obj.name = tag_name
        sess.commit()
        return 'Created', 200
    elif 'DELETE' == request.method:
        if tag_name_obj is not None:
            try:
                tag.names.remove(tag_name_obj)
            except ValueError:
                pass
            sess.delete(tag_name_obj)
            sess.commit()
        return 'Removed', 204


if __name__ == '__main__':
    app.run()
