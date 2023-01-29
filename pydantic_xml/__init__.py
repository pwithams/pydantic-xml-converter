from typing import Any, Dict, Optional, Tuple

import xmltodict
from pydantic import BaseModel

__version__ = "0.0.2"


class XmlAttribute(BaseModel):
    """Represents an xmltodict attribute."""

    key: str
    value: str

    def dict(self, **kwargs):
        return {
            f"@{self.key}": self.value,
        }


class XmlBaseModel(BaseModel):
    """Represents an xmltodict attribute."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._xml_attributes: Dict[str, XmlAttribute] = {}

    class Config:
        allow_population_by_field_name = True
        extra = "allow"

    def dict(self, xml=False, by_alias=True, **kwargs):
        base_dict = super().dict(by_alias=by_alias, **kwargs)
        del base_dict["_xml_attributes"]
        if not xml:
            return base_dict
        for key, model_field in self.__fields__.items():
            attribute_key = None
            if model_field.alias in self._xml_attributes:
                attribute_key = model_field.alias
            if model_field.name in self._xml_attributes:
                attribute_key = model_field.name
            if attribute_key:
                if type(base_dict[model_field.alias]) not in [list, dict]:
                    foundation = {"#text": str(base_dict[model_field.alias])}
                else:
                    foundation = {alias: base_dict[model_field.alias]}
                base_dict[model_field.alias] = foundation
                foundation.update(self._xml_attributes[attribute_key].copy().dict())

        return base_dict

    def xml(self, pretty=False) -> str:
        model_as_dict = self.dict(xml=True)
        root_name = self.__class__.__name__
        if hasattr(self.Config(), "xml_root_name"):
            root_name = self.Config().xml_root_name
        return xmltodict.unparse({root_name: model_as_dict}, pretty=pretty)

    def set_xml_attribute(self, alias: str, attribute: XmlAttribute) -> None:
        self._xml_attributes[alias] = attribute

    @classmethod
    def parse_xml(cls, raw: str):
        data = xmltodict.parse(raw)
        # remove root element
        for key in data:
            data = data[key]
            break
        data, attribute_details = remove_attributes(data)
        model = cls.parse_obj(data)
        for alias, attr in attribute_details.items():
            model.set_xml_attribute(alias, attr)
        return model


def remove_attributes(
    data: dict, parent_path: Optional[str] = None
) -> Tuple[Any, Dict[str, XmlAttribute]]:
    """Removes xmltodict attribute structure to allow pydantic parsing"""
    new_data = {}
    attribute_details: Dict[str, XmlAttribute] = {}
    for key in data:
        if key.startswith("@"):
            if not parent_path:
                raise ValueError("parent_path cannot be None")
            # ignore attribute names and do not include in response
            attribute_details[parent_path] = XmlAttribute(
                key=key.strip("@"), value=data[key]
            )
            continue
        if key == "#text":
            # return text content without nesting
            return data[key], attribute_details
        if isinstance(data[key], dict):
            # if not a text attribute, recursively perform
            # for children
            path = key
            if parent_path:
                path = f"{parent_path}.{key}"
            new_data[key], details = remove_attributes(data[key], parent_path=path)
            attribute_details.update(details)
    return new_data, attribute_details
