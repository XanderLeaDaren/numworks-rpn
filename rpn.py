__version__ = "2025-12-19 T 10:27 UTC+1"

from math import exp, log, log10, sin, asin, cos, acos, tan, atan, pi, sqrt
from time import sleep, monotonic
from random import random

from ion import keydown
from kandinsky import draw_string, fill_rect

from micropython import kbd_intr
kbd_intr(-1)  # Disable KeyboardInterrupt


# RPN AND PYTHON SPECIFIC FUNCTIONS

def python_int(foo):
    """Python-specific: keep integers instead of floats, if possible."""
    foo = float(foo)
    try: integer = int(foo)
    except OverflowError as message: draw_error(message)
    else:
        if foo == integer:
            foo = integer
        return foo

def python_trailing(value):
    # Remove Python-specific trailing 000000001 if possible
    if value.count(".") == 1 and (value[-1] == "1" or value[-1] == "2"):
        zeros = 0; last = -2
        while value[last] == "0": zeros += 1; last -= 1
        if zeros >= 7: value = value[:last+1]
    # Remove Python-specific trailing 9s if possible
    if value.count(".") == 1 and value[-1] == "9":
        nines = 0; last = -2
        while value[last] == "9": nines += 1; last -= 1
        if nines >= 7:
            value = value[:last+1]
            last_digit = int(value[-1]) + 1
            value = value[:-1] + str(last_digit)
    return value

def drop():
    stack.pop(0)
    if fixed: stack.append(stack[2])

def push(foo, history=True):
    try: top = python_int(foo)
    except Exception as message: draw_error(message)
    else:
        if history: global lastx; lastx = foo
        stack.insert(0, top)
    if fixed: stack.pop()

def evaluate1(operation):
    """Evaluate unary operations."""
    global entry, stack, lastx
    if not entry and stack:
        try: result = operation(stack[0])
        except Exception as message: draw_error(message)
        else: lastx = stack[0]; stack[0] = python_int(result)
    elif entry:
        try: result = operation(float(entry))
        except Exception as message: draw_error(message)
        else: lastx = entry; stack.insert(0, python_int(result)); entry = ""
        draw_command(0)
    draw_stack(8, 0.2)

def evaluate2(operation, refresh=True):
    """Evaluate binary operations."""
    global entry, stack, lastx
    if not entry and len(stack) >= 2:
        try: result = operation(stack[1], stack[0])
        except Exception as message: draw_error(message)
        else: lastx = stack[0]; stack[1] = python_int(result); drop()
    elif entry and stack:
        try: result = operation(stack[0], float(entry))
        except Exception as message: draw_error(message)
        else: lastx = entry; stack[0] = python_int(result); entry = ""
    if refresh: display()


# MATH FUNCTIONS

def factorial(n):
    if float(n) != int(n):
        raise Exception("math domain error")
    else:
        prod = 1; max = n
        while max > 0: prod *= max; max -= 1
        return prod

def hms(dec):
    """Convert decimal time in hours to sexagesimal format."""
    hours = int(dec)
    minutes = int((dec - hours) * 60)
    seconds = ((dec - hours) * 60 - minutes) * 60
    return hours + minutes/100 + seconds/10000

def prime_facto(n):
    """Find the lowest prime divisor of a natural number n."""
    if float(n) != int(n):
        raise Exception("math domain error")
    else:
        div = 2
        while div**2 <= n:
            if n % div == 0: return div
            div += 1
        return 1


# GUI FUNCTIONS

def draw_register(level, timeout=0, selected=False):
    """Display the requested stack register on correct background and line height."""
    if fixed:
        height = 46; name = ("X:", "Y:", "Z:", "T:")
    else:
        height = 23; name = ("1:", "2:", "3:", "4:", "5:", "6:", "7:", "8:")
    bg_color = (245,250,255) if level % 2 == 0 else (255,254,255)
    bg_text = (214,213,231) if selected else bg_color
    if stack[level] > 10**25:  # Scientific notation instead of overflowing big num
        value = "{:.20e}".format(stack[level])
    else:
        value = python_trailing(str(stack[level]))
    y_text = 185 - (level+1)*height + (height - 18) // 2
    fill_rect(0, 184 - (level+1)*height, 320, height, bg_color)
    draw_string(name[level], 10, y_text, (0,0,0), bg_color)
    draw_string(value, 310 - 10*len(value), y_text, (0,0,0), bg_text)
    sleep(timeout)

def draw_stack(depth=8, timeout=0):
    """Refresh the first {depth} stack levels from stack top."""
    if fixed: depth = 4
    if depth > len(stack): depth = len(stack)
    for level in range(depth):
        draw_register(level)
    sleep(timeout)

def draw_command(timeout=0.2):
    """Refresh the command line, bottom of the screen."""
    fill_rect(0, 185, 320, 37, (255,254,255))
    draw_string(entry, 5, 195, (0,0,0), (255,254,255))
    blink_cursor(True)
    sleep(timeout)

def display(command_line=True):
    """Refresh the whole screen: background, all stack levels, separator, and command line."""
    fill_rect(0, 0, 320, 184, (245,250,255))
    # On fixed stack, drop oldest level if not displayable
    levels = 4 if fixed else 8
    if fixed and len(stack) > levels: stack.pop()
    n = len(stack) if len(stack) < levels else levels
    draw_stack(n)
    fill_rect(0, 184, 320, 1, (223,217,222))
    if command_line: draw_command()
    else: sleep(0.2)

def blink_cursor(forced=False):
    color = (0,0,0) if int(monotonic()) % 2 == 0 or forced else (255,254,255)
    fill_rect(5 + 10*len(entry), 194, 1, 18, color)


def draw_error(text):
    """Display an error or exception in a black dialog box."""
    fill_rect(144 - 5*len(str(text)), 89, 32 + 10*len(str(text)), 44, (0,0,0))
    draw_string(str(text), 160 - 5*len(str(text)), 102, (255,254,255), (0,0,0))
    sleep(0.5); pressed = False
    while not pressed:
        for i in range(53):
            if keydown(i): pressed = True
    display(False)


def draw_item(line, items, descriptions, selected=False):
    """Display a menu item line, eventually on a selected background."""
    h = 174 // len(items)
    bg_color = (214,213,231) if selected else (255,254,255)
    fill_rect(28, 49 + h*line, 264, h - 1, bg_color)
    draw_string(items[line], 35, 41 + h*line + h // 2, (0,0,0), bg_color)
    draw_string(descriptions[line], 285 - 10*len(descriptions[line]), 41 + h*line + h // 2, (164,165,164), bg_color)

def draw_menu(items, descriptions):
    """Display all items and descriptions menu inside a dialog box."""
    fill_rect(27, 48, 266, 174, (238,238,238))
    fill_rect(28, 49, 264, 173, (255,254,255))
    h = 174 // len(items)
    for i in range(len(items)):
        draw_item(i, items, descriptions)
        fill_rect(28, 48 + h*i, 264, 1, (238,238,238))
    fill_rect(28, 48 + h*len(items), 264, 1, (238,238,238))


def varbox():
    """Display a dialog with functions mapped to ALPHA + some key."""
    keys = ("D", "R", "C", "F", "H", "P", "?")
    desc = ("Set angles to degrees", "Set angles to radians", "Convert °F to °C", "Convert °C to °F", "Convert hrs to h:min", "Prime factorisation", "Random number in [0,1)")
    fill_rect(27, 27, 266, 21, (65,64,65))
    fill_rect(28, 28, 264, 19, (108,99,115))
    draw_string("Alpha shortcuts", 85, 28, (255,254,255), (108,99,115))
    draw_menu(keys, desc)
    sleep(0.5); pressed = False
    while not pressed:
        for i in (4, 5, 15):  # OK, BACK, VAR
            if keydown(i): pressed = True
    display()


def toolbox():
    """Display a dialog with common RPN functions and their mappings."""
    keys = (" xnt", "  (", "  )", " Ans", "[shift]Ans", "[shift] ÷", "[shift] -")
    desc = ("Fixed/dynamic stack", "ROLL (n)/all levels", "SWAP last two levels", "Copy last X value", "Copy 2nd level", "Inverse", "Change signs")
    fill_rect(27, 27, 266, 21, (65,64,65))
    fill_rect(28, 28, 264, 19, (108,99,115))
    draw_string("Hotkeys", 125, 28, (255,254,255), (108,99,115))
    draw_menu(keys, desc)
    sleep(0.5); pressed = False
    while not pressed:
        for i in (4, 5, 16):  # OK, BACK, TOOLBOX
            if keydown(i): pressed = True
    display()


def percentage():
    """Display a dialog with common percentage functions."""
    items = ("%", "Δ%", "%T", "±%", "MU%P")
    descriptions = ("Percentage of X", "Percent difference", "Percent of total", "Evolution or markup", "Markup on price")
    fill_rect(27, 27, 266, 21, (65,64,65))
    fill_rect(28, 28, 264, 19, (108,99,115))
    draw_string("Percentage", 110, 28, (255,254,255), (108,99,115))
    draw_menu(items, descriptions)
    line = 0; quit = False
    draw_item(0, items, descriptions, True)
    while not quit:
        sleep(0.13)
        if keydown(1) and line > 0:  # UP
            draw_item(line, items, descriptions)
            draw_item(line - 1, items, descriptions, True)
            line -= 1
        if keydown(2) and line < len(items) - 1:  # DOWN
            draw_item(line, items, descriptions)
            draw_item(line + 1, items, descriptions, True)
            line += 1
        if keydown(4) or keydown(52):  # OK/EXE
            if line == 0:  # % Percentage of X
                if entry and stack:
                    base = stack[0]
                    evaluate2(lambda x, y: x*y / 100, False)
                    push(base, False)
                    stack[0], stack[1] = stack[1], stack[0]
                elif not entry and len(stack) >= 2:
                    base = stack[1]
                    evaluate2(lambda x, y: x*y / 100, False)
                    push(base, False)
                    stack[0], stack[1] = stack[1], stack[0]
            elif line == 1:  # Δ% Percent difference
                if entry and stack:
                    base = stack[0]
                    evaluate2(lambda x, y: (y-x) / x * 100, False)
                    push(base, False)
                    stack[0], stack[1] = stack[1], stack[0]
                elif not entry and len(stack) >= 2:
                    base = stack[1]
                    evaluate2(lambda x, y: (y-x) / x * 100, False)
                    push(base, False)
                    stack[0], stack[1] = stack[1], stack[0]
            elif line == 2:  # %T Percent of total
                if entry and stack:
                    base = stack[0]
                    evaluate2(lambda x, y: y/x * 100, False)
                    push(base, False)
                    stack[0], stack[1] = stack[1], stack[0]
                elif not entry and len(stack) >= 2:
                    base = stack[1]
                    evaluate2(lambda x, y: y/x * 100, False)
                    push(base, False)
                    stack[0], stack[1] = stack[1], stack[0]
            elif line == 3:  # ±% Evolution, or markup on cost
                evaluate2(lambda x, y: x + x*y / 100)
            elif line == 4:  # MU%P Markup on price, or margin
                evaluate2(lambda x, y: (y-x) / y * 100)
            quit = True; display()
        if keydown(5): quit = True; display()  # BACK


# MAIN PROGRAM

# Original state: dynamic empty stack, no lastX, empty entry command line, angles in degrees
fixed = False; stack = []
lastx = ""; entry = ""
degrees = True

display()
while True:

    # Characters the user may enter on the command line
    if keydown(48): entry += "0"; draw_command()
    elif keydown(42): entry += "1"; draw_command()
    elif keydown(43): entry += "2"; draw_command()
    elif keydown(44): entry += "3"; draw_command()
    elif keydown(36): entry += "4"; draw_command()
    elif keydown(37): entry += "5"; draw_command()
    elif keydown(38): entry += "6"; draw_command()
    elif keydown(30): entry += "7"; draw_command()
    elif keydown(31): entry += "8"; draw_command()
    elif keydown(32): entry += "9"; draw_command()
    elif keydown(49):
        if not entry: entry = "0."
        else: entry += "."
        draw_command()
    elif keydown(50):
        if not entry: entry = "1e"
        else: entry += "e";
        draw_command()
    elif keydown(27):
        if entry: push(entry); entry = ""; draw_command()
        push(pi)
        draw_stack(8, 0.2)

    # RPN-specific
    elif keydown(14):  # XNT
        fixed = not fixed  # Switch between fixed or dynamic stack
        if fixed:  # Max 4 levels, equal to 0 if not used
            for level in range(4, len(stack)): stack.pop()
            for level in range(4 - len(stack)): stack.append(0)
        else:  # All levels should be empty if not used
            while stack[len(stack) - 1] == 0:
                stack.pop()
                if stack == [0]: stack = []; break
        display()
    elif keydown(51):  # Ans
        try:
            if entry: stack.insert(0, python_int(entry)); entry = ""  # LastX
        except Exception as message: draw_error(message)
        else: push(lastx); display()
    elif keydown(4) or keydown(52):  # OK/EXE
        if entry: push(entry); entry = ""; display()  # ENTER
        elif stack: push(stack[0]); draw_stack(8, 0.2)  # DUP
    elif keydown(17):  # BACKSPACE
        if not entry and stack: drop(); display(False)  # DROP stack top level
        else: entry = entry[:-1]; draw_command()  # CLEAR last character on command line
    elif keydown(33):  # (: (n) ROLL down
        if entry:
            try: pos = float(entry)
            except Exception as message: draw_error(message)
            else:
                if pos == int(pos) and int(pos) <= len(stack):
                    entry = ""; draw_command()
                    stack.insert(int(pos-1), stack.pop(0))
                    draw_stack(int(pos))
                else:
                    draw_error("invalid stack level number")
        elif len(stack) >= 2: stack.append(stack.pop(0)); draw_stack(8, 0.2)
    elif keydown(34):  # ): SWAP
        if entry: push(entry); entry = ""
        if len(stack) >= 2: stack[0], stack[1] = stack[1], stack[0]
        draw_stack(2, 0.2)
    elif keydown(1):  # UP: selection of levels if stack is dynamic
        if not fixed and stack:
            level = 0; draw_register(level, 0.2, True)
            while level >= 0:
                if keydown(1) and level < len(stack) - 1:  # UP
                    draw_register(level)
                    draw_register(level + 1, 0.2, True)
                    level += 1
                if keydown(2):  # DOWN
                    draw_register(level)
                    if level > 0: draw_register(level - 1, 0.2, True)
                    level -= 1
                if keydown(17):  # BACKSPACE: DROP
                    stack = stack[level+1:]; level = -1
                if keydown(4) or keydown(52):  # OK/EXE: PICK
                    stack[0] = stack[level]; level = -1
                if keydown(33):  # (: ROLL down
                    stack.insert(int(level), stack.pop(0)); level = -1
                if keydown(5): level = -1  # BACK: exit selection mode
            display(False)

    # Unary operators
    elif keydown(18):
        if not entry and not stack: push(exp(1)); draw_register(0, 0.2)
        else: evaluate1(lambda x: exp(x))
    elif keydown(19): evaluate1(lambda x: log(x))
    elif keydown(20): evaluate1(lambda x: log10(x))
    elif keydown(21): evaluate1(lambda x: 1/x)  # INVERSE
    elif keydown(22): evaluate1(lambda x: -x)  # CHS
    elif keydown(24):
        if degrees: evaluate1(lambda x: sin(x * pi / 180))
        else: evaluate1(lambda x: sin(x))
    elif keydown(25):
        if degrees: evaluate1(lambda x: cos(x * pi / 180))
        else: evaluate1(lambda x: cos(x))
    elif keydown(26):
        if degrees: evaluate1(lambda x: tan(x * pi / 180))
        else: evaluate1(lambda x: tan(x))
    elif keydown(28): evaluate1(lambda x: sqrt(x))
    elif keydown(29): evaluate1(lambda x: x*x)

    # Binary operators
    elif keydown(23): evaluate2(lambda x, y: x ** y)
    elif keydown(39): evaluate2(lambda x, y: x * y)
    elif keydown(40): evaluate2(lambda x, y: x / y)
    elif keydown(45): evaluate2(lambda x, y: x + y)
    elif keydown(46):
        if entry and entry[-1] == "e" and entry.count("-") == 0: entry += "-"
        else: evaluate2(lambda x, y: x - y)

    # SHIFT operators
    elif keydown(12):  # SHIFT
        pressed = False; draw_string("shift", 270, 0, (255,254,255), (255,181,0)); sleep(0.2)
        while not pressed:
            if keydown(17):  # BACKSPACE: CLEAR
                stack = [0, 0, 0, 0] if fixed else []
                entry = ""; pressed = True; display()
            if keydown(24):
                if degrees: evaluate1(lambda x: asin(x) * 180 / pi)
                else: evaluate1(lambda x: asin(x))
                pressed = True
            if keydown(25):
                if degrees: evaluate1(lambda x: acos(x) * 180 / pi)
                else: evaluate1(lambda x: acos(x))
                pressed = True
            if keydown(26):
                if degrees: evaluate1(lambda x: atan(x) * 180 / pi)
                else: evaluate1(lambda x: atan(x))
                pressed = True
            if keydown(33):  # (: ROLL up
                if entry:
                    try: pos = float(entry)
                    except Exception as message: draw_error(message)
                    else:
                        entry = ""
                        if pos == int(pos) and int(pos) <= len(stack):
                            stack.insert(0, stack.pop(int(pos)-1))
                        else: draw_error("invalid stack level number")
                    display()
                elif len(stack) >= 2: stack.insert(0, stack.pop())
                pressed = True
            if keydown(40): evaluate1(lambda x: 1/x); pressed = True  # DIVISION
            if keydown(46): evaluate1(lambda x: -x); pressed = True  # MINUS
            if keydown(51):  # Ans: OVER
                if fixed or len(stack) >= 2: push(stack[1])
                pressed = True
            if keydown(12): pressed = True  # SHIFT
        display(False)

    # ALPHA operators
    elif keydown(13):  # ALPHA
        pressed = False; draw_string("alpha", 270, 0, (255,254,255), (255,181,0)); sleep(0.2)
        while not pressed:
            if keydown(6):  # HOME
                pressed = True; display(False); draw_error(__version__)
            if keydown(17):  # %: Percentage functions
                pressed = True; display(False); percentage()
            if keydown(20):  # C: Fahrenheit to Celsius
                evaluate1(lambda x: (x-32) * 5/9); pressed = True
            if keydown(21):  # D: Set angles to degrees
                degrees = True; pressed = True; display(False)
            if keydown(23):  # F: Celsius to Fahrenheit
                evaluate1(lambda x: x * 9/5 + 32); pressed = True
            if keydown(25):  # H
                evaluate1(lambda x: hms(x)); pressed = True
            if keydown(33):  # P: Prime factorisation
                if not entry and stack:
                    try: push(prime_facto(float(stack[0])), False)
                    except Exception as message: draw_error(message)
                    display(False)
                elif entry:
                    if float(entry) != int(float(entry)): draw_error("math domain error")
                    else: push(float(entry)); push(prime_facto(float(entry)), False); entry = ""
                    display()
                pressed = True
            if keydown(36):  # R: Set angles to radians
                degrees = False; pressed = True; display(False)
            if keydown(48):  # ?
                if not entry: push(random())
                pressed = True; display(False)
            if keydown(49): evaluate1(lambda x: factorial(x)); pressed = True
            if keydown(13): pressed = True; display(False)  # ALPHA

    elif keydown(16): toolbox()
    elif keydown(15): varbox()
    elif keydown(6): quit()  # HOME

    blink_cursor()
