from typing import Annotated

from pydantic import fields

from pydantic_xml import XmlAttribute, XmlBaseModel


def test_pydantic_xml():
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
