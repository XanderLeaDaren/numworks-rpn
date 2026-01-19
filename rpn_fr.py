__version__ = "2026-01-19 T 13:37 UTC+1"

from math import exp, log, log10, sin, asin, cos, acos, tan, atan, pi, sqrt
from time import sleep, monotonic
from random import random

from ion import keydown
from kandinsky import draw_string, fill_rect

from micropython import kbd_intr
kbd_intr(-1)  # Disable KeyboardInterrupt


# FONCTION SPÉCIFIQUES À LA NPI ET À PYTHON

def python_int(foo):
    """Propre à Python : si possible, utiliser des nombres entiers"""
    foo = float(foo)
    try: integer = int(foo)
    except OverflowError as message: draw_error(message)
    else:
        if foo == integer:
            foo = integer
        return foo

def python_trailing(value):
    # Retrait des 000000001 propres à Python, si possible
    if value.count(".") == 1 and (value[-1] == "1" or value[-1] == "2"):
        zeros = 0; last = -2
        while value[last] == "0": zeros += 1; last -= 1
        if zeros >= 7: value = value[:last+1]
    # Retrait des 9999999 propres à Python, si possible
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
    """Calcul avec opérateurs unaires"""
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
    """Calcul avec opérateurs binaires"""
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


# FONCTIONS MATHÉMATIQUES

def factorial(n):
    if float(n) != int(n):
        raise Exception("valeur interdite")
    else:
        prod = 1; max = n
        while max > 0: prod *= max; max -= 1
        return prod

def hms(dec):
    """Conversion de temps décimal en heures au format sexagésimal"""
    hours = int(dec)
    minutes = int((dec - hours) * 60)
    seconds = ((dec - hours) * 60 - minutes) * 60
    return hours + minutes/100 + seconds/10000

def prime_facto(n):
    """Trouve le plus petit diviseur premier d’un nombre entier n"""
    if float(n) != int(n):
        raise Exception("valeur interdite")
    else:
        div = 2
        while div**2 <= n:
            if n % div == 0: return div
            div += 1
        return 1


# FONCTIONS D'AFFICHAGE

def draw_register(level, timeout=0, selected=False):
    """Affiche le registre de la pile demandé sur fond correct et bonne heauteur de ligne"""
    if fixed:
        height = 46; name = ("X:", "Y:", "Z:", "T:")
    else:
        height = 23; name = ("1:", "2:", "3:", "4:", "5:", "6:", "7:", "8:")
    bg_color = (245,250,255) if level % 2 == 0 else (255,254,255)
    bg_text = (214,213,231) if selected else bg_color
    y_text = 185 - (level+1)*height + (height - 18) // 2
    fill_rect(0, 184 - (level+1)*height, 320, height, bg_color)
    draw_string(name[level], 10, y_text, (0,0,0), bg_color)
    if fixed:
        x = 40 if stack[level] >= 0 else 30
        draw_string("{:.21f}".format(stack[level]), x, y_text, (0,0,0), bg_text)
    else:
        if stack[level] > 10**25:  # Notation scientifique pour conserver nombres à l’écran
            value = "{:.20e}".format(stack[level])
        else:
            value = python_trailing(str(stack[level]))
        draw_string(value, 310 - 10*len(value), y_text, (0,0,0), bg_text)
    sleep(timeout)

def draw_stack(depth=8, timeout=0):
    """Rafraichit les {depth} premiers registres depuis le haut de la pile"""
    if fixed: depth = 4
    if depth > len(stack): depth = len(stack)
    for level in range(depth):
        draw_register(level)
    sleep(timeout)

def draw_command(timeout=0.2):
    """Rafraichit la ligne de commande, en bas de l’écran"""
    fill_rect(0, 185, 320, 37, (255,254,255))
    draw_string(entry, 5, 195, (0,0,0), (255,254,255))
    blink_cursor(True)
    sleep(timeout)

def display(command_line=True):
    """Rafraichit tout l'écran : fond, tous les registres de la pile, la ligne de commande"""
    fill_rect(0, 0, 320, 184, (245,250,255))
    # Si la pile est limitée, le plus ancien registre sort et est perdu
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
    """Affiche une erreur ou exception Python dans une boite de dialogue noire"""
    if str(text) == "math domain error":
        msg = "valeur interdite"
    elif str(text) == "invalid syntax for number":
        msg = "syntaxe non valide"
    else:
        msg = str(text)
    fill_rect(144 - 5*len(msg), 89, 32 + 10*len(msg), 44, (0,0,0))
    draw_string(msg, 160 - 5*len(msg), 102, (255,254,255), (0,0,0))
    sleep(0.5); pressed = False
    while not pressed:
        for i in range(53):
            if keydown(i): pressed = True
    display(False)


def draw_item(line, items, descriptions, selected=False):
    """Affiche une ligne d'un menu, éventuellement sur un fond sélectionné"""
    h = 174 // len(items)
    bg_color = (214,213,231) if selected else (255,254,255)
    fill_rect(28, 49 + h*line, 264, h - 1, bg_color)
    draw_string(items[line], 35, 41 + h*line + h // 2, (0,0,0), bg_color)
    draw_string(descriptions[line], 285 - 10*len(descriptions[line]), 41 + h*line + h // 2, (164,165,164), bg_color)

def draw_menu(items, descriptions):
    """Affiche tous les éléments et descriptions d’un menu dans une boite de dialogue"""
    fill_rect(27, 48, 266, 174, (238,238,238))
    fill_rect(28, 49, 264, 173, (255,254,255))
    h = 174 // len(items)
    for i in range(len(items)):
        draw_item(i, items, descriptions)
        fill_rect(28, 48 + h*i, 264, 1, (238,238,238))
    fill_rect(28, 48 + h*len(items), 264, 1, (238,238,238))


def varbox():
    """Affiche un dialogue avec les fonctions disponibles avec la touche ALPHA"""
    keys = ("D", "R", "C", "F", "H", "P", "?")
    desc = ("Angles en degrés", "Angles en radians", "Convertir °F en °C", "Convertir °C en °F", "Heures en h:min", "Facteurs premiers", "Nb aléa. de [0;1[")
    fill_rect(27, 27, 266, 21, (65,64,65))
    fill_rect(28, 28, 264, 19, (108,99,115))
    draw_string("Raccourcis ALPHA", 80, 28, (255,254,255), (108,99,115))
    draw_menu(keys, desc)
    sleep(0.5); pressed = False
    while not pressed:
        for i in (4, 5, 15):  # OK, BACK, VAR
            if keydown(i): pressed = True
    display()


def toolbox():
    """Affiche un dialogue avec les fonctions de NPI habituelles et leurs touches"""
    keys = (" xnt", "  (", "  )", " Ans", "[shift]Ans", "[shift] ÷", "[shift] -")
    desc = ("Pile fixe/dynamiq.", "Défilement bas", "échange niv.1 & 2", "Copie dernier arg.", "Copie niv.2 ", "Inverse ", "Opposé")
    fill_rect(27, 27, 266, 21, (65,64,65))
    fill_rect(28, 28, 264, 19, (108,99,115))
    draw_string("Raccourcis", 110, 28, (255,254,255), (108,99,115))
    draw_menu(keys, desc)
    sleep(0.5); pressed = False
    while not pressed:
        for i in (4, 5, 16):  # OK, BACK, TOOLBOX
            if keydown(i): pressed = True
    display()


def percentage():
    """Affiche un dialogue avec des fonctions de pourcentage habituelles"""
    items = ("%", "Δ%", "%T", "±%", "MU%P")
    descriptions = ("X % de Y", "Diff. en pourcent", "Pourcentage du total", "Evolution ou marge", "Taux de marque")
    fill_rect(27, 27, 266, 21, (65,64,65))
    fill_rect(28, 28, 264, 19, (108,99,115))
    draw_string("Pourcentages", 100, 28, (255,254,255), (108,99,115))
    draw_menu(items, descriptions)
    line = 0; quit = False
    draw_item(0, items, descriptions, True)
    while not quit:
        sleep(0.13)
        if keydown(1) and line > 0:  # HAUT
            draw_item(line, items, descriptions)
            draw_item(line - 1, items, descriptions, True)
            line -= 1
        if keydown(2) and line < len(items) - 1:  # BAS
            draw_item(line, items, descriptions)
            draw_item(line + 1, items, descriptions, True)
            line += 1
        if keydown(4) or keydown(52):  # OK/EXE
            if line == 0:  # % X pourcent de Y
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
            elif line == 1:  # Δ% Différence en pourcent
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
            elif line == 2:  # %T Pourcentage du total
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
            elif line == 3:  # ±% Evolution ou marge
                evaluate2(lambda x, y: x + x*y / 100)
            elif line == 4:  # MU%P Taux de marque
                evaluate2(lambda x, y: (y-x) / y * 100)
            quit = True; display()
        if keydown(5): quit = True; display()  # BACK


# PROGRAMME PRINCIPAL

# État originel :
# pile limitée vide, pas de dernier paramètre,
# ligne de commande vide, angles en degrés

fixed = False; stack = []
lastx = ""; entry = ""
degrees = True

display()
while True:

    # Caractères utilisables sur la ligne de commande
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

    # Propres à la NPI
    elif keydown(14):  # XNT
        fixed = not fixed  # Passer d’une pile limitée à dynamique
        if fixed:  # Maximum 4 niveaux, égaux à 0 si non utilisés
            for level in range(4, len(stack)): stack.pop()
            for level in range(4 - len(stack)): stack.append(0)
        else:  # Tous niveaux vides si non utilisés
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
        if not entry and stack: drop(); display(False)  # DROP retire le niveau supérieur
        else: entry = entry[:-1]; draw_command()  # CLEAR efface le dernier caractère saisi
    elif keydown(33):  # (: (n) ROLL défilement vers le bas
        if entry:
            try: pos = float(entry)
            except Exception as message: draw_error(message)
            else:
                if pos == int(pos) and int(pos) <= len(stack):
                    entry = ""; draw_command()
                    stack.insert(int(pos-1), stack.pop(0))
                    draw_stack(int(pos))
                else:
                    draw_error("niveau de pile non valide")
        elif len(stack) >= 2: stack.append(stack.pop(0)); draw_stack(8, 0.2)
    elif keydown(34):  # ): SWAP
        if entry: push(entry); entry = ""
        if len(stack) >= 2: stack[0], stack[1] = stack[1], stack[0]
        draw_stack(2, 0.2)
    elif keydown(1):  # HAUT: sélection des niveaux, sur pile dynamique
        if not fixed and stack:
            level = 0; draw_register(level, 0.2, True)
            while level >= 0:
                if keydown(1) and level < len(stack) - 1:  # HAUT
                    draw_register(level)
                    draw_register(level + 1, 0.2, True)
                    level += 1
                if keydown(2):  # BAS
                    draw_register(level)
                    if level > 0: draw_register(level - 1, 0.2, True)
                    level -= 1
                if keydown(17):  # BACKSPACE: DROP
                    stack = stack[level+1:]; level = -1
                if keydown(4) or keydown(52):  # OK/EXE: PICK
                    stack[0] = stack[level]; level = -1
                if keydown(33):  # (: ROLL défilement vers le bas
                    stack.insert(int(level), stack.pop(0)); level = -1
                if keydown(5): level = -1  # BACK: quitter le mode de sélection
            display(False)

    # Opérateurs unaires
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

    # Opérateurs binaires
    elif keydown(23): evaluate2(lambda x, y: x ** y)
    elif keydown(39): evaluate2(lambda x, y: x * y)
    elif keydown(40): evaluate2(lambda x, y: x / y)
    elif keydown(45): evaluate2(lambda x, y: x + y)
    elif keydown(46):
        if entry and entry[-1] == "e" and entry.count("-") == 0: entry += "-"
        else: evaluate2(lambda x, y: x - y)

    # Opérateurs sur SHIFT
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
            if keydown(33):  # (: ROLL défilement vers le haut
                if entry:
                    try: pos = float(entry)
                    except Exception as message: draw_error(message)
                    else:
                        entry = ""
                        if pos == int(pos) and int(pos) <= len(stack):
                            stack.insert(0, stack.pop(int(pos)-1))
                        else: draw_error("niveau de pile non valide")
                    display()
                elif len(stack) >= 2: stack.insert(0, stack.pop())
                pressed = True
            if keydown(40): evaluate1(lambda x: 1/x); pressed = True  # DIVISION
            if keydown(46): evaluate1(lambda x: -x); pressed = True  # SYMBOLE MOINS
            if keydown(51):  # Ans: OVER
                if fixed or len(stack) >= 2: push(stack[1])
                pressed = True
            if keydown(12): pressed = True  # SHIFT
        display(False)

    # Opérateurs sur ALPHA
    elif keydown(13):  # ALPHA
        pressed = False; draw_string("alpha", 270, 0, (255,254,255), (255,181,0)); sleep(0.2)
        while not pressed:
            if keydown(6):  # HOME
                pressed = True; display(False); draw_error(__version__)
            if keydown(17):  # %: fonctions de pourcentages
                pressed = True; display(False); percentage()
            if keydown(20):  # C: Fahrenheit en Celsius
                evaluate1(lambda x: (x-32) * 5/9); pressed = True
            if keydown(21):  # D: angles en degrés
                degrees = True; pressed = True; display(False)
            if keydown(23):  # F: Celsius en Fahrenheit
                evaluate1(lambda x: x * 9/5 + 32); pressed = True
            if keydown(25):  # H
                evaluate1(lambda x: hms(x)); pressed = True
            if keydown(33):  # P: Facteurs premiers
                if not entry and stack:
                    try: push(prime_facto(float(stack[0])), False)
                    except Exception as message: draw_error(message)
                    display(False)
                elif entry:
                    if float(entry) != int(float(entry)): draw_error("valeur interdite")
                    else: push(float(entry)); push(prime_facto(float(entry)), False); entry = ""
                    display()
                pressed = True
            if keydown(36):  # R: angles en radians
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
