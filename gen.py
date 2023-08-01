#!/usr/bin/python

"""
SPDX-License-Identifier: BSD-3-Clause
"""

import json
import sys
import xml.etree.ElementTree as ET

class Type:
    def __init__(self, el, types):
        self.el = el
        self.types = types

    def resolve(self):
        raise NotImplementedError

class Typedef(Type):
    def resolve(self):
        return self.el.get("name")

class PointerType(Type):
    def resolve(self):
        return f"{self.types[self.el.get('type')].resolve()} *"

class FundamentalType(Type):
    def resolve(self):
        return self.el.get("name")

class CvQualifiedType(Type):
    def resolve(self):
        return f"const {self.types[self.el.get('type')].resolve()}"

class ElaboratedType(Type):
    def resolve(self):
        keyword = self.el.get("keyword")
        if keyword == "struct":
            return self.types[self.el.get('type')].resolve()
        else:
            raise NotImplementedError

class ArrayType(Type):
    def resolve(self):
        return f"{self.types[self.el.get('type')].resolve()}[{self.el.get('max')}]"

class Struct(Type):
    def resolve(self):
        return f"struct {self.el.get('name')}"

class FunctionType(Type):
    pass

TYPES = [
    "Typedef",
    "PointerType",
    "FundamentalType",
    "ElaboratedType",
    "CvQualifiedType",
    "ArrayType",
    "FunctionType",
    "Struct",
]

class Function(Type):
    def to_json(self):
        obj = {}
        obj["name"] = self.el.get("name")
        returns = self.el.get("returns")
        obj["returns"] = self.types[returns].resolve()
        obj["arguments"] = []
        for arg in self.el.iter("Argument"):
            obj["arguments"].append({
                "type": self.types[arg.get("type")].resolve(),
                "name": arg.get("name")
            })
        return obj
    
class FunctionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Function):
            return obj.to_json()
        else:
            return super().default(z)

class AST:
    def __init__(self, root):
        self.root = root
        self.types = {}
        self.functions = []

        for el in root.iter():
            if el.tag not in TYPES:
                continue
            cls = getattr(sys.modules[__name__], el.tag)
            if cls is None:
                continue
            self.types[el.get("id")] = cls(el, self.types)

        for el in root.iter("Function"):
            self.functions.append(Function(el, self.types))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=argparse.FileType("r"))
    args = parser.parse_args()

    tree = ET.parse(args.infile)
    root = tree.getroot()
    print(json.dumps(AST(root).functions, cls=FunctionEncoder, indent=2))
