import json
from collections import defaultdict
from typing import Any, Dict, Optional, Tuple

import xmltodict
from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField

__version__ = "0.0.8"


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
        self._xml_attributes: Dict[str, list[XmlAttribute]] = defaultdict(list)

    class Config:
        allow_population_by_field_name = True
        extra = "allow"

    def dict(
        self, xml=False, remove_nulls=True, add_root=False, by_alias=True, **kwargs
    ) -> Dict[str, Any]:
        base_dict = super().dict(by_alias=by_alias, **kwargs)
        del base_dict["_xml_attributes"]
        full_dict = base_dict
        if add_root:
            full_dict = {self.get_root_name(): base_dict}
        if remove_nulls:
            remove_nulls_from_dict(full_dict)
        if not xml:
            return full_dict
        add_attributes_to_dict(
            list(self.__fields__.values()), base_dict, self._xml_attributes
        )
        if not by_alias:
            raise ValueError("Cannot use by_alias=True with xml=True")
        return full_dict

    def json(self, pretty=False, **kwargs) -> str:
        indent = None
        if pretty:
            indent = 2
        return json.dumps(self.dict(**kwargs), indent=indent)

    def xml(self, pretty=False, **kwargs) -> str:
        model_as_dict = self.dict(xml=True, add_root=True, **kwargs)
        return xmltodict.unparse(model_as_dict, pretty=pretty)

    def set_xml_attribute(self, alias: str, attribute: XmlAttribute) -> None:
        self._xml_attributes[alias].append(attribute)

    def get_root_name(self) -> str:
        root_name = self.__class__.__name__
        if hasattr(self.Config(), "xml_root_name"):
            root_name = self.Config().xml_root_name  # type: ignore
        return root_name

    @classmethod
    def get_list_fields(cls):
        fields = []
        for model_field in cls.__fields__.values():
            try:
                if isinstance(model_field.outer_type_(), list):
                    fields.append(model_field.alias)
            except ValidationError:
                pass

            try:
                if issubclass(model_field.outer_type_, BaseModel):
                    fields += model_field.type_.get_list_fields()
            except TypeError:
                pass
        return fields

    @classmethod
    def parse_xml(cls, raw: str) -> "XmlBaseModel":
        data = xmltodict.parse(raw)
        # remove root element
        for key in data:
            data = data[key]
            break
        data, attribute_details = remove_attributes(data)
        dicts_to_list(data, cls.get_list_fields())
        model = cls.parse_obj(data)
        for alias, attr_list in attribute_details.items():
            for attr in attr_list:
                model.set_xml_attribute(alias, attr)
        return model


def add_attributes_to_dict(
    fields: list[ModelField],
    data: Dict[Any, Any],
    xml_attributes: Dict[str, list[XmlAttribute]],
    path="",
):
    for model_field in fields:
        if model_field.alias not in data:
            continue

        foundation = data[model_field.alias]
        attribute_key = None
        if f"{path}{model_field.alias}" in xml_attributes:
            attribute_key = model_field.alias
        elif f"{path}{model_field.name}" in xml_attributes:
            attribute_key = model_field.name

        attr_path = f"{path}{model_field.alias}."
        if isinstance(foundation, dict):
            add_attributes_to_dict(
                model_field.type_.__fields__.values(),
                foundation,
                xml_attributes,
                attr_path,
            )
            if attribute_key:
                for attribute in xml_attributes[attr_path.strip(".")]:
                    foundation.update(attribute.copy().dict())

        elif isinstance(foundation, list):
            for index, value in enumerate(foundation):
                attr_path = f"{path}{model_field.alias}[{index}]."
                add_attributes_to_dict(
                    model_field.type_.__fields__.values(),
                    foundation[index],
                    xml_attributes,
                    attr_path,
                )
                if attr_path.strip(".") in xml_attributes:
                    for attribute in xml_attributes[attr_path.strip(".")]:
                        foundation[index].update(attribute.copy().dict())

        else:
            if attribute_key:
                foundation = {"#text": str(foundation)}
                for attribute in xml_attributes[attribute_key]:
                    foundation.update(attribute.copy().dict())

        data[model_field.alias] = foundation


def dicts_to_list(data: Dict[Any, Any], key_names: list[str]) -> None:
    for key, value in data.items():
        if isinstance(value, dict):
            dicts_to_list(value, key_names)
            if key in key_names:
                data[key] = [value]


def remove_attributes(
    data: dict, parent_path: Optional[str] = None
) -> Tuple[Any, Dict[str, list[XmlAttribute]]]:
    """Removes xmltodict attribute structure to allow pydantic parsing"""
    new_data = {}
    attribute_details: Dict[str, list[XmlAttribute]] = defaultdict(list)
    for key in data:
        if key.startswith("@"):
            if not parent_path:
                raise ValueError("parent_path cannot be None")
            # ignore attribute names and do not include in response
            attribute_details[parent_path].append(
                XmlAttribute(key=key.strip("@"), value=data[key])
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
            for key, value in details.items():
                if key in attribute_details:
                    attribute_details[key] += details[key]
                else:
                    attribute_details[key] = details[key]
        elif isinstance(data[key], list):
            for index, item in enumerate(data[key]):
                if isinstance(item, dict):
                    path = key
                    if parent_path:
                        path = f"{parent_path}.{key}[{index}]"
                    if key not in new_data:
                        new_data[key] = []
                    result, details = remove_attributes(item, parent_path=path)
                    new_data[key].append(result)
                    attribute_details.update(details)
        else:
            new_data[key] = data[key]
    return new_data, attribute_details


def remove_nulls_from_dict(data: Dict[Any, Any]) -> None:
    for key, value in list(data.items()):
        if value is None:
            del data[key]
        elif isinstance(value, dict):
            remove_nulls_from_dict(data[key])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_nulls_from_dict(item)
