# Pydantic XML Converter

Allows existing Pydantic models to be converted to/from XML with support for XML attributes.

## Install

`pip install pydantic-xml-extension`

## Examples

### Generating XML from an existing Pydantic model
```python
from pydantic import fields, BaseModel
from pydantic_xml import PydanticXmlConverter, XmlAttribute

class CustomBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        
class ExistingModel(CustomBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int

model = ExistingModel(Name="test", age=12)
converter = PydanticXmlConverter("Model")
converter.set_xml_attribute("name", XmlAttribute(key="id", value="123"))
converter.set_xml_attribute("age", XmlAttribute(key="custom", value="value"))
print(converter.xml(model))
>> <?xml version="1.0" encoding="utf-8"?>
>> <Model><Name id="123">test</Name><age custom="value">12</age></Model>
```

### Creating an instance of an existing Pydantic model from XML
```python
from pydantic_xml import XmlBaseModel, XmlAttribute

class CustomBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True

class ExistingModel(XmlBaseModel):
    name: Annotated[str, fields.Field(alias="Name")]
    age: int

input_xml = '<Model><Name id="123">test</Name><age custom="value">12</age></Model>'

converter = PydanticXmlConverter("Model")
model = converter.parse_xml(input_xml, ExistingModel)

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

to view or access the saved attributes identified during parsing, you use the `converter.xml_attributes` attribute. 
