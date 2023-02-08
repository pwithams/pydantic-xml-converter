# Pydantic XML Extension

Allows Pydantic models to render to XML.

## Install

`pip install pydantic-xml-extension`

## Examples

### Generating XML from a model
```python
from pydantic import fields, BaseModel
from pydantic_xml import PydanticXmlConverter, XmlAttribute

class CustomBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        
class ExampleModel(CustomBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int

model = ExampleModel(Name="test", age=12)
converter = PydanticXmlConverter("Model")
converter.set_xml_attribute("name", XmlAttribute(key="id", value="123"))
converter.set_xml_attribute("age", XmlAttribute(key="custom", value="value"))
print(converter.xml(model))
>> <?xml version="1.0" encoding="utf-8"?>
>> <Model><Name id="123">test</Name><age custom="value">12</age></Model>
```

### Creating a model from XML
```python
from pydantic_xml import XmlBaseModel, XmlAttribute

class CustomBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True

class ExampleModel(XmlBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int

input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

converter = PydanticXmlConverter("Model")
model = converter.parse_xml(input_xml, ExampleModel)

print(model)
>> Model(name="test", age=12)

print(converter.generate_dict(model))
>> {"Name": "test", "age": 12}

print(converter.generate_dict(model, by_alias=False))
>> {"name": "test", "age": 12}

print(converter.generate_xml(model))
>> <?xml version="1.0" encoding="utf-8"?>
>> <Model><Name id="123">test</Name><age custom="value">12</age></Model>
```
