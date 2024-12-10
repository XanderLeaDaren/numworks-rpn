from ion import *
from kandinsky import *
from math import *
from random import *
from time import *

# GUI: refreshes whole screen
def display():
    # STACK: number of levels displayed
    if fixed:
        levels = 5
    else:
        levels = 8
    # Fixed stack: drops oldest level if not displayable
    if fixed and len(stack) > levels:
        stack.pop()
    # GUI: height (pixels) of lines displayed (stack + entry)
    h = 222 // (levels+1)
    # GUI: white background
    fill_rect(0,0, 320,222, color(255,254,255))
    # GUI: odd/even line backgrounds
    if fixed or (not fixed and len(stack)>=7):
        fill_rect(0,1*h, 320,h, color(245,250,255))
    if fixed or (not fixed and len(stack)>=5):
        fill_rect(0,3*h, 320,h, color(245,250,255))
    if not fixed and len(stack) >= 3:
        fill_rect(0,5*h, 320,h, color(245,250,255))
    if not fixed and len(stack) >= 1:
        fill_rect(0,7*h, 320,h, color(245,250,255))  
    # GUI: displays stack level names
    if fixed:
        shift = 9
    else:
        shift = 3
    if fixed:
        name = ["X:", "Y:", "Z:", "T:", "L:"]
        for line in range(levels):
            draw_string(name[line], 10, h*(levels-1-line) + shift)
    else:
        for line in range(min(levels, len(stack))):
            draw_string(str(line+1)+":", 10, h*(levels-1-line) + shift)
    # GUI: displays stack levels contents
    for line in range(len(stack)):
        draw_string(str(stack[line]), 310 - 10*len(str(stack[line])), h*(levels-1-line) + shift)
    # GUI: entry field separation line
    fill_rect(0,levels*h, 320,1, color(223,217,222))
    # GUI: entry field contents
    draw_string(entry, 10, levels*h + shift + shift%8)
    sleep(0.2)

# Python-specific: keep integers and not floats if possible
def python_int(foo):
    foo = float(foo)
    if foo == int(foo):
        foo = int(foo)
    return foo

# Dropping something from the stack
def drop():
    stack.pop(0)
    # On fixed stack: L-level keeps its value
    if fixed:
        stack.append(stack[3])

# Pushing something to the stack
def push(foo):
    stack.insert(0, python_int(foo))

# Unary operations
def evaluate1(operation):
    global entry, stack
    if not entry and stack:
        stack[0] = python_int(operation(stack[0]))
    elif entry:
        push(operation(float(entry)))
        entry = ""
    display()

# Binary operations
def evaluate2(operation):
    global entry, stack
    if not entry and len(stack)>=2:
        stack[1] = python_int(operation(stack[1], stack[0]))
        drop()
    elif entry and stack:
        stack[0] = python_int(operation(stack[0], float(entry)))
        entry = ""
    display()

# Converting decimal to sexagesimal
def hms(dec):
    hours = int(dec)
    minutes = (dec-hours) * 60
    return hours + minutes/100

# Finding the lowest prime divisor
def prime_facto(n):
    div = 2
    while div**2 <= n:
       if n % div == 0:
           return div
       div += 1
    return 1

# Hotkeys recap toolbox
def toolbox():
    # Title
    fill_rect(27,26, 266,22, color(65,64,65))
    fill_rect(28,27, 264,20, color(106,101,115))
    draw_string(" HOTKEYS ", 115,28)
    # Contents
    fill_rect(27,48, 266,174, color(238,238,238))
    fill_rect(28,49, 264,173, color(255,254,255))
    draw_string("xnt: fixed/dynamic stack", 35,52)
    fill_rect(28,74, 264,1, color(238,238,238))
    draw_string("D: rad → deg     i : 1/x", 35,80)
    draw_string("R: deg → rad     , :  ±", 35,100)
    fill_rect(28,124, 264,1, color(238,238,238))
    draw_string("C: °F → °C       ( : ROLL", 35,130)
    draw_string("F: °C → °F       ) : SWAP", 35,150)
    fill_rect(28,174, 264,1, color(238,238,238))
    draw_string("H: dec → h:min   ? : rand", 35,180)
    draw_string("P: prime fact.", 35,200)
    # Closing the Hotkeys toolbox
    sleep(0.5)
    while not keydown(KEY_OK) and not keydown(KEY_TOOLBOX):
        None
    display()

################################################

# Original state: dynamic stack, empty entry field
fixed = False
stack = []
entry = ""

# Key pressed?
display()
while True:
    # Type in entry
    if keydown(KEY_ZERO):
        entry += "0"
        display()
    elif keydown(KEY_ONE):
        entry += "1"
        display()
    elif keydown(KEY_TWO):
        entry += "2"
        display()
    elif keydown(KEY_THREE):
        entry += "3"
        display()
    elif keydown(KEY_FOUR):
        entry += "4"
        display()
    elif keydown(KEY_FIVE):
        entry += "5"
        display()
    elif keydown(KEY_SIX):
        entry += "6"
        display()
    elif keydown(KEY_SEVEN):
        entry += "7"
        display()
    elif keydown(KEY_EIGHT):
        entry += "8"
        display()
    elif keydown(KEY_NINE):
        entry += "9"
        display()
    elif keydown(KEY_DOT):
        entry += "."
        display()
    elif keydown(KEY_PI) and not entry:
        push(pi)
        display()
    
    # RPN-specific
    elif keydown(KEY_XNT): # Fixed or dynamic stack
        fixed = not fixed
        if fixed: # All levels should be 0 if not used
            for level in range(5 - len(stack)):
                stack.append(0)
        else: # All levels should be empty if not used
            while stack[len(stack) - 1] == 0:
                stack.pop()
                if stack == [0]:
                    stack = []
                    break
        display()
    elif keydown(KEY_EXE): # ENTER, DUP
        if entry:
            push(entry)
            entry = ""
        elif stack:
            dup = stack[0]
            push(dup)
        display()
    elif keydown(KEY_LEFTPARENTHESIS): # ROLL
        if entry:
            push(entry)
            entry = ""
        if len(stack) >= 2:
            stack.append(stack[0])
            stack.pop(0)
        display()
    elif keydown(KEY_RIGHTPARENTHESIS): # SWAP
        if entry:
            push(entry)
            entry = ""
        if len(stack) >= 2:
            swap = stack[0]
            stack[0] = stack[1]
            stack[1] = swap
        display()

    # Drops stack top or deletes cipher
    elif keydown(KEY_BACKSPACE):
        if not entry and stack:
            drop()
        else:
            entry = entry[:-1]
        display()

    # Unary operators
    elif keydown(KEY_EXP):
        # Inputs e
        if not entry and not stack:
            push(exp(1))
            display()
        else:
            evaluate1(lambda x: exp(x))
    elif keydown(KEY_LN):
        evaluate1(lambda x: log(x))
    elif keydown(KEY_LOG):
        evaluate1(lambda x: log10(x))
    elif keydown(KEY_SINE):
        evaluate1(lambda x: sin(x))
    elif keydown(KEY_COSINE):
        evaluate1(lambda x: cos(x))
    elif keydown(KEY_TANGENT):
        evaluate1(lambda x: tan(x))
    elif keydown(KEY_SQRT):
        evaluate1(lambda x: sqrt(x))
    elif keydown(KEY_SQUARE):
        evaluate1(lambda x: x*x)

    # SHIFT: reciprocal trig, CLEAR
    elif keydown(KEY_SHIFT):
        pressed = False
        draw_string("shift",270,0)
        while not pressed:
            if keydown(KEY_SINE):
                evaluate1(lambda x: asin(x))
                pressed = True
            if keydown(KEY_COSINE):
                evaluate1(lambda x: acos(x))
                pressed = True
            if keydown(KEY_TANGENT):
                evaluate1(lambda x: atan(x))
                pressed = True
            if keydown(KEY_BACKSPACE): # CLEAR
                if fixed:
                    stack = [0, 0, 0, 0, 0]
                else:
                    stack = []
                entry = ""
                pressed = True
                display()

    # Not labeled unary operators
    elif keydown(KEY_IMAGINARY):
        evaluate1(lambda x: 1/x)
    elif keydown(KEY_COMMA):
        evaluate1(lambda x: -x)

    # Binary operators
    elif keydown(KEY_PLUS):
        evaluate2(lambda x,y: x+y)
    elif keydown(KEY_MINUS):
        evaluate2(lambda x,y: x-y)
    elif keydown(KEY_MULTIPLICATION):
        evaluate2(lambda x,y: x*y)
    elif keydown(KEY_DIVISION):
        evaluate2(lambda x,y: x/y)
    elif keydown(KEY_POWER):
        evaluate2(lambda x,y: x**y)
    elif keydown(KEY_EE):
        evaluate2(lambda x,y: x * 10**y)

    # ALPHA operators
    elif keydown(KEY_ALPHA):
        pressed = False
        draw_string("alpha",270,0)
        while not pressed:
            if keydown(KEY_DOT): # !: factorial
                evaluate1(lambda x: factorial(int(x)))
                pressed = True
            if keydown(KEY_COSINE): # H: dec to HH:MM
                evaluate1(lambda x: hms(x))
                pressed = True
            if keydown(KEY_IMAGINARY): # D: radians to degrees
                evaluate1(lambda x: degrees(x))
                pressed = True
            if keydown(KEY_FOUR): # R: degrees to radians
                evaluate1(lambda x: radians(x))
                pressed = True
            if keydown(KEY_LOG): # C: Fahrenheit to Celsius
                evaluate1(lambda x: (x-32) * 5/9)
                pressed = True
            if keydown(KEY_POWER): # F: Celsius to Fahrenheit
                evaluate1(lambda x: x * 9/5 + 32)
                pressed = True
            if keydown(KEY_LEFTPARENTHESIS): # P: Prime factorisation
                if not entry and stack:
                    push(prime_facto(int(stack[0])))
                elif entry:
                    push(int(entry))
                    push(prime_facto(int(entry)))
                    entry = ""
                pressed = True
                display()
            if keydown(KEY_ZERO): # ?: Random number in [0;1[
                if not entry:
                    push(random())
                pressed = True
                display()
              
    # Hotkeys / Help
    elif keydown(KEY_TOOLBOX):
        toolbox()

    # Idle timeout before next inf. loop
    sleep(0.1)
