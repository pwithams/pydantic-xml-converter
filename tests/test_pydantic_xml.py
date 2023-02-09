import json
import re
from typing import Annotated, List, Optional

from pydantic import BaseModel, fields

import pydantic_xml


def strip_xml(xml_string):
    return re.sub(r">\s*<", ">\n<", xml_string.replace("\n", "")).strip()


class CustomBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True


class ListItem(CustomBaseModel):
    age: int
    some_value: Optional[str]


class SubModel(CustomBaseModel):
    age: int
    some_value: Optional[str]
    items: Annotated[Optional[List[ListItem]], fields.Field(alias="ListItem")]


class Model(CustomBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int
    optional_field: Annotated[Optional[SubModel], fields.Field(alias="SubModel")]


def test_render_xml():
    m = Model(Name="test", age=12)
    converter = pydantic_xml.PydanticXmlConverter("Model")
    converter.set_xml_attribute(
        "Name", pydantic_xml.XmlAttribute(key="id", value="123")
    )
    converter.set_xml_attribute(
        "age", pydantic_xml.XmlAttribute(key="custom", value="value")
    )
    xml_string = converter.generate_xml(m)
    xml_string = xml_string.replace(
        '<?xml version="1.0" encoding="utf-8"?>', ""
    ).strip()
    expected_xml = (
        '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'
    )
    assert xml_string == expected_xml


def test_render_xml_no_alias():
    m = Model(Name="test", age=12)

    converter = pydantic_xml.PydanticXmlConverter("Model")
    converter.set_xml_attribute(
        "name", pydantic_xml.XmlAttribute(key="id", value="123")
    )
    converter.set_xml_attribute(
        "age", pydantic_xml.XmlAttribute(key="custom", value="value")
    )
    xml_string = converter.generate_xml(m)
    xml_string = xml_string.replace(
        '<?xml version="1.0" encoding="utf-8"?>', ""
    ).strip()
    expected_xml = (
        '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'
    )
    assert xml_string == expected_xml


def test_parse_xml():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    converter = pydantic_xml.PydanticXmlConverter("Model")
    expected_model = Model(
        name="test",
        age=12,
    )
    model = converter.parse_xml(input_xml, Model)
    assert model == expected_model


def test_parse_render_xml():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    converter = pydantic_xml.PydanticXmlConverter("Model")
    expected_model = Model(
        name="test",
        age=12,
    )

    model = converter.parse_xml(input_xml, Model)
    assert model == expected_model
    output = (
        converter.generate_xml(model)
        .replace('<?xml version="1.0" encoding="utf-8"?>', "")
        .strip()
    )

    assert output == input_xml


def test_parse_render_xml_nulls():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    converter = pydantic_xml.PydanticXmlConverter("Model")
    expected_model = Model(
        name="test",
        age=12,
    )

    model = converter.parse_xml(input_xml, Model)
    assert model == expected_model
    output = (
        converter.generate_xml(model, remove_nulls=False)
        .replace('<?xml version="1.0" encoding="utf-8"?>', "")
        .strip()
    )

    expected_output_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel></SubModel></Model>'
    assert output == expected_output_xml


def test_parse_render_xml_no_nulls_nested():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel><age>12</age><ListItem><age>12</age></ListItem><ListItem><age>12</age><some_value>test</some_value></ListItem></SubModel></Model>'
    converter = pydantic_xml.PydanticXmlConverter("Model")
    model = converter.parse_xml(input_xml, Model)
    expected_model = Model(
        name="test",
        age=12,
        optional_field=SubModel(
            age=12,
            items=[ListItem(age=12), ListItem(age=12, some_value="test")],
        ),
    )
    assert model == expected_model
    output = (
        converter.generate_xml(model)
        .replace('<?xml version="1.0" encoding="utf-8"?>', "")
        .strip()
    )
    assert output == input_xml


def test_parse_render_xml_nested_attributes():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel SomeId="1234"><age>12</age><ListItem><age>12</age></ListItem><ListItem id="1234" name="test"><age>12</age><some_value>test</some_value></ListItem><ListItem><age>12</age></ListItem></SubModel></Model>'
    converter = pydantic_xml.PydanticXmlConverter("Model")
    model = converter.parse_xml(input_xml, Model)
    output = (
        converter.generate_xml(model)
        .replace('<?xml version="1.0" encoding="utf-8"?>', "")
        .strip()
    )
    assert output == input_xml


def test_parse_render_json():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

    expected_json = '{"Model": {"Name": "test", "age": 12}}'

    converter = pydantic_xml.PydanticXmlConverter("Model")
    model = converter.parse_xml(input_xml, Model)
    assert converter.generate_json(model, add_root=True) == expected_json
    assert converter.generate_dict(model, add_root=True) == json.loads(expected_json)
    output = (
        converter.generate_xml(model)
        .replace('<?xml version="1.0" encoding="utf-8"?>', "")
        .strip()
    )

    assert output == input_xml


def test_nested_models():
    input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age><SubModel><age>34</age></SubModel></Model>'
    expected_model = Model(
        name="test",
        age=12,
        optional_field=SubModel(age=34),
    )
    converter = pydantic_xml.PydanticXmlConverter("Model")
    model = converter.parse_xml(input_xml, Model)
    assert model == expected_model


def test_remove_nulls():
    data = {
        "attr1": 12,
        "attr2": None,
        "attr3": {
            "attr3.1": None,
            "attr3.2": [{"list": "value", "none": None}, {"list": "value2"}],
        },
    }
    expected_response = {
        "attr1": 12,
        "attr3": {"attr3.2": [{"list": "value"}, {"list": "value2"}]},
    }
    pydantic_xml.remove_nulls_from_dict(data)
    assert data == expected_response


def test_dicts_to_list():
    data = {
        "attr1": 12,
        "attr2": {"some_data": 123},
        "attr3": {"some_data2": {"test": 123}},
    }
    expected_data = {
        "attr1": 12,
        "attr2": [{"some_data": 123}],
        "attr3": [{"some_data2": [{"test": 123}]}],
    }
    pydantic_xml.dicts_to_list(data, ["attr2", "attr3", "some_data2"], {})
    assert data == expected_data


def test_random_xml():
    xml_string = """<?xml version="1.0" encoding="utf-8"?>
    <root>
      <monkey fat="beginning">-1849338856</monkey>
      <of>
        <changing alive="station">
          <sang rays="speed">203723125.97784948</sang>
          <birth maybe="sweet">279884000</birth>
          <calm rather="beginning">attack</calm>
          <mass them="afraid">needle</mass>
          <one poem="excited">arrangement</one>
          <another probably="rise">197055265.1714635</another>
        </changing>
        <simple open="running">orbit</simple>
        <basket>-797888089</basket>
        <turn>-737700207</turn>
        <principal>-1187301227.2417045</principal>
        <bean sold="mean">-456432991</bean>
      </of>
      <slow>-400726633</slow>
      <dress>-832880860.8035483</dress>
      <themselves>1106985214.2440586</themselves>
      <necessary hello="gather">-1232936066</necessary>
    </root>
    """

    class Changing(BaseModel):
        sang: float
        birth: int
        calm: str
        mass: str
        one: str
        another: float

    class Of(BaseModel):
        changing: Changing
        simple: str
        basket: int
        turn: int
        principal: float
        bean: int

    class Root(BaseModel):
        monkey: int
        of: Of
        slow: int
        dress: float
        themselves: float
        necessary: int

    converter = pydantic_xml.PydanticXmlConverter("root")
    root_model = converter.parse_xml(xml_string, Root)
    output_string = converter.generate_xml(root_model, pretty=True)
    assert strip_xml(output_string) == strip_xml(xml_string)
