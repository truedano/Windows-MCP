from dataclasses import dataclass,field

@dataclass
class TreeState:
    nodes:list['TreeElementNode']=field(default_factory=[])

    def elements_to_string(self)->str:
        return '\n'.join([f'Label: {index}|App Name: {node.app_name}|ControlType: {node.control_type}|Name: {node.name}|Shortcut: {node.shortcut}|Center: {node.center.to_string()}' for index,node in enumerate(self.nodes)])

@dataclass
class Center:
    x:int
    y:int

    def to_string(self)->str:
        return f'({self.x},{self.y})'

@dataclass
class TreeElementNode:
    name:str
    control_type:str
    shortcut:str
    center:Center
    app_name:str