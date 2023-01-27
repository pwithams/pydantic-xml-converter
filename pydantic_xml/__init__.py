from typing import Dict

import xmltodict
from pydantic import BaseModel

__version__ = ""


class XmlAttribute(BaseModel):
    key: str
    value: str

    def dict(self):
        return {
            f"@{self.key}": self.value,
        }


class XmlBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        xml_attributes: Dict[str, XmlAttribute] = {}

    def dict(self, xml=False, by_alias=True):
        base_dict = super().dict(by_alias=by_alias)
        if not xml:
            return base_dict
        for key, model_field in self.__fields__.items():
            alias = model_field.alias
            if model_field.name in self.Config().xml_attributes:
                if type(base_dict[alias]) not in [list, dict]:
                    foundation = {"#text": str(base_dict[alias])}
                else:
                    foundation = {alias: base_dict[alias]}
                base_dict[alias] = foundation
                foundation.update(
                    self.Config().xml_attributes[model_field.name].copy().dict()
                )

        return base_dict

    def xml(self, pretty=False) -> str:
        model_as_dict = self.dict(xml=True)
        root_name = self.__class__.__name__
        if hasattr(self.Config(), "xml_root_name"):
            root_name = self.Config().xml_root_name
        return xmltodict.unparse({root_name: model_as_dict}, pretty=pretty)

    def set_xml_attribute(self, alias: str, attribute: XmlAttribute) -> None:
        self.Config().xml_attributes[alias] = attribute
