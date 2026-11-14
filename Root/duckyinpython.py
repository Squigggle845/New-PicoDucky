import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

key_map = {
    "ENTER": Keycode.ENTER,
    "RETURN": Keycode.ENTER,
    "GUI": Keycode.GUI,
    "COMMAND": Keycode.GUI,
    "WINDOWS": Keycode.GUI,
    "SPACE": Keycode.SPACE,
    "TAB": Keycode.TAB,
    "ALT": Keycode.ALT,
    "CONTROL": Keycode.CONTROL,
    "CTRL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT,
    "ESCAPE": Keycode.ESCAPE,
    "ESC": Keycode.ESCAPE,
    "UP": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
    "BACKSPACE": Keycode.BACKSPACE,
    "DELETE": Keycode.DELETE,
    "CAPSLOCK": Keycode.CAPS_LOCK,
    "F1": Keycode.F1, "F2": Keycode.F2, "F3": Keycode.F3, "F4": Keycode.F4,
    "F5": Keycode.F5, "F6": Keycode.F6, "F7": Keycode.F7, "F8": Keycode.F8,
    "F9": Keycode.F9, "F10": Keycode.F10, "F11": Keycode.F11, "F12": Keycode.F12,
    "a": Keycode.A, "b": Keycode.B, "c": Keycode.C, "d": Keycode.D,
    "e": Keycode.E, "f": Keycode.F, "g": Keycode.G, "h": Keycode.H,
    "i": Keycode.I, "j": Keycode.J, "k": Keycode.K, "l": Keycode.L,
    "m": Keycode.M, "n": Keycode.N, "o": Keycode.O, "p": Keycode.P,
    "q": Keycode.Q, "r": Keycode.R, "s": Keycode.S, "t": Keycode.T,
    "u": Keycode.U, "v": Keycode.V, "w": Keycode.W, "x": Keycode.X,
    "y": Keycode.Y, "z": Keycode.Z
}

variables = {}

def eval_expr(expr):
    expr = expr.strip()
    for var_name, val in variables.items():
        expr = expr.replace(var_name, str(val))
    try:
        return eval(expr)
    except Exception:
        return 0

def replace_vars(text):
    for var_name, val in variables.items():
        text = text.replace(var_name, str(val))
    return text

def send_combo(parts):
    codes = []
    for p in parts:
        if p in key_map:
            codes.append(key_map[p])
        elif p.lower() in key_map:
            codes.append(key_map[p.lower()])
    if codes:
        kbd.send(*codes)

def execute_line(line):
    if line.startswith("REM") or not line:
        return
    elif line.startswith("DELAY "):
        val = eval_expr(line[6:])
        time.sleep(val / 1000.0)
    elif line.startswith("STRINGLN "):
        layout.write(replace_vars(line[9:]) + "\n")
    elif line.startswith("STRING "):
        layout.write(replace_vars(line[7:]))
    elif line.startswith("VAR "):
        parts = line[4:].split("=", 1)
        if len(parts) == 2:
            var_name = parts[0].strip()
            variables[var_name] = eval_expr(parts[1])
    elif line.startswith("$"):
        parts = line.split("=", 1)
        if len(parts) == 2:
            var_name = parts[0].strip()
            variables[var_name] = eval_expr(parts[1])
    else:
        parts = line.split()
        send_combo(parts)

def run_block(lines):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("WHILE "):
            cond = line[6:].strip(" ()")
            block = []
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                l = lines[i].strip()
                if l.startswith("WHILE "):
                    depth += 1
                elif l == "END_WHILE":
                    depth -= 1
                if depth > 0:
                    block.append(lines[i])
                i += 1
            while eval_expr(cond):
                run_block(block)
                
        elif line.startswith("IF "):
            cond = line[3:].replace("THEN", "").strip(" ()")
            block = []
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                l = lines[i].strip()
                if l.startswith("IF "):
                    depth += 1
                elif l == "END_IF":
                    depth -= 1
                if depth > 0:
                    block.append(lines[i])
                i += 1
            if eval_expr(cond):
                run_block(block)
        else:
            execute_line(line)
            i += 1

def runScript(filename="payload.dd"):
    try:
        with open(filename, "r") as f:
            lines = [l.strip("\r\n") for l in f.readlines()]
        run_block(lines)
    except Exception as e:
        print("Script Error:", e)