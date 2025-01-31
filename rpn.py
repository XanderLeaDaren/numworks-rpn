__author__ = "Alexandre ANDRÉ"
__version__ = "2025-01-31 T 16:28 UTC+1"

from math import exp, log, log10, sin, asin, cos, acos, tan, atan, pi, sqrt
from math import degrees, radians, ceil
from time import sleep, monotonic
from random import random

from ion import *
from kandinsky import color, draw_string, fill_rect

import micropython as mp
mp.kbd_intr(-1)  # Disable KeyboardInterrupt


###############################################################
# Constants: screen size and colors from the NumWorks palette #
###############################################################

XMAX = 320
YMAX = 222

BOX_WIDTH = 266

BLACK = color(0, 0, 0)
MGREY = color(164, 165, 164)
DGREY = color(180, 180, 180)
LGREY = color(238, 238, 238)
WHITE = color(255, 254, 255)

LBLUE = color(245, 250, 255)
YELLOW = color(255, 181, 0)

SELECT_BG = color(214, 213, 231)

SEPARATOR = color(223, 217, 222)

TITLE_BG = color(108, 99, 115)
TITLE_BORDER = color(65, 64, 65)


# Original state: dynamic empty stack, no lastX, empty entry command line
fixed = False
stack = []
lastx = ""
entry = ""


#############################################################################
# Functions specific to Reverse Polish Notation, stack manipulation, Python #
#############################################################################

def python_int(foo):
    """Python-specific: keep integers instead of floats if possible."""
    foo = float(foo)
    try:
        integer = int(foo)
    except OverflowError as message:
        draw_error(message)
    else:
        if foo == integer:
            foo = integer
        return foo

def drop():
    """Drop the stack top level, keep T level value if fixed stack mode."""
    stack.pop(0)
    if fixed: stack.append(stack[2])

def push(foo):
    """Push something onto the stack."""
    try: top = python_int(foo)
    except Exception as message: draw_error(message)
    else:
        global lastx
        lastx = foo
        stack.insert(0, top)

def evaluate1(operation):
    """Evaluate unary operations."""
    global entry, stack, lastx
    if not entry and stack:
        try: result = operation(stack[0])
        except Exception as message: draw_error(message)
        else:
            lastx = stack[0]
            stack[0] = python_int(result)
    elif entry:
        try: result = operation(float(entry))
        except Exception as message: draw_error(message)
        else:
            lastx = entry
            stack.insert(0, python_int(result))
            entry = ""
    display()

def evaluate2(operation):
    """Evaluate binary operations."""
    global entry, stack, lastx
    if not entry and len(stack) >= 2:
        try: result = operation(stack[1], stack[0])
        except Exception as message: draw_error(message)
        else:
            lastx = stack[0]
            stack[1] = python_int(result)
            drop()
    elif entry and stack:
        try: result = operation(stack[0], float(entry))
        except Exception as message: draw_error(message)
        else:
            lastx = entry
            stack[0] = python_int(result)
            entry = ""
    display()


#################################################################
# Mathematical functions mapped to some keys or used in dialogs #
#################################################################

def factorial(n):
    """Compute the factorial of n, for positive whole numbers."""
    if float(n) != int(n):
        raise Exception("math domain error")
    else:
        prod = 1
        max = n
        while max > 0:
            prod *= max
            max -= 1
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

def med(data):
    """Determine the median of a list of numbers."""
    s = sorted(data); n = len(s)
    if n % 2 == 1: return s[n//2]
    else: return (s[n//2 - 1] + s[n//2]) / 2

def quartile(data, q):
    """Determine the 1st or 3rd quartile of a list of numbers."""
    s = sorted(data)
    n = len(s)
    i = ceil(q/4 * n)
    return s[i - 1]

def stdev(s):
    """Calculate the standard deviation of a list of numbers."""
    m = sum(s) / len(s); v = 0
    for i in s: v += (i - m)**2
    return sqrt(v / len(s))


######################################
# Graphical User Interface functions #
######################################

def display():
    """Refresh the whole screen."""
    # Depending on stack style, nb of lines displayed, level names, text shift
    if fixed:
        name = ["X:", "Y:", "Z:", "T:"]
        levels = 4
        shift = 13
    else:
        name = ["1:", "2:", "3:", "4:", "5:", "6:", "7:", "8:"]
        levels = 8
        shift = 3
    # Height (pixels) of lines displayed (including stack and command line)
    h = YMAX // (levels+1)
    # On fixed stack, drop oldest level if not displayable
    if fixed and len(stack) > levels: stack.pop()
    # Odd or even line backgrounds
    fill_rect(0, 0, XMAX, YMAX, LBLUE)
    if fixed or len(stack) >= 8: fill_rect(0, 0, XMAX, h, WHITE)
    if fixed or len(stack) >= 6: fill_rect(0, 2*h, XMAX, h, WHITE)
    if not fixed and len(stack) >= 4: fill_rect(0, 4*h, XMAX, h, WHITE)
    if not fixed and len(stack) >= 2: fill_rect(0, 6*h, XMAX, h, WHITE)
    # Display stack levels
    for line in range(len(stack)):
        x_value = 310 - 10*len(str(stack[line]))
        y = h * (levels-1-line) + shift
        bg_color = LBLUE if line % 2 == 0 else WHITE
        draw_string(name[line], 10, y, BLACK, bg_color)
        draw_string(str(stack[line]), x_value, y, BLACK, bg_color)
    # Entry command line
    fill_rect(0, levels*h, XMAX, 1, SEPARATOR)
    fill_rect(0, levels*h + 1, XMAX, YMAX - (levels-1)*h, WHITE)
    y = YMAX - 23 if not fixed else YMAX - 30
    draw_string(entry, 5, y, BLACK, WHITE)
    sleep(0.2)


def blink_cursor():
    x = 5 + 10*len(entry)
    y = YMAX - 24 if not fixed else YMAX - 31
    color = BLACK if int(monotonic()) % 2 == 0 else WHITE
    fill_rect(x, y, 1, 18, color)


def select_stack(level):
    """Highlight selected stack level, if any."""
    h = YMAX // 9
    x = 310 - 10 * len(str(stack[level]))
    y = h * (7 - level) + (h - 18) // 2
    draw_string(str(stack[level]), x, y, BLACK, SELECT_BG)


def draw_error(text):
    """Display an error or exception in a black dialog box."""
    text = str(text)
    width = 10*len(text) + 32
    x = (XMAX - width) // 2
    fill_rect(x, 89, width, 44, BLACK)
    draw_string(text, x + 16, 102, WHITE, BLACK)
    sleep(0.5)
    pressed = False
    while not pressed:
        for i in range(53):
            if keydown(i): pressed = True
    display()


def draw_item(line, items, descriptions, selected=False):
    """Display a menu item line, eventually on a selected background."""
    n = len(items)
    h = 174 // n
    y = 50 + line * h
    y_txt = (h - 18) // 2
    background = SELECT_BG if selected else WHITE
    fill_rect(28, y - 1, 264, h - 1, background)
    draw_string(items[line], 35, y + y_txt, BLACK, background)
    x_desc = 285 - 10*len(descriptions[line])
    draw_string(descriptions[line], x_desc, y + y_txt, MGREY, background)


def draw_menu(items, descriptions):
    """Display all items and descriptions menu inside a dialog box."""
    fill_rect(27, 48, BOX_WIDTH, 174, LGREY)
    fill_rect(28, 49, BOX_WIDTH - 2, 173, WHITE)
    n = len(items)
    h = 174 // n
    for i in range(len(items)):
        draw_item(i, items, descriptions)
        y = 50 + i * h
        fill_rect(28, y - 2, 264, 1, LGREY)
    fill_rect(28, 48 + len(items) * h, 264, 1, LGREY)


def varbox():
    """Display a dialog with functions mapped to ALPHA + some key."""
    keys = ["D", "R", "C", "F", "H", "P", "S", "?"]
    desc = ["Convert rad to °",
            "Convert ° to rad",
            "Convert °F to °C",
            "Convert °C to °F",
            "Convert hrs to h:min",
            "Prime factorisation",
            "Statistics",
            "Random number in [0,1)"]
    fill_rect(27, 27, BOX_WIDTH, 21, TITLE_BORDER)
    fill_rect(28, 28, BOX_WIDTH - 2, 19, TITLE_BG)
    title = "Alpha shortcuts"
    x = (XMAX - 10*len(title)) // 2
    draw_string(title, x, 28, WHITE, TITLE_BG)
    draw_menu(keys, desc)
    sleep(0.5)
    pressed = False
    while not pressed:
        for i in [KEY_OK, KEY_VAR, KEY_BACK]:
            if keydown(i): pressed = True
    display()


def toolbox():
    """Display a dialog with common RPN functions and their mappings."""
    keys = [" xnt",
            "  (",
            "  )",
            " Ans",
            "[shift]Ans",
            "[shift] ÷",
            "[shift] -"]
    desc = ["Fixed/dynamic stack",
            "ROLL (n)/all levels",
            "SWAP last two levels",
            "Copy last X value",
            "Copy 2nd level",
            "Inverse",
            "Change signs"]
    fill_rect(27, 27, BOX_WIDTH, 21, TITLE_BORDER)
    fill_rect(28, 28, BOX_WIDTH - 2, 19, TITLE_BG)
    title = "Hotkeys"
    x = (XMAX - 10*len(title)) // 2
    draw_string(title, x, 28, WHITE, TITLE_BG)
    draw_menu(keys, desc)
    sleep(0.5)
    pressed = False
    while not pressed:
        for i in [KEY_OK, KEY_TOOLBOX, KEY_BACK]:
            if keydown(i): pressed = True
    display()


def percentage():
    """Display a dialog with common percentage functions."""
    items = ["%", "Δ%", "%T", "±%", "MU%P"]
    descriptions = ["Percentage of X",
            "Percent difference",
            "Percent of total",
            "Evolution or markup",
            "Markup on price"]
    fill_rect(27, 27, BOX_WIDTH, 21, TITLE_BORDER)
    fill_rect(28, 28, BOX_WIDTH - 2, 19, TITLE_BG)
    title = "Percentage"
    x = (XMAX - 10*len(title)) // 2
    draw_string(title, x, 28, WHITE, TITLE_BG)
    draw_menu(items, descriptions)
    line = 0
    quit = False
    draw_item(0, items, descriptions, True)
    while not quit:
        sleep(0.13)
        if keydown(KEY_UP) and line > 0:
            draw_item(line, items, descriptions)
            draw_item(line - 1, items, descriptions, True)
            line -= 1
        if keydown(KEY_DOWN) and line < len(items) - 1:
            draw_item(line, items, descriptions)
            draw_item(line + 1, items, descriptions, True)
            line += 1
        if keydown(KEY_OK) or keydown(KEY_EXE):
            if line == 0:
                if entry and stack:
                    base = stack[0]
                    evaluate2(lambda x, y: x*y / 100)
                    push(base)
                    stack[0], stack[1] = stack[1], stack[0]
                elif not entry and len(stack) >= 2:
                    base = stack[1]
                    evaluate2(lambda x, y: x*y / 100)
                    push(base)
                    stack[0], stack[1] = stack[1], stack[0]
            elif line == 1:
                evaluate2(lambda x, y: (y - x) / x * 100)
            elif line == 2:
                if entry and stack:
                    base = stack[0]
                    evaluate2(lambda x, y: y/x * 100)
                    push(base)
                    stack[0], stack[1] = stack[1], stack[0]
                elif not entry and len(stack) >= 2:
                    base = stack[1]
                    evaluate2(lambda x, y: y/x * 100)
                    push(base)
                    stack[0], stack[1] = stack[1], stack[0]
            elif line == 3:
                evaluate2(lambda x, y: x + x*y / 100)
            elif line == 4:
                evaluate2(lambda x, y: (y - x) / y * 100)
            quit = True
            display()
        if keydown(KEY_BACK):
            quit = True
            display()


def statistics():
    """Display a dialog with statistic informations on stack values."""
    desc = ["Minimum",
            "1st quartile",
            "Median",
            "3rd quartile",
            "Maximum",
            "Mean",
            "Std deviation",
            "Nb of data",
            "Sum of values"]
    stat = ["Min", "Q1", "Med", "Q3", "Max", "x", "σ", "n", "Σx"]
    values = [
            min(stack),
            quartile(stack, 1),
            med(stack),
            quartile(stack, 3),
            max(stack),
            sum(stack) / len(stack),
            stdev(stack),
            len(stack),
            sum(stack)]
    fill_rect(27, 27, BOX_WIDTH, 21, TITLE_BORDER)
    fill_rect(28, 28, BOX_WIDTH - 2, 19, TITLE_BG)
    title = "Statistics"
    x = (XMAX - 10*len(title)) // 2
    draw_string(title, x, 28, WHITE, TITLE_BG)
    # Dialog contents
    fill_rect(27, 48, BOX_WIDTH, 174, LGREY)
    fill_rect(28, 49, BOX_WIDTH - 2, 173, WHITE)
    # Line backgrounds
    for i in range(len(stat)):
        bg_color = LBLUE if i % 2 == 0 else WHITE
        y = 50 + 19*i
        fill_rect(28, y - 1, 264, 19, bg_color)
        draw_string(desc[i], 162 - 10*len(desc[i]), y, BLACK, bg_color)
        draw_string(stat[i], 185 - 5*len(stat[i]), y, DGREY, bg_color)
        txt = str(values[i])[0:8]
        draw_string(txt, 285 - 10*len(txt), y, BLACK, bg_color)
    # Workaround: draw a bar over x for the missing "mean" glyph
    fill_rect(180, 148, 10, 1, DGREY)
    # Separators for more convenient reading
    fill_rect(28, 49 + 19*5, 264, 1, DGREY)
    fill_rect(28, 49 + 19*7, 264, 1, DGREY)
    sleep(0.5)
    pressed = False
    while not pressed:
        for i in [KEY_OK, KEY_BACK]:
            if keydown(i): pressed = True
    display()


#######################################################
# Main program: infinite loop checking for key inputs #
#######################################################

display()
while True:

    # Characters the user may enter on the command line
    if keydown(KEY_ZERO): entry += "0"; display()
    elif keydown(KEY_ONE): entry += "1"; display()
    elif keydown(KEY_TWO): entry += "2"; display()
    elif keydown(KEY_THREE): entry += "3"; display()
    elif keydown(KEY_FOUR): entry += "4"; display()
    elif keydown(KEY_FIVE): entry += "5"; display()
    elif keydown(KEY_SIX): entry += "6"; display()
    elif keydown(KEY_SEVEN): entry += "7"; display()
    elif keydown(KEY_EIGHT): entry += "8"; display()
    elif keydown(KEY_NINE): entry += "9"; display()
    elif keydown(KEY_DOT):
        if not entry: entry = "0."
        else: entry += "."
        display()
    elif keydown(KEY_EE):
        if not entry: entry = "1e"
        else: entry += "e";
        display()
    elif keydown(KEY_PI) and not entry: push(pi); display()

    # RPN-specific
    elif keydown(KEY_XNT):
        fixed = not fixed  # Switch between fixed or dynamic stack
        if fixed:  # Max 4 levels, equal to 0 if not used
            for level in range(4, len(stack)):
                stack.pop()
            for level in range(4 - len(stack)):
                stack.append(0)
        else:  # All levels should be empty if not used
            while stack[len(stack) - 1] == 0:
                stack.pop()
                if stack == [0]:
                    stack = []
                    break
        display()
    elif keydown(KEY_ANS):
        try:
            if entry: stack.insert(0, python_int(entry))  # LastX
        except Exception as message: draw_error(message)
        else: push(lastx); display()
    elif keydown(KEY_EXE) or keydown(KEY_OK):
        if entry: push(entry); entry = ""  # ENTER
        elif stack: dup = stack[0]; push(dup)  # DUP
        display()
    elif keydown(KEY_BACKSPACE):
        if not entry and stack: drop()  # DROP stack top level
        else: entry = entry[:-1]  # CLEAR last character on command line
        display()
    elif keydown(KEY_LEFTPARENTHESIS):  # (n) ROLL down
        if entry:
            try: pos = float(entry)
            except Exception as message: draw_error(message)
            else:
                entry = ""
                if pos == int(pos) and int(pos) <= len(stack):
                    stack.insert(int(pos-1), stack.pop(0))
                else:
                    draw_error("invalid stack level number")
        elif len(stack) >= 2: stack.append(stack.pop(0))
        display()
    elif keydown(KEY_RIGHTPARENTHESIS):  # SWAP
        if entry:
            push(entry)
            entry = ""
        if len(stack) >= 2:
            swap = stack[0]
            stack[0] = stack[1]
            stack[1] = swap
        display()
    elif keydown(KEY_UP):  # Selection of levels if stack is dynamic
        if not fixed and stack:
            level = 0
            select_stack(level)
            sleep(0.2)
            while level >= 0:
                if keydown(KEY_UP) and level < len(stack) - 1:
                    level += 1
                    display()
                    select_stack(level)
                if keydown(KEY_DOWN):
                    level -= 1
                    display()
                    select_stack(level)
                # DROP first levels
                if keydown(KEY_BACKSPACE):
                    stack = stack[level+1:]
                    level = -1
                # PICK actual level and copy to stack top
                if keydown(KEY_OK) or keydown(KEY_EXE):
                    stack[0] = stack[level]
                    level = -1
                # Exit selection mode
                if keydown(KEY_BACK): level = -1
            display()

    # Unary operators
    elif keydown(KEY_EXP):
        if not entry and not stack: push(exp(1)); display()
        else: evaluate1(lambda x: exp(x))
    elif keydown(KEY_LN): evaluate1(lambda x: log(x))
    elif keydown(KEY_LOG): evaluate1(lambda x: log10(x))
    elif keydown(KEY_SINE): evaluate1(lambda x: sin(x))
    elif keydown(KEY_COSINE): evaluate1(lambda x: cos(x))
    elif keydown(KEY_TANGENT): evaluate1(lambda x: tan(x))
    elif keydown(KEY_SQRT): evaluate1(lambda x: sqrt(x))
    elif keydown(KEY_SQUARE): evaluate1(lambda x: x*x)

    # Binary operators
    elif keydown(KEY_POWER): evaluate2(lambda x, y: x ** y)
    elif keydown(KEY_MULTIPLICATION): evaluate2(lambda x, y: x * y)
    elif keydown(KEY_DIVISION): evaluate2(lambda x, y: x / y)
    elif keydown(KEY_PLUS): evaluate2(lambda x, y: x + y)
    elif keydown(KEY_MINUS):
        if entry and entry[-1] == "e" and entry.count("-") == 0: entry += "-"
        else: evaluate2(lambda x, y: x - y)

    # SHIFT operators
    elif keydown(KEY_SHIFT):
        pressed = False
        draw_string("shift", 270, 0, WHITE, YELLOW)
        sleep(0.2)
        while not pressed:
            if keydown(KEY_BACKSPACE):  # CLEAR
                if fixed: stack = [0, 0, 0, 0]
                else: stack = []
                entry = ""
                pressed = True
                display()
            if keydown(KEY_SINE):
                evaluate1(lambda x: asin(x))
                pressed = True
            if keydown(KEY_COSINE):
                evaluate1(lambda x: acos(x))
                pressed = True
            if keydown(KEY_TANGENT):
                evaluate1(lambda x: atan(x))
                pressed = True
            if keydown(KEY_LEFTPARENTHESIS):  # ROLL up
                if entry:
                    try: pos = float(entry)
                    except Exception as message: draw_error(message)
                    else:
                        entry = ""
                        if pos == int(pos) and int(pos) <= len(stack):
                            stack.insert(0, stack.pop(int(pos)-1))
                        else: draw_error("invalid stack level number")
                elif len(stack) >= 2: stack.insert(0, stack.pop())
                pressed = True
                display()
            if keydown(KEY_DIVISION):
                evaluate1(lambda x: 1/x)
                pressed = True
            if keydown(KEY_MINUS):
                evaluate1(lambda x: -x)
                pressed = True
            if keydown(KEY_ANS):  # OVER
                if fixed or len(stack) >= 2: push(stack[1])
                pressed = True
                display()
            if keydown(KEY_SHIFT):  # Quit shift mode
                pressed = True
                display()

    # ALPHA operators
    elif keydown(KEY_ALPHA):
        pressed = False
        draw_string("alpha", 270, 0, WHITE, YELLOW)
        sleep(0.2)
        while not pressed:
            if keydown(KEY_HOME):
                pressed = True
                display()
                draw_error(__version__)
            if keydown(KEY_BACKSPACE):  # %: Percentage functions
                pressed = True
                display()
                percentage()
            if keydown(KEY_LOG):  # C: Fahrenheit to Celsius
                evaluate1(lambda x: (x-32) * 5/9)
                pressed = True
            if keydown(KEY_IMAGINARY):  # D: radians to degrees
                evaluate1(lambda x: degrees(x))
                pressed = True
            if keydown(KEY_POWER):  # F: Celsius to Fahrenheit
                evaluate1(lambda x: x * 9/5 + 32)
                pressed = True
            if keydown(KEY_COSINE):  # H: dec to H:MMSS
                evaluate1(lambda x: hms(x))
                pressed = True
            if keydown(KEY_LEFTPARENTHESIS):  # P: Prime factorisation
                if not entry and stack:
                    try: push(prime_facto(float(stack[0])))
                    except Exception as message: draw_error(message)
                elif entry:
                    if float(entry) != int(float(entry)):
                        draw_error("math domain error")
                    else:
                        push(float(entry))
                        push(prime_facto(float(entry)))
                        entry = ""
                pressed = True
                display()
            if keydown(KEY_FOUR):  # R: degrees to radians
                evaluate1(lambda x: radians(x))
                pressed = True
            if keydown(KEY_FIVE):  # S: Statistics
                pressed = True
                if not fixed and len(stack) >= 2:
                    statistics()
                display()
            if keydown(KEY_ZERO):  # ?: Random number in [0;1[
                if not entry: push(random())
                pressed = True
                display()
            if keydown(KEY_DOT):  # !: factorial
                evaluate1(lambda x: factorial(x))
                pressed = True
            if keydown(KEY_ALPHA):  # Quit alpha mode
                pressed = True
                display()

    elif keydown(KEY_TOOLBOX): toolbox()  # RPN Hotkeys
    elif keydown(KEY_VAR): varbox()  # Alpha shortcuts
    elif keydown(KEY_HOME): quit()  # Back to NumWorks homescreen

    blink_cursor()

    # Idle timeout before next infinite loop
    sleep(0.06)
