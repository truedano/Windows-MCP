from mcp.server.fastmcp import FastMCP,Image
from platform import system,release
from humancursor import SystemCursor
from src.desktop import Desktop
from textwrap import dedent
from typing import Literal
import pyautogui as pg
import pyperclip as pc

pg.FAILSAFE=False
pg.PAUSE=1.0

os=system()
version=release()

instructions=dedent(f'''
Windows MCP server provides tools to interact directly with the {os} {version} desktop, 
thus enabling to operate the desktop like an actual USER.''')

desktop=Desktop()
cursor=SystemCursor()
mcp=FastMCP(name='windows-mcp',instructions=instructions)

@mcp.tool(name='Launch-Tool', description='To launch an application present in start menu')
def launch_tool(name: str) -> str:
    _,status=desktop.launch_app(name)
    if status!=0:
        return f'Failed to launch {name.title()}.'
    else:
        return f'Launched {name.title()}.'
    
@mcp.tool(name='Powershell-Tool', description='To execute commands in powershell')
def powershell_tool(command: str) -> str:
    response,status=desktop.execute_command(command)
    return f'Status Code: {status}\nResponse: {response}'

@mcp.tool(name='State-Tool',description='To get the current state of the desktop')
def state_tool()->str:
    desktop_state=desktop.get_state()
    interactive_elements=desktop_state.tree_state.interactive_elements_to_string()
    informative_elements=desktop_state.tree_state.informative_elements_to_string()
    apps=desktop_state.apps_to_string()
    active_app=desktop_state.active_app_to_string()
    return f'Active App:\n{active_app}\n\nOpened Apps:\n{apps}\n\nList of Interactive Elements:\n{interactive_elements}\n\nList of Informative Elements:\n{informative_elements}'

@mcp.tool(name='Clipboard-Tool',description='To copy content to clipboard and retrieve it when needed')
def clipboard_tool(mode: Literal['copy', 'paste'], text: str = None)->str:
    if mode == 'copy':
        if text:
            pc.copy(text)  # Copy text to system clipboard
            return f'Copied "{text}" to clipboard'
        else:
            raise ValueError("No text provided to copy")
    elif mode == 'paste':
        clipboard_content = pc.paste()  # Get text from system clipboard
        return f'Clipboard Content: "{clipboard_content}"'
    else:
        raise ValueError('Invalid mode. Use "copy" or "paste".')

@mcp.tool(name='Click-Tool',description='Clicks on the element at the specified cordinates.')
def click_tool(loc:tuple[int,int],button:Literal['left','right','middle']='left',clicks:int=1)->str:
    x,y=loc
    cursor.move_to(loc)
    control=desktop.get_element_under_cursor()
    pg.click(button=button,clicks=clicks)
    num_clicks={1:'Single',2:'Double',3:'Triple'}
    return f'{num_clicks.get(clicks)} {button} Clicked on {control.Name} Element with ControlType {control.ControlTypeName} at ({x},{y}).'

@mcp.tool(name='Type-Tool',description='Types the specified text on the selected element at the specified cordinates.')
def type_tool(loc:tuple[int,int],text:str,clear:bool=False):
    x,y=loc
    cursor.click_on(loc)
    control=desktop.get_element_under_cursor()
    if clear==True:
        pg.hotkey('ctrl','a')
        pg.press('backspace')
    pg.typewrite(text,interval=0.1)
    return f'Typed {text} on {control.Name} Element with ControlType {control.ControlTypeName} at ({x},{y}).'

# @mcp.tool(name='Screenshot-Tool',description='To view the screenshot of the desktop.')
# def screenshot_tool()->bytes:
#     data=desktop.get_screenshot()
#     return Image(data=data,format='png')

@mcp.tool(name='Scroll-Tool',description='Scrolls the screen up or down by the specified amount.')
def scroll_tool(direction:Literal['up','down']='',amount:int=0)->str:
    if direction=='up':
        pg.scroll(amount)
    elif direction=='down':
        pg.scroll(-amount)
    else:
        return 'Invalid direction.'
    return f'Scrolled  {direction} by {amount}.'

@mcp.tool(name='Drag-Tool',description='Drags the element to the specified coordinates.')
def drag_tool(from_loc:tuple,to_loc:tuple)->str:
    control=desktop.get_element_under_cursor()
    x1,y1=from_loc
    x2,y2=to_loc
    cursor.drag_and_drop(from_loc,to_loc)
    return f'Dragged the {control.Name} element with ControlType {control.ControlTypeName} from ({x1},{y1}) to ({x2},{y2}).'


@mcp.tool(name='Move-Tool',description='Moves the mouse pointer to the specified coordinates.')
def move_tool(to_loc:tuple=(0,0))->str:
    x,y=to_loc
    cursor.move_to(to_loc)
    return f'Moved the mouse pointer to ({x},{y}).'

@mcp.tool(name='Shortcut-Tool',description='Perform a keyboard shortcut.')
def shortcut_tool(shortcut:list[str]):
    pg.hotkey(*shortcut)
    return f'Pressed {'+'.join(shortcut)}.'

@mcp.tool(name='Key-Tool',description='Presses a specific key on the keyboard.')
def key_tool(key:str='')->str:
    pg.press(key)
    return f'Pressed the key {key}.'

@mcp.tool(name='Wait-Tool',description='Waits for the specified duration in seconds.')
def wait_tool(duration:int)->str:
    pg.sleep(duration)
    return f'Waited for {duration} seconds.'

if __name__ == "__main__":
    mcp.run()