from marshmallow import Schema, fields


class TagSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    created_at = fields.String()
    
    # def get_localized_name(self, obj):
    #     return "localized_name"
    #
    # def save_localized_name(self, obj):
    #     return "save_localized_name"
    

class CompanySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    lang_code = fields.Method('decode_lang_code')
    created_at = fields.String()
    tags = fields.Nested(TagSchema(), many=True)
    
    def decode_lang_code(self, obj):
        print(self, obj)


def schema_to_serializer(schema):
    return lambda instance: schema.dump(instance)


def schema_to_deserializer(schema):
    return lambda data: schema.load(data).data


tag_schema = TagSchema()
company_schema = CompanySchema()
