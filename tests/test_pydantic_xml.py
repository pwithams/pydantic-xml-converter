import json
from typing import Annotated, List, Optional

from pydantic import fields

from pydantic_xml import XmlAttribute, XmlBaseModel


class ListItem(XmlBaseModel):
    age: int
    some_value: Optional[str]


class SubModel(XmlBaseModel):
    age: int
    some_value: Optional[str]
    items: Optional[List[ListItem]]


class Model(XmlBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int
    optional_field: Annotated[Optional[SubModel], fields.Field(alias="SubModel")]


def test_render_xml():
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
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_model = Model(
        name="test",
        age=12,
    )
    result = Model.parse_xml(input_xml)
    assert result == expected_model


def test_parse_render_xml():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_model = Model(
        name="test",
        age=12,
    )

    result = Model.parse_xml(input_xml)
    assert result == expected_model
    output = result.xml().replace('<?xml version="1.0" encoding="utf-8"?>', "").strip()

    assert output == input_xml


def test_parse_render_xml_nulls():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_model = Model(
        name="test",
        age=12,
    )

    result = Model.parse_xml(input_xml)
    assert result == expected_model
    output = (
        result.xml(remove_nulls=False)
        .replace('<?xml version="1.0" encoding="utf-8"?>', "")
        .strip()
    )

    expected_output_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel></SubModel></Model>'
    assert output == expected_output_xml


def test_parse_render_xml_no_nulls_nested():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel><age>12</age><ListItem><age>12</age></ListItem><ListItem><age>12</age><some_value>test</some_value></ListItem></SubModel></Model>'
    result = Model.parse_xml(input_xml)
    output = result.xml().replace('<?xml version="1.0" encoding="utf-8"?>', "").strip()
    assert output == input_xml


def test_parse_render_xml_nested_attributes():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel SomeId="1234"><age>12</age><ListItem><age>12</age></ListItem><ListItem id="1234" name="test"><age>12</age><some_value>test</some_value></ListItem></SubModel></Model>'
    result = Model.parse_xml(input_xml)
    output = result.xml().replace('<?xml version="1.0" encoding="utf-8"?>', "").strip()
    assert output == input_xml


def test_parse_render_json():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_json = '{"Model": {"Name": "test", "age": 12}}'

    result = Model.parse_xml(input_xml)
    assert result.json(add_root=True) == expected_json
    assert result.dict(add_root=True) == json.loads(expected_json)
    output = result.xml().replace('<?xml version="1.0" encoding="utf-8"?>', "").strip()

    assert output == input_xml


def test_nested_models():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel><age>34</age></SubModel></Model>'
    expected_model = Model(
        name="test",
        age=12,
        optional_field=SubModel(age=34),
    )
    model = Model.parse_xml(input_xml)
    assert model == expected_model
