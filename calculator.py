import math
import re
import statistics
import tkinter as tk
from collections import Counter
from tkinter import ttk

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except Exception:          # missing OR broken matplotlib: run without the graph
    HAS_MPL = False

# ---- Light background, dark text ----
BG = "#F5F5F5"
PANEL = "#E3E8EF"
BTN_NUM = "#FFFFFF"
BTN_OP = "#CFD8E6"
BTN_EQ = "#1E88E5"
BTN_CLEAR = "#FFCDD2"
TEXT = "#111111"

# Safe-eval settings, built without typing double underscores
# (so copy/paste from chat cannot damage them)
UNDER = "_" * 2
SAFE_GLOBALS = {UNDER + "builtins" + UNDER: {}}


def create(cls, *args):
    """Make an object of cls and run its setup() method."""
    obj = cls()
    obj.setup(*args)
    return obj


root = tk.Tk()
root.title("Calc")
root.configure(bg=BG)
root.resizable(False, False)

# ---- Tab design ----
style = ttk.Style()
style.theme_use("clam")
style.configure("TNotebook", background=BG, borderwidth=0)
style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT,
                padding=(16, 8), font=("Segoe UI", 11))
style.map("TNotebook.Tab",
          background=[("selected", BTN_EQ)],
          foreground=[("selected", "white")])

tabs = ttk.Notebook(root)
tabs.pack(fill="both", expand=True)

basic_tab = tk.Frame(tabs, bg=BG)
advanced_tab = tk.Frame(tabs, bg=BG)
stats_tab = tk.Frame(tabs, bg=BG)
graph_tab = tk.Frame(tabs, bg=BG)
tabs.add(basic_tab, text="Basic")
tabs.add(advanced_tab, text="Advanced")
tabs.add(stats_tab, text="Statistics")
tabs.add(graph_tab, text="Graph")

# ---- Keypad layouts ----
BASIC_ROWS = [
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "−"],
    ["0", ".", "⌫", "+"],
    ["C", "(", ")", "="],
]

ADVANCED_ROWS = [
    ["sin", "cos", "tan", "log", "ln"],
    ["√", "x²", "xʸ", "(", ")"],
    ["7", "8", "9", "÷", "C"],
    ["4", "5", "6", "×", "⌫"],
    ["1", "2", "3", "−", "π"],
    ["0", ".", "e", "+", "="],
]

# what each special key types into the screen
INSERT = {
    "sin": "sin(", "cos": "cos(", "tan": "tan(",
    "log": "log(", "ln": "ln(", "√": "sqrt(",
    "x²": "^2", "xʸ": "^",
}

# functions the calculator understands (angles are in DEGREES)
NAMES = {
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    "log": math.log10,
    "ln": math.log,
    "sqrt": math.sqrt,
    "pi": math.pi,
    "e": math.e,
}


class Calculator:
    def setup(self, parent, rows):
        self.expression = ""
        columns = len(rows[0])

        self.screen = tk.Label(parent, text="0", anchor="e", font=("Consolas", 24, "bold"),
                               bg=PANEL, fg=TEXT, padx=10, pady=14)
        self.screen.grid(row=0, column=0, columnspan=columns, padx=12, pady=12, sticky="ew")

        for r, row in enumerate(rows, start=1):
            for c, label in enumerate(row):
                fg = TEXT
                if label == "=":
                    color, fg = BTN_EQ, "white"
                elif label in ("C", "⌫"):
                    color = BTN_CLEAR
                elif label in "+-*/÷×−":
                    color = BTN_OP
                elif label in INSERT or label == "π":
                    color = PANEL
                else:
                    color = BTN_NUM
                tk.Button(parent, text=label, font=("Segoe UI", 13, "bold"),
                          width=5, height=2, bg=color, fg=fg, relief="flat",
                          activebackground=BTN_OP,
                          command=lambda t=label: self.press(t)
                          ).grid(row=r, column=c, padx=3, pady=3)

    def show(self, text):
        self.screen.config(text=text or "0")

    def press(self, key):
        if self.expression == "Error":
            self.expression = ""
        if key == "C":
            self.expression = ""
        elif key == "⌫":
            self.expression = self.expression[:-1]
        elif key == "=":
            self.calculate()
            return
        else:
            self.expression += INSERT.get(key, key)
        self.show(self.expression)

    def calculate(self):
        if not self.expression:                      # nothing to calculate
            return
        text = (self.expression.replace("×", "*").replace("÷", "/")
                .replace("−", "-").replace("π", "pi")
                .replace("^", "**"))
        # implicit multiplication: 2pi, 3(4), 2sin(30), (1+2)(3+4)
        text = re.sub(r"(\d|\))\s*(?=pi\b|e\b|[a-z]+\(|\()", r"\1*", text)
        text += ")" * (text.count("(") - text.count(")"))   # close open brackets
        try:
            result = eval(text, dict(SAFE_GLOBALS), NAMES)
            if isinstance(result, float):
                result = round(result, 10)
                if result == int(result):
                    result = int(result)
            self.expression = str(result)
        except Exception:
            self.expression = "Error"
        self.show(self.expression)


basic = create(Calculator, basic_tab, BASIC_ROWS)
advanced = create(Calculator, advanced_tab, ADVANCED_ROWS)
calculators = [basic, advanced]   # same order as the tabs

# ---- Keyboard support ----
KEYMAP = {
    "*": "×", "/": "÷", "-": "−",
    "p": "π", "s": "sin", "c": "cos", "t": "tan",
    "l": "log", "n": "ln", "r": "√",
}
FUNCTION_KEYS = "pstclnr"        # only available on the Advanced tab
TYPEABLE = "0123456789.+()^=e"


def on_key(event):
    tab = tabs.index(tabs.select())
    if tab >= len(calculators):          # Statistics / Graph tabs: no calculator
        return
    calc = calculators[tab]
    if tab == 0 and event.char and event.char in FUNCTION_KEYS + "e^":
        return                           # Basic tab has no functions
    if event.keysym in ("Return", "KP_Enter"):
        calc.press("=")
    elif event.keysym == "BackSpace":
        calc.press("⌫")
    elif event.keysym in ("Escape", "Delete"):
        calc.press("C")
    elif event.char in KEYMAP:
        calc.press(KEYMAP[event.char])
    elif event.char and event.char in TYPEABLE:
        calc.press(event.char)


root.bind("<Key>", on_key)


# ================= STATISTICS TAB =================
def parse_numbers(text):
    """'24, 80 75' -> [24.0, 80.0, 75.0]  (ValueError if not numbers)"""
    return [float(p) for p in text.replace(",", " ").split()]


def fmt(v):
    """Show 41.2 as 41.2 and 24.0 as 24."""
    if isinstance(v, str):
        return v
    if isinstance(v, float):
        v = round(v, 6)
        if math.isfinite(v) and v == int(v):
            return str(int(v))
    return str(v)


def need(data, n, what):
    if len(data) < n:
        raise ValueError(f"{what} needs at least {n} values")


def quartiles(xs):
    need(xs, 2, "Quartiles")
    return statistics.quantiles(xs, n=4, method="inclusive")


def mode(xs):
    if max(Counter(xs).values()) == 1:       # every value appears once
        return "No mode"
    return ", ".join(fmt(v) for v in statistics.multimode(xs))


def sample(func, what):
    def run(xs, ys):
        need(xs, 2, what)
        return func(xs)
    return run


def regression(xs, ys):
    if not ys:
        raise ValueError("Add Y data too (second box)")
    if len(xs) != len(ys):
        raise ValueError(f"X has {len(xs)} values but Y has {len(ys)}")
    need(xs, 2, "Regression")
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        raise ValueError("All X values are the same")
    slope = sxy / sxx
    intercept = my - slope * mx
    r = sxy / math.sqrt(sxx * syy) if syy else 0.0
    return slope, intercept, r


STATS = {
    "Count": lambda xs, ys: len(xs),
    "Sum": lambda xs, ys: sum(xs),
    "Mean": lambda xs, ys: statistics.mean(xs),
    "Median": lambda xs, ys: statistics.median(xs),
    "Mode": lambda xs, ys: mode(xs),
    "Min": lambda xs, ys: min(xs),
    "Max": lambda xs, ys: max(xs),
    "Range": lambda xs, ys: max(xs) - min(xs),
    "Q1": lambda xs, ys: quartiles(xs)[0],
    "Q3": lambda xs, ys: quartiles(xs)[2],
    "IQR": lambda xs, ys: quartiles(xs)[2] - quartiles(xs)[0],
    "Samp Var": sample(statistics.variance, "Sample variance"),
    "Pop Var": lambda xs, ys: statistics.pvariance(xs),
    "Std (s)": sample(statistics.stdev, "Sample std dev"),
    "Std (σ)": lambda xs, ys: statistics.pstdev(xs),
    "Corr (r)": lambda xs, ys: regression(xs, ys)[2],
    "Slope (m)": lambda xs, ys: regression(xs, ys)[0],
    "Y-Int (b)": lambda xs, ys: regression(xs, ys)[1],
}


def compute(name, xs, ys):
    if not xs:
        raise ValueError("Add some X data first")
    return fmt(STATS[name](xs, ys))


class StatisticsTab:
    def setup(self, parent):
        self.xs, self.ys = [], []

        self.x_entry = self.make_row(parent, 0, "Data (X):", "x")
        self.x_info = tk.Label(parent, text="No X data entered yet.", anchor="w",
                               bg=BG, fg=TEXT, font=("Consolas", 10))
        self.x_info.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12)

        self.y_entry = self.make_row(parent, 2, "Data (Y):", "y")
        self.y_info = tk.Label(parent, text="No Y data entered yet (optional).", anchor="w",
                               bg=BG, fg=TEXT, font=("Consolas", 10))
        self.y_info.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12)

        pad = tk.Frame(parent, bg=BG)
        pad.grid(row=4, column=0, columnspan=3, padx=12, pady=10)
        names = list(STATS) + ["All", "Clear All"]
        for i, name in enumerate(names):
            color, fg = PANEL, TEXT
            if name == "All":
                color, fg = BTN_EQ, "white"
            elif name == "Clear All":
                color = BTN_CLEAR
            tk.Button(pad, text=name, font=("Segoe UI", 10, "bold"), width=9, height=1,
                      bg=color, fg=fg, relief="flat", activebackground=BTN_OP,
                      command=lambda n=name: self.on_stat(n)
                      ).grid(row=i // 4, column=i % 4, padx=3, pady=3)

        self.result = tk.Text(parent, height=9, width=44, bg=PANEL, fg=TEXT, relief="flat",
                              font=("Consolas", 11), state="disabled")
        self.result.grid(row=5, column=0, columnspan=3, padx=12, pady=(0, 12))
        self.write("Enter data, press Add, then press a button.\nTip: type  24, 80, 75, 12, 15",
                   reset=True)

    def make_row(self, parent, row, label, which):
        tk.Label(parent, text=label, bg=BG, fg=TEXT,
                 font=("Segoe UI", 11)).grid(row=row, column=0, padx=(12, 4),
                                             pady=(12, 0), sticky="w")
        entry = tk.Entry(parent, width=26, font=("Consolas", 12), bg=BTN_NUM, fg=TEXT,
                         relief="flat", insertbackground=TEXT)
        entry.grid(row=row, column=1, pady=(12, 0), ipady=4)
        entry.bind("<Return>", lambda e: self.add(which))
        tk.Button(parent, text="Add", font=("Segoe UI", 10, "bold"), bg=BTN_OP, fg=TEXT,
                  relief="flat", width=6, command=lambda: self.add(which)
                  ).grid(row=row, column=2, padx=8, pady=(12, 0))
        return entry

    def write(self, text, reset=False):
        self.result.config(state="normal")
        if reset:
            self.result.delete("1.0", "end")
        self.result.insert("end", text + "\n")
        self.result.see("end")
        self.result.config(state="disabled")

    def update_info(self):
        for label, data, name in ((self.x_info, self.xs, "X"), (self.y_info, self.ys, "Y")):
            if not data:
                label.config(text=f"No {name} data entered yet." if name == "X"
                             else "No Y data entered yet (optional).")
            else:
                shown = ", ".join(fmt(v) for v in data[:10])
                more = ", ..." if len(data) > 10 else ""
                label.config(text=f"{name} ({len(data)}): {shown}{more}")

    def add(self, which):
        entry = self.x_entry if which == "x" else self.y_entry
        try:
            numbers = parse_numbers(entry.get())
        except ValueError:
            self.write("Please type numbers only, like: 24, 80, 75", reset=True)
            return
        if not numbers:
            return
        (self.xs if which == "x" else self.ys).extend(numbers)
        entry.delete(0, tk.END)
        self.update_info()

    def on_stat(self, name):
        if name == "Clear All":
            self.xs.clear()
            self.ys.clear()
            self.update_info()
            self.write("All data cleared.", reset=True)
        elif name == "All":
            self.write("---- All results ----", reset=True)
            for n in STATS:
                try:
                    value = compute(n, self.xs, self.ys)
                except ValueError:
                    value = "-"
                self.write(f"{n:<10} = {value}")
        else:
            try:
                self.write(f"{name} = {compute(name, self.xs, self.ys)}")
            except ValueError as error:
                self.write(str(error))


stats = create(StatisticsTab, stats_tab)


# ================= GRAPH TAB =================
# the graph uses RADIANS for sin/cos/tan (so waves look normal)
GRAPH_NAMES = dict(NAMES)
GRAPH_NAMES.update({"sin": math.sin, "cos": math.cos, "tan": math.tan})


def to_python(text):
    """'2x^2 + 3' -> '2*x**2 + 3'"""
    text = (text.replace("^", "**").replace("π", "pi").replace("×", "*")
            .replace("÷", "/").replace("−", "-"))
    # 2x, 2(x+1), 3pi, (x+1)(x-1), (x+1)x
    text = re.sub(r"(\d|\))\s*(?=[a-zA-Z(])", r"\1*", text)
    # x(x+1), x2, x sin(x)
    text = re.sub(r"(?<![a-zA-Z_])x\s*(?=[\da-zA-Z(])", "x*", text)
    # pi x, e(x+1)
    text = re.sub(r"\b(pi|e)\s*(?=x\b|\()", r"\1*", text)
    return text


def sample_function(text, x_min, x_max, n=400):
    """Return (xs, ys) for y = f(x). Bad points become nan (gaps in the line)."""
    try:
        code = compile(to_python(text), "<graph>", "eval")
    except (SyntaxError, ValueError):
        raise ValueError("Invalid formula")
    xs = [x_min + (x_max - x_min) * i / (n - 1) for i in range(n)]
    ys = []
    for x in xs:
        try:
            ys.append(float(eval(code, dict(SAFE_GLOBALS), dict(GRAPH_NAMES, x=x))))
        except Exception:
            ys.append(float("nan"))
    if all(math.isnan(y) for y in ys):
        raise ValueError("Could not plot this formula")
    return xs, ys


class GraphTab:
    def setup(self, parent):
        self.xlim, self.ylim = (-10, 10), (-10, 10)
        self.points = None
        if not HAS_MPL:
            tk.Label(parent, text="Graph needs matplotlib.\n\nOpen the terminal and run:\n"
                     "python -m pip install matplotlib\n\nthen run the program again.",
                     bg=BG, fg=TEXT, font=("Segoe UI", 12), justify="center"
                     ).pack(padx=40, pady=80)
            return

        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", padx=12, pady=10)
        tk.Label(bar, text="y =", bg=BG, fg=TEXT, font=("Segoe UI", 13, "bold")).pack(side="left")
        self.entry = tk.Entry(bar, width=20, font=("Consolas", 12), bg=BTN_NUM, fg=TEXT,
                              relief="flat", insertbackground=TEXT)
        self.entry.pack(side="left", padx=8, ipady=4)
        self.entry.insert(0, "x^2")
        self.entry.bind("<Return>", lambda e: self.plot())
        for text, command, color in (("Plot", self.plot, BTN_EQ), ("Reset", self.reset, BTN_OP)):
            tk.Button(bar, text=text, command=command, bg=color,
                      fg="white" if color == BTN_EQ else TEXT, relief="flat",
                      font=("Segoe UI", 10, "bold"), width=6).pack(side="left", padx=3)

        self.fig = Figure(figsize=(4.6, 3.8), dpi=100, facecolor=BG)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(padx=12)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.info = tk.Label(parent, text="", bg=BG, fg=TEXT, font=("Consolas", 10), anchor="w")
        self.info.pack(fill="x", padx=12, pady=8)
        self.draw()

    # ---- buttons ----
    def plot(self):
        if self.points is not None:
            self.points = None
            self.xlim, self.ylim = (-10, 10), (-10, 10)
        self.draw()

    def reset(self):
        self.points = None
        self.xlim, self.ylim = (-10, 10), (-10, 10)
        self.draw()

    def show_points(self, xs, ys, slope, intercept, r):
        """Called from the Statistics tab: scatter plot + best-fit line."""
        self.points = (xs, ys, slope, intercept, r)
        pad_x = (max(xs) - min(xs)) * 0.2 or 1
        pad_y = (max(ys) - min(ys)) * 0.2 or 1
        self.xlim = (min(xs) - pad_x, max(xs) + pad_x)
        self.ylim = (min(ys) - pad_y, max(ys) + pad_y)
        self.draw()

    # ---- drawing ----
    def draw(self):
        ax = self.ax
        ax.clear()
        ax.set_facecolor(BTN_NUM)
        ax.grid(True, color=PANEL)
        ax.axhline(0, color="#888888", linewidth=1)
        ax.axvline(0, color="#888888", linewidth=1)
        message = "Scroll the mouse wheel to zoom."

        if self.points is not None:
            px, py, m, b, r = self.points
            ax.scatter(px, py, color=BTN_EQ, zorder=3)
            ends = list(self.xlim)
            ax.plot(ends, [m * v + b for v in ends], color="#E53935", linestyle="--")
            sign = "+" if b >= 0 else "-"
            message = f"Best fit: y = {fmt(m)}x {sign} {fmt(abs(b))}   r = {fmt(r)}"
        else:
            text = self.entry.get().strip()
            if text:
                try:
                    xs, ys = sample_function(text, self.xlim[0], self.xlim[1])
                    ax.plot(xs, ys, color=BTN_EQ, linewidth=2)
                    message = f"y = {text}   (scroll to zoom)"
                except ValueError as error:
                    message = str(error)

        ax.set_xlim(*self.xlim)
        ax.set_ylim(*self.ylim)
        self.info.config(text=message)
        self.canvas.draw_idle()

    def on_scroll(self, event):
        if event.xdata is None or event.ydata is None:
            return
        scale = 0.8 if event.button == "up" else 1.25
        (x0, x1), (y0, y1) = self.xlim, self.ylim
        cx, cy = event.xdata, event.ydata
        self.xlim = (cx - (cx - x0) * scale, cx + (x1 - cx) * scale)
        self.ylim = (cy - (cy - y0) * scale, cy + (y1 - cy) * scale)
        self.draw()


graph = create(GraphTab, graph_tab)


def view_graph():
    """Statistics tab -> 'View Graph' button."""
    if not HAS_MPL:
        stats.write("Graph needs matplotlib. Run:  python -m pip install matplotlib", reset=True)
        return
    if not stats.xs or len(stats.xs) != len(stats.ys):
        stats.write("For a graph, add X and Y data with the same number of values.", reset=True)
        return
    try:
        slope, intercept, r = regression(stats.xs, stats.ys)
    except ValueError as error:
        stats.write(str(error), reset=True)
        return
    graph.show_points(stats.xs, stats.ys, slope, intercept, r)
    tabs.select(graph_tab)


tk.Button(stats_tab, text="View Graph", font=("Segoe UI", 11, "bold"), bg=BTN_EQ,
          fg="white", relief="flat", activebackground=BTN_OP,
          command=view_graph).grid(row=7, column=0, columnspan=3, sticky="ew",
                                   padx=12, pady=(0, 12), ipady=3)

root.mainloop()