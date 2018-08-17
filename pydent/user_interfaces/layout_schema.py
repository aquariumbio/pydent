from marshmallow import Schema, fields


class PositionSchema(Schema):
    x = fields.Int()
    y = fields.Int()


class IOSchema(PositionSchema):
    id = fields.Int()
    height = fields.Int()
    width = fields.Int()
    model = fields.Dict()


class LayoutWireSchema(Schema):
    from_module = fields.Dict(allow_none=True)
    to_op = fields.Int()
    to = fields.Dict()
    _from = fields.Dict(data_key="from")


class TextBoxSchema(PositionSchema):
    anchor = fields.Nested(PositionSchema)
    markdown = fields.String()


class LayoutSchema(IOSchema):
    parent_id = fields.Int()
    name = fields.String()
    input = fields.Nested(IOSchema, many=True, allow_none=True)
    output = fields.Nested(IOSchema, many=True, allow_none=True)
    documentation = fields.String()
    children = fields.Nested("LayoutSchema", many=True, allow_none=True)
    wires = fields.Nested(LayoutWireSchema, allow_none=True)
    text_boxes = fields.Nested(TextBoxSchema, many=True, allow_none=True)