import json
from collections import defaultdict
from typing import Any, Dict, Optional, Tuple

import xmltodict
from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField

__version__ = "0.0.13"


class XmlAttribute(BaseModel):
    key: str
    value: str

    def dict(self, **kwargs):
        return {
            f"@{self.key}": self.value,
        }


class PydanticXmlConverter:
    def __init__(self, root_name) -> None:
        self.xml_attributes: Dict[str, list[XmlAttribute]] = defaultdict(list)
        self.root_name: str = root_name

    def generate_dict(
        self,
        base_model: BaseModel,
        xml=False,
        remove_nulls=True,
        add_root=False,
        by_alias=True,
        **kwargs,
    ) -> Dict[str, Any]:
        base_dict = base_model.dict(by_alias=by_alias, **kwargs).copy()
        full_dict = base_dict
        if add_root:
            full_dict = {self.root_name: base_dict}
        if remove_nulls:
            remove_nulls_from_dict(full_dict)
        if not xml:
            return full_dict
        add_attributes_to_dict(
            list(base_model.__fields__.values()), base_dict, self.xml_attributes
        )
        if not by_alias:
            raise ValueError("Cannot use by_alias=True with xml=True")
        return full_dict

    def generate_json(self, base_model: BaseModel, pretty=False, **kwargs) -> str:
        indent = None
        if pretty:
            indent = 2
        return json.dumps(self.generate_dict(base_model, **kwargs), indent=indent)

    def generate_xml(self, base_model: BaseModel, pretty=False, **kwargs) -> str:
        model_as_dict = self.generate_dict(
            base_model, xml=True, add_root=True, **kwargs
        )
        return xmltodict.unparse(model_as_dict, pretty=pretty)

    def set_xml_attribute(self, alias: str, attribute: XmlAttribute) -> None:
        self.xml_attributes[alias].append(attribute)

    def parse_xml(self, raw: str, cls: type) -> BaseModel:
        data = xmltodict.parse(raw)
        # remove root element
        for key in data:
            data = data[key]
            break
        data, attribute_details = remove_attributes(data)
        dicts_to_list(data, get_list_fields(cls), attribute_details)
        remove_nulls_from_dict(data)
        self.xml_attributes = defaultdict(list)
        for alias, attr_list in attribute_details.items():
            for attr in attr_list:
                self.set_xml_attribute(alias, attr)
        model = cls.parse_obj(data)
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
        if f"{path}{model_field.name}" in xml_attributes:
            attribute_key = model_field.name
        if f"{path}{model_field.alias}" in xml_attributes:
            attribute_key = model_field.alias

        attr_path = f"{path}{model_field.name}."
        if attribute_key:
            attr_path = f"{path}{attribute_key}."
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
                for attribute in xml_attributes[attr_path.strip(".")]:
                    foundation.update(attribute.copy().dict())

        data[model_field.alias] = foundation


def dicts_to_list(
    data: Dict[Any, Any], key_names: list[str], attribute_details
) -> None:
    for key, value in data.items():
        if isinstance(value, dict):
            dicts_to_list(value, key_names, attribute_details)
            if key in key_names:
                data[key] = [value]
                for attribute_key in list(attribute_details.keys()):
                    if f"{key}." in attribute_key:
                        attribute_details[
                            attribute_key.replace(f"{key}.", f"{key}[0].")
                        ] = attribute_details[attribute_key]
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    dicts_to_list(item, key_names, attribute_details)


def remove_attributes(
    data: dict, parent_path: Optional[str] = None
) -> Tuple[Any, Dict[str, list[XmlAttribute]]]:
    """Removes xmltodict attribute structure to allow pydantic parsing"""
    new_data = {}
    attribute_details: Dict[str, list[XmlAttribute]] = defaultdict(list)
    non_attr_count = 0
    for key in data:
        if not key.startswith("@"):
            non_attr_count += 1
    if non_attr_count == 0:
        return None, attribute_details
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
        if value is None or value == {}:
            del data[key]
        elif isinstance(value, dict):
            remove_nulls_from_dict(data[key])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_nulls_from_dict(item)


def get_list_fields(cls):
    fields = []
    for model_field in cls.__fields__.values():
        try:
            if isinstance(model_field.outer_type_(), list):
                fields.append(model_field.alias)
                fields += get_list_fields(model_field.type_)
        except (ValidationError, TypeError):
            pass

        try:
            if issubclass(model_field.outer_type_, BaseModel):
                fields += get_list_fields(model_field.type_)
        except TypeError:
            pass
    return fields
