import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

led = None
try:
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
except Exception:
    pass

def set_led(state):
    if led:
        led.value = state

KEY_MAP = {
    "ENTER": Keycode.ENTER, "RETURN": Keycode.ENTER,
    "GUI": Keycode.GUI, "COMMAND": Keycode.GUI, "WINDOWS": Keycode.GUI, "WIN": Keycode.GUI,
    "SPACE": Keycode.SPACE, "TAB": Keycode.TAB,
    "ALT": Keycode.ALT, "OPTION": Keycode.ALT,
    "CONTROL": Keycode.CONTROL, "CTRL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT,
    "ESCAPE": Keycode.ESCAPE, "ESC": Keycode.ESCAPE,
    "UP": Keycode.UP_ARROW, "UPARROW": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW, "DOWNARROW": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW, "LEFTARROW": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW, "RIGHTARROW": Keycode.RIGHT_ARROW,
    "BACKSPACE": Keycode.BACKSPACE, "DELETE": Keycode.DELETE, "DEL": Keycode.DELETE,
    "INSERT": Keycode.INSERT, "HOME": Keycode.HOME, "END": Keycode.END,
    "PAGEUP": Keycode.PAGE_UP, "PAGEDOWN": Keycode.PAGE_DOWN,
    "CAPSLOCK": Keycode.CAPS_LOCK, "NUMLOCK": Keycode.KEYPAD_NUMLOCK,
    "SCROLLLOCK": Keycode.SCROLL_LOCK, "PRINTSCREEN": Keycode.PRINT_SCREEN,
    "PAUSE": Keycode.PAUSE, "BREAK": Keycode.PAUSE, "MENU": Keycode.APPLICATION, "APP": Keycode.APPLICATION,
    "F1": Keycode.F1, "F2": Keycode.F2, "F3": Keycode.F3, "F4": Keycode.F4,
    "F5": Keycode.F5, "F6": Keycode.F6, "F7": Keycode.F7, "F8": Keycode.F8,
    "F9": Keycode.F9, "F10": Keycode.F10, "F11": Keycode.F11, "F12": Keycode.F12,
    "a": Keycode.A, "b": Keycode.B, "c": Keycode.C, "d": Keycode.D,
    "e": Keycode.E, "f": Keycode.F, "g": Keycode.G, "h": Keycode.H,
    "i": Keycode.I, "j": Keycode.J, "k": Keycode.K, "l": Keycode.L,
    "m": Keycode.M, "n": Keycode.N, "o": Keycode.O, "p": Keycode.P,
    "q": Keycode.Q, "r": Keycode.R, "s": Keycode.S, "t": Keycode.T,
    "u": Keycode.U, "v": Keycode.V, "w": Keycode.W, "x": Keycode.X,
    "y": Keycode.Y, "z": Keycode.Z,
    "0": Keycode.ZERO, "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE,
    "4": Keycode.FOUR, "5": Keycode.FIVE, "6": Keycode.SIX, "7": Keycode.SEVEN,
    "8": Keycode.EIGHT, "9": Keycode.NINE
}

variables = {}
defines = {}
functions = {}
default_delay = 0
stop_flag = False

def reset_state():
    global variables, defines, functions, default_delay, stop_flag
    variables = {
        "TRUE": True, "FALSE": False,
        "WINDOWS": 1, "MACOS": 2, "LINUX": 3,
        "$_OS": 1,
        "$_RECEIVED_HOST_LOCK_LED_REPLY": True,
        "$_HOST_CONFIGURATION_REQUEST_COUNT": 5,
        "$_CAPSLOCK_ON": False, "$_NUMLOCK_ON": False, "$_SCROLLLOCK_ON": False
    }
    defines = {}
    functions = {}
    default_delay = 0
    stop_flag = False

def apply_defines_and_vars(text):
    for def_name in sorted(defines.keys(), key=len, reverse=True):
        text = text.replace(def_name, str(defines[def_name]))
    for var_name in sorted(variables.keys(), key=len, reverse=True):
        if var_name.startswith("$"):
            text = text.replace(var_name, str(variables[var_name]))
    return text

def eval_expr(expr):
    expr = expr.strip().replace("&&", " and ").replace("||", " or ")
    for def_name in sorted(defines.keys(), key=len, reverse=True):
        expr = expr.replace(def_name, str(defines[def_name]))
    for var_name in sorted(variables.keys(), key=len, reverse=True):
        val = variables[var_name]
        if isinstance(val, bool):
            expr = expr.replace(var_name, "True" if val else "False")
        else:
            expr = expr.replace(var_name, str(val))
    try:
        return eval(expr)
    except Exception:
        return 0

def send_combo(line):
    normalized = line.replace("-", " ").replace("+", " ")
    codes = []
    for p in normalized.split():
        if p in KEY_MAP:
            codes.append(KEY_MAP[p])
        elif p.upper() in KEY_MAP:
            codes.append(KEY_MAP[p.upper()])
        elif p.lower() in KEY_MAP:
            codes.append(KEY_MAP[p.lower()])
    if codes:
        kbd.send(*codes)

def execute_line(line):
    global default_delay, stop_flag
    if stop_flag or not line or line.startswith("REM"):
        return

    if line.startswith("DEFINE "):
        parts = line[7:].strip().split(" ", 1)
        if len(parts) == 2:
            defines[parts[0].strip()] = parts[1].strip()
        return

    if line in ("STOP_PAYLOAD", "HALT"):
        stop_flag = True
        return
    elif line.startswith("LED_G") or line == "LED_ON":
        set_led(True)
        return
    elif line.startswith("LED_R") or line == "LED_OFF":
        set_led(False)
        return
    elif line.startswith("WAIT_FOR_BUTTON_PRESS"):
        return

    if line.startswith("DEFAULT_DELAY ") or line.startswith("DEFAULTDELAY "):
        default_delay = int(eval_expr(line.split(" ", 1)[1]))
        return
    elif line.startswith("DELAY "):
        time.sleep(max(0, eval_expr(line[6:])) / 1000.0)
        return

    if line.startswith("STRINGLN "):
        layout.write(apply_defines_and_vars(line[9:]) + "\n")
    elif line.startswith("STRING "):
        layout.write(apply_defines_and_vars(line[7:]))
    elif line.startswith("VAR "):
        parts = line[4:].split("=", 1)
        if len(parts) == 2:
            variables[parts[0].strip()] = eval_expr(parts[1])
    elif line.startswith("$"):
        parts = line.split("=", 1)
        if len(parts) == 2:
            variables[parts[0].strip()] = eval_expr(parts[1])
    elif line.startswith("CALL "):
        func_name = line[5:].strip().rstrip("()")
        if func_name in functions:
            run_block(functions[func_name])
    elif line.endswith("()") and line[:-2].strip() in functions:
        run_block(functions[line[:-2].strip()])
    else:
        send_combo(apply_defines_and_vars(line))

    if default_delay > 0 and not line.startswith("DELAY"):
        time.sleep(default_delay / 1000.0)

def run_block(lines):
    global stop_flag
    i = 0
    while i < len(lines) and not stop_flag:
        line = lines[i].strip()
        if not line or line.startswith("REM"):
            i += 1
            continue

        if line.startswith("EXTENSION "):
            i += 1
            while i < len(lines):
                ext_line = lines[i].strip()
                if ext_line.startswith("DEFINE "):
                    execute_line(ext_line)
                elif ext_line == "END_EXTENSION":
                    break
                i += 1
            i += 1
        elif line.startswith("FUNCTION "):
            func_name = line[9:].strip().rstrip("()")
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != "END_FUNCTION":
                block.append(lines[i])
                i += 1
            functions[func_name] = block
            i += 1
        elif line in ("STRING", "STRINGLN"):
            is_ln = (line == "STRINGLN")
            end_tag = "END_STRINGLN" if is_ln else "END_STRING"
            i += 1
            while i < len(lines):
                s_line = lines[i].strip("\r\n")
                if s_line.strip() == end_tag:
                    break
                layout.write(apply_defines_and_vars(s_line.lstrip()) + ("\n" if is_ln else ""))
                i += 1
            i += 1
        elif line.startswith("REPEAT "):
            count = int(eval_expr(line[7:]))
            if i > 0:
                prev_line = lines[i - 1].strip()
                for _ in range(count):
                    if stop_flag:
                        break
                    execute_line(prev_line)
            i += 1
        elif line.startswith("WHILE "):
            cond = line[6:].strip()
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
            while not stop_flag and eval_expr(cond):
                run_block(block)
        elif line.startswith("IF "):
            branches = []
            curr_cond = line[3:].replace("THEN", "").strip()
            curr_block = []
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                l = lines[i].strip()
                if l.startswith("IF "):
                    depth += 1
                    curr_block.append(lines[i])
                elif l == "END_IF":
                    depth -= 1
                    if depth == 0:
                        branches.append((curr_cond, curr_block))
                    else:
                        curr_block.append(lines[i])
                elif depth == 1 and (l.startswith("ELSE IF ") or l.startswith("ELSE_IF ")):
                    branches.append((curr_cond, curr_block))
                    curr_cond = l.split("IF ", 1)[1].replace("THEN", "").strip()
                    curr_block = []
                elif depth == 1 and l == "ELSE":
                    branches.append((curr_cond, curr_block))
                    curr_cond = "True"
                    curr_block = []
                else:
                    curr_block.append(lines[i])
                i += 1
            for cond_str, b_lines in branches:
                if eval_expr(cond_str):
                    run_block(b_lines)
                    break
        else:
            execute_line(line)
            i += 1

def run_ducky_text(text):
    reset_state()
    set_led(True)
    lines = [l.strip("\r\n") for l in text.splitlines()]
    run_block(lines)
    set_led(False)

def run_ducky_file(filename="payload.dd"):
    try:
        with open(filename, "r") as f:
            content = f.read()
        run_ducky_text(content)
        return True, f"Executed {filename}!"
    except Exception as e:
        set_led(False)
        return False, f"Error: {e}"