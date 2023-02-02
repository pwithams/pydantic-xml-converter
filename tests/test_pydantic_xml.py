import json
from typing import Annotated

from pydantic import fields

from pydantic_xml import XmlAttribute, XmlBaseModel


def test_render_xml():
    class Model(XmlBaseModel):
        name: Annotated[str, fields.Field(alias="Name")]
        age: int

    m = Model(Name="test", age=12)
    m.set_xml_attribute("name", XmlAttribute(key="id", value="123"))
    m.set_xml_attribute("age", XmlAttribute(key="custom", value="value"))
    xml_string = m.xml()
    xml_string = xml_string.replace(
        '<?xml version="1.0" encoding="utf-8"?>', ""
    ).strip()
    expected_xml = (
        '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'
    )
    assert xml_string == expected_xml


def test_parse_xml():
    class Model(XmlBaseModel):
        name: Annotated[str, fields.Field(alias="Name")]
        age: int

    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_model = Model(
        name="test",
        age=12,
    )
    result = Model.parse_xml(input_xml)
    assert result == expected_model


def test_parse_render_xml():
    class Model(XmlBaseModel):
        name: Annotated[str, fields.Field(alias="Name")]
        age: int

    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_model = Model(
        name="test",
        age=12,
    )

    result = Model.parse_xml(input_xml)
    assert result == expected_model
    output = result.xml().replace('<?xml version="1.0" encoding="utf-8"?>', "").strip()

    assert output == input_xml


def test_parse_render_json():
    class Model(XmlBaseModel):
        name: Annotated[str, fields.Field(alias="Name")]
        age: int

    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_json = '{"Model": {"Name": "test", "age": 12}}'

    result = Model.parse_xml(input_xml)
    assert result.json() == expected_json
    assert result.dict() == json.loads(expected_json)
    output = result.xml().replace('<?xml version="1.0" encoding="utf-8"?>', "").strip()

    assert output == input_xml
