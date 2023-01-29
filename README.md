# Pydantic XML Extension

Allows Pydantic models to render to XML.

## Install

`pip install pydantic-xml-extension`

## Examples

### Generating XML from a model
```python
from pydantic_xml import XmlBaseModel, XmlAttribute

class ExampleModel(XmlBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int

model = ExampleModel(Name="test", age=12)
model.set_xml_attribute("name", XmlAttribute(key="id", value="123"))
model.set_xml_attribute("age", XmlAttribute(key="custom", value="value"))
print(model.xml())
>> <?xml version="1.0" encoding="utf-8"?>
>> <Model><Name id="123">test</Name><age custom="value">12</age></Model>
```

### Creating a model from XML
```python
from pydantic_xml import XmlBaseModel, XmlAttribute

class ExampleModel(XmlBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int

input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

model = ExampleModel.parse_xml(input_xml)

print(model)
>> Model(name="test", age=12)

print(model.dict())
>> {"Name": "test", "age": 12}

print(model.dict(by_alias=False))
>> {"name": "test", "age": 12}

print(model.xml())
>> <?xml version="1.0" encoding="utf-8"?>
>> <Model><Name id="123">test</Name><age custom="value">12</age></Model>
```
