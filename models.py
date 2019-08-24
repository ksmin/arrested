from flask import request
from enum import Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy, event
from pycountry import languages


db = SQLAlchemy()


lang_code_dict = {lang.alpha_2: lang.name for lang in list(languages) if hasattr(lang, 'alpha_2')}
LanguageCodeEnum = Enum('LanguageCodeEnum', lang_code_dict)


companies_with_tags = \
    db.Table(
        'companies_with_tags', db.metadata,
        db.Column('company_id', db.Integer, db.ForeignKey('company.id')),
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
    )


class LocalizedNameWrapperMixin(object):
    _name = ''
    
    def get_localized_name(self):
        lang_code = request.args.get('lang_code', 'ko')
        names = [name for name in self.names if
                 name.lang_code.name == lang_code]
        print('names:', names)
        if 0 == len(names):
            names = [name for name in self.names if
                     name.lang_code.name == 'ko']
        if 0 == len(names):
            names = self.names
        return names[0]
    
    @hybrid_property
    def name(self):
        try:
            return self.get_localized_name().name
        except IndexError:
            return None
    
    @name.setter
    def name(self, value):
        self._name = value
    
    @name.expression
    def name(cls):
        return CompanyName.name
    
    _lang_code = ''
    
    @hybrid_property
    def lang_code(self):
        try:
            return self.get_localized_name().lang_code
        except IndexError:
            return None
    
    @lang_code.setter
    def lang_code(self, value):
        self._lang_code = value
    
    @lang_code.expression
    def lang_code(cls):
        return CompanyName.lang_code


class CompanyName(db.Model):
    __tablename__ = 'company_name'
    __table_args__ = (
        db.UniqueConstraint('company_id', 'lang_code',
                            name='_company_lang_unique'),
    )
    
    id = db.Column(db.Integer, db.Sequence('company_name_id_seq'),
                   primary_key=True)
    company = db.relationship("Company", back_populates="names")
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'),
                           nullable=False)
    name = db.Column(db.String, unique=True, nullable=False)
    lang_code = db.Column(db.Enum(LanguageCodeEnum), default='ko')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())


class Company(db.Model, LocalizedNameWrapperMixin):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, db.Sequence('company_id_seq'), primary_key=True)
    names = db.relationship("CompanyName", back_populates="company")
    tags = db.relationship("Tag", secondary=lambda: companies_with_tags,
                           backref='companies')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # @classmethod
    # def query(cls):
    #     original_query = db.session.query(cls)
    #     # condition = (Group.groupname == 'students')
    #     # return original_query.join(Group).filter(condition)
    #     return original_query.all()


@event.listens_for(Company, 'after_insert')
def after_insert_company(mapper, connection, target):
    connection.execute(CompanyName.__table__.insert(), {
        "company_id": target.id,
        "name": target._name,
        "lang_code": target._lang_code
    })
    

# @event.listens_for(Company, 'after_update')
# def after_update_company(mapper, connection, target):
#     company_name = CompanyName.query \
#         .filter_by(company_id=target.id,
#                    lang_code=target._lang_code) \
#         .first()
#     if company_name is None:
#         connection.execute(CompanyName.__table__.insert(), {
#             "company_id": target.id,
#             "name": target._name,
#             "lang_code": target._lang_code
#         })
#     else:
#         connection.execute(
#             CompanyName.__table__.update(CompanyName.id == company_name.id),
#             {"name": target._name}
#         )


class TagName(db.Model):
    __tablename__ = 'tag_name'
    __table_args__ = (
        db.UniqueConstraint('tag_id', 'lang_code',
                            name='_tag_lang_unique'),
    )
    
    id = db.Column(db.Integer, db.Sequence('tag_name_id_seq'),
                   primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    tag = db.relationship("Tag", back_populates="names")
    name = db.Column(db.String, unique=True, nullable=False)
    lang_code = db.Column(db.Enum(LanguageCodeEnum), default='ko')
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    
class Tag(db.Model, LocalizedNameWrapperMixin):
    __tablename__ = 'tag'
    
    id = db.Column(db.Integer, db.Sequence('tag_id_seq'), primary_key=True)
    names = db.relationship("TagName", back_populates="tag")
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())


@event.listens_for(Tag, 'after_insert')
def after_insert_tag(mapper, connection, target):
    connection.execute(TagName.__table__.insert(), {
        "tag_id": target.id,
        "name": target._name,
        "lang_code": target._lang_code
    })


# @event.listens_for(Tag, 'after_update')
# def after_update_tag(mapper, connection, target):
#     tag_name = TagName.query \
#         .filter_by(tag_id=target.id,
#                    lang_code=target._lang_code) \
#         .first()
#     if tag_name is None:
#         connection.execute(TagName.__table__.insert(), {
#             "tag_id": target.id,
#             "name": target._name,
#             "lang_code": target._lang_code
#         })
#     else:
#         connection.execute(
#             TagName.__table__.update(TagName.id == tag_name.id),
#             {"name": target._name}
#         )
