import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# --- 1. Hardware Safe-Mode Switch (GP0 to GND) ---
# Connect GP0 (Pin 1) to GND (Pin 3) to disable typing when editing files
safe_pin = digitalio.DigitalInOut(board.GP0)
safe_pin.direction = digitalio.Direction.INPUT
safe_pin.pull = digitalio.Pull.UP

if not safe_pin.value:
    print("Safe mode active (GP0 grounded). Skipping payload execution.")
else:
    # Wait 3 seconds for the host OS to register the USB keyboard
    time.sleep(3)

    kbd = Keyboard(usb_hid.devices)
    layout = KeyboardLayoutUS(kbd)

    # --- 2. Cross-Platform Keycode Dictionary ---
    KEY_MAP = {
        "ENTER": Keycode.ENTER,
        "RETURN": Keycode.ENTER,
        "GUI": Keycode.GUI,
        "COMMAND": Keycode.GUI,
        "WINDOWS": Keycode.GUI,
        "SPACE": Keycode.SPACE,
        "TAB": Keycode.TAB,
        "ALT": Keycode.ALT,
        "OPTION": Keycode.ALT,
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
    default_delay = 0

    def eval_expr(expr):
        expr = expr.strip()
        # Sort by variable length descending so $COUNT10 replaces before $COUNT
        for var_name in sorted(variables.keys(), key=len, reverse=True):
            expr = expr.replace(var_name, str(variables[var_name]))
        try:
            return eval(expr)
        except Exception:
            return 0

    def replace_vars(text):
        for var_name in sorted(variables.keys(), key=len, reverse=True):
            text = text.replace(var_name, str(variables[var_name]))
        return text

    def send_combo(parts):
        codes = []
        for p in parts:
            if p in KEY_MAP:
                codes.append(KEY_MAP[p])
            elif p.lower() in KEY_MAP:
                codes.append(KEY_MAP[p.lower()])
        if codes:
            kbd.send(*codes)

    def execute_line(line):
        global default_delay
        if not line or line.startswith("REM"):
            return

        if line.startswith("DEFAULT_DELAY ") or line.startswith("DEFAULTDELAY "):
            default_delay = int(eval_expr(line.split(" ", 1)[1]))
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
                variables[parts[0].strip()] = eval_expr(parts[1])
        elif line.startswith("$"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                variables[parts[0].strip()] = eval_expr(parts[1])
        else:
            send_combo(line.split())

        if default_delay > 0 and not line.startswith("DELAY"):
            time.sleep(default_delay / 1000.0)

    def run_block(lines):
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Handle DuckyScript 3.0 WHILE Loops
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

            # Handle DuckyScript 3.0 IF / ELSE Statements
            elif line.startswith("IF "):
                cond = line[3:].replace("THEN", "").strip(" ()")
                true_block = []
                false_block = []
                in_else = False
                depth = 1
                i += 1
                while i < len(lines) and depth > 0:
                    l = lines[i].strip()
                    if l.startswith("IF "):
                        depth += 1
                    elif l == "END_IF":
                        depth -= 1
                    elif l == "ELSE" and depth == 1:
                        in_else = True
                        i += 1
                        continue
                    if depth > 0:
                        if in_else:
                            false_block.append(lines[i])
                        else:
                            true_block.append(lines[i])
                    i += 1
                if eval_expr(cond):
                    run_block(true_block)
                elif false_block:
                    run_block(false_block)
            else:
                execute_line(line)
                i += 1

    # --- 3. Load and Execute payload.dd ---
    try:
        with open("payload.dd", "r") as f:
            script_lines = [l.strip("\r\n") for l in f.readlines()]
        run_block(script_lines)
    except Exception as e:
        print("Execution error:", e)