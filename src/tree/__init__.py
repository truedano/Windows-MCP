from src.tree.views import TreeElementNode,Center,TreeState
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.tree.config import INTERACTIVE_CONTROL_TYPE_NAMES
from uiautomation import GetRootControl,Control,ImageControl
from typing import TYPE_CHECKING
from time import sleep

if TYPE_CHECKING:
    from src.desktop import Desktop

class Tree:
    def __init__(self,desktop:'Desktop'):
        self.desktop=desktop

    def get_state(self)->TreeState:
        sleep(0.75)
        # Get the root control of the desktop
        root=GetRootControl()
        nodes=self.get_appwise_interactive_nodes(node=root)
        return TreeState(nodes=nodes)
    
    def get_appwise_interactive_nodes(self,node:Control) -> list[TreeElementNode]:
        apps=node.GetChildren()
        visible_apps=filter(lambda app: self.desktop.get_app_status(app)!='Minimized',apps)
        interactive_nodes=[]
        # Parallel traversal
        with ThreadPoolExecutor() as executor:
            future_to_node = {executor.submit(self.get_interactive_nodes, app): app for app in visible_apps}
            for future in as_completed(future_to_node):
                try:
                    result = future.result()
                    if result:
                        interactive_nodes.extend(result)
                except Exception as e:
                    print(f"Error processing node {future_to_node[future].Name}: {e}")
        return interactive_nodes

    def get_interactive_nodes(self, node: Control) -> list[TreeElementNode]:
        interactive_nodes = []
        app_name=node.Name.strip()
        app_name='Desktop' if app_name=='Program Manager' else app_name
        def is_element_interactive(node: Control):
            if node.ControlTypeName in INTERACTIVE_CONTROL_TYPE_NAMES:
                if is_element_visible(node) and not is_element_image(node):
                    if node.IsEnabled:
                        return True
            return False
        
        def is_element_visible(node:Control,threshold:int=0):
            box=node.BoundingRectangle
            width=box.width()
            height=box.height()
            area=width*height
            is_offscreen=not node.IsOffscreen
            return area > threshold and is_offscreen
        
        def is_element_image(node:Control):
            if isinstance(node,ImageControl):
                if not node.Name.strip() or node.LocalizedControlType=='graphic':
                    return True
            return False
            
        def tree_traversal(node: Control):
            if is_element_interactive(node):
                box = node.BoundingRectangle
                center = Center(x=box.xcenter(),y=box.ycenter())
                interactive_nodes.append(TreeElementNode(
                    name=node.Name.strip() or "''",
                    control_type=node.LocalizedControlType.title(),
                    shortcut=node.AcceleratorKey or "''",
                    center=center,
                    app_name=app_name
                ))
            # Recursively check all children
            for child in node.GetChildren():
                tree_traversal(child)
        tree_traversal(node)
        return interactive_nodes