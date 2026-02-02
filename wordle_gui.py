import argparse
import os
import random
import string
import sys
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional, Tuple
from ttkbootstrap import Style as TBStyle

# Optional color support
try:
    from colorama import Fore, Back, Style, init as colorama_init
    colorama_init(autoreset=True)
    _HAS_COLORAMA = True
except Exception:
    _HAS_COLORAMA = False

# --- Small fallback word lists (replace by providing solutions.txt and allowed.txt files) ---
FALLBACK_SOLUTIONS = [
    "cigar", "rebut", "sissy", "humph", "awake", "blush", "focal", "evade", "naval", "serve",
    "heath", "dwarf", "model", "karma", "stink", "grade", "quiet", "bench", "abate", "feign",
    "house","under","pride","singer","learn","claim","trust","smile","human","later",
    "twice","guide","match","front","timer","music","watch","exist","grant","quiet",
    "track","shift","group","spirit","wrath","slope","upset","peach","grape","serve",
    "field","plead","begin","sword","stack","spear","often","value","evade","honor",
    "sense","harsh","solid","shore","start","still","upper","table","fruit","white",
    "steel","fault","guard","heart","panel","think","trade","flour","shout","raise",
    "stone","union","sharp","paint","model","green","bloom","smoke","young","guest",
    "lodge","wires","sugar","throw","reach","logic","links","stool","magic","graph",
    "price","prove","risky","skill","youth","ivory","fresh","plain","press","timer",
    "fight","train","might","total","legal","climb","cabin","sound","trend","share",
    "party","light","party","grave","entry","pause","level","tasks","worry","rough",
    "notes","write","scene","sleep","wears","juice","speed","horse","eagle","happy"
    "faith","glory","honor","proud","brave","sharp","swift","peace","smoke","flame",
    "stone","river","ocean","tiger","eagle","horse","sheep","plant","grain","wheat",
    "sight","sound","taste","touch","smell","laugh","tears","anger","mercy","truth",
    "power","money","worth","value","price","trade","stock","share","funds","credit",
    "logic","reason","ideas","dream","think","learn","teach","study","focus","skill",
    "speed","force","energy","vigor","might","sweat","blood","bones","flesh","heart",
    "brain","nerves","cells","tissue","organ","vital","clean","dirty","rough","smooth",
    "round","sharp","blunt","thick","thin","heavy","light","quiet","loudy","noisy",
    "happy","sadly","angry","calms","proud","shame","bride","groom","child","elder"
    "vivid","frost","spark","amber","civic","rural","lunar","solar","orbit","comet",
    "quake","storm","cloud","rainy","windy","sunny","misty","foggy","chill","humid",
    "bison","zebra","koala","panda","otter","camel","llama","rhino","whale","shark",
    "coral","kelp","algae","tides","waves","sands","dunes","rocks","cliff","caves",
    "forge","anvil","metal","alloy","welds","screw","bolts","gears","lever","pulle",
    "codec","input","output","cache","stack","queue","array","logic","loops","flags",
    "mouse","keybd","screen","pixel","audio","video","frame","files","cloud","serve",
    "cargo","pilot","fleet","rails","roads","tolls","ports","canal","ships","trucks"

]

FALLBACK_ALLOWED = FALLBACK_SOLUTIONS + [
    "apple", "grape", "mango", "berry", "other", "there", "their", "which", "could", "would",
]

# --- Helpers ---

def load_wordlist(filename: str) -> List[str]:
    """Load a newline-separated wordlist and return lowercase 5-letter words."""
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        words = [w.strip().lower() for w in f if w.strip()]
    words = [w for w in words if len(w) == 5 and w.isalpha()]
    return words


def pick_solution(solutions: List[str], seed: Optional[int] = None) -> str:
    if seed is not None:
        random.seed(seed)
    return random.choice(solutions)


def get_feedback(guess: str, solution: str) -> List[str]:
    """
    Return feedback for each letter in guess as one of: 'green','yellow','gray'.
    Correctly handles repeated letters.
    """
    assert len(guess) == 5 and len(solution) == 5
    feedback = [None] * 5
    sol_chars = list(solution)

    # First pass: greens
    for i, ch in enumerate(guess):
        if ch == sol_chars[i]:
            feedback[i] = 'green'
            sol_chars[i] = None

    # Second pass: yellows and grays
    for i, ch in enumerate(guess):
        if feedback[i] is not None:
            continue
        if ch in sol_chars:
            feedback[i] = 'yellow'
            sol_chars[sol_chars.index(ch)] = None
        else:
            feedback[i] = 'gray'
    return feedback


def render_feedback(guess: str, feedback: List[str], use_color: bool = True) -> str:
    """Return a human-readable rendering of the feedback."""
    if use_color and _HAS_COLORAMA:
        out = []
        for ch, fb in zip(guess, feedback):
            if fb == 'green':
                out.append(Back.GREEN + Fore.BLACK + f' {ch.upper()} ' + Style.RESET_ALL)
            elif fb == 'yellow':
                out.append(Back.YELLOW + Fore.BLACK + f' {ch.upper()} ' + Style.RESET_ALL)
            else:
                out.append(Back.WHITE + Fore.BLACK + f' {ch.upper()} ' + Style.RESET_ALL)
        return ' '.join(out)
    else:
        emoji_map = {'green': '🟩', 'yellow': '🟨', 'gray': '⬛'}
        return ''.join(emoji_map[fb] for fb in feedback) + '  ' + guess.upper()


def clear_console():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass


# --- Input providers: avoid calling input() in non-interactive environments ---
class InputProvider:
    def next_guess(self, prompt: str) -> str:
        raise NotImplementedError


class InteractiveInput(InputProvider):
    def next_guess(self, prompt: str) -> str:
        # This may raise OSError in sandboxed environments; callers should only use
        # this provider when stdin.isatty() is True.
        return input(prompt)


class FileInput(InputProvider):
    def __init__(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        with open(path, 'r', encoding='utf-8') as f:
            lines = [l.strip().lower() for l in f if l.strip()]
        self._iter = iter(lines)

    def next_guess(self, prompt: str) -> str:
        return next(self._iter)  # may raise StopIteration when exhausted


class AutoInput(InputProvider):
    """Automatically yields guesses from the allowed list.

    Strategies supported:
      - 'random': shuffle allowed list (uses seed if provided)
      - 'sequential': iterate allowed list in order
    """
    def __init__(self, allowed: List[str], strategy: str = 'random', seed: Optional[int] = None):
        self.allowed = list(allowed)
        if strategy not in ('random', 'sequential'):
            raise ValueError('strategy must be random or sequential')
        self.strategy = strategy
        if seed is not None:
            random.seed(seed)
        if strategy == 'random':
            random.shuffle(self.allowed)
        self._iter = iter(self.allowed)

    def next_guess(self, prompt: str) -> str:
        return next(self._iter)


# --- Main game loop (safe; never calls input() directly) ---

def play_wordle(solutions: List[str], allowed: List[str], input_provider: InputProvider, *,
                attempts: int = 6, use_color: bool = True, solution_seed: Optional[int] = None,
                verbose: bool = True) -> Tuple[bool, int, List[Tuple[str, List[str]]]]:
    """
    Play a single game. Returns (won, attempts_used, guesses_and_feedback).

    The function relies on `input_provider.next_guess(prompt)` to obtain guesses.
    This makes it safe to run in automated/non-interactive environments.
    """
    solution = pick_solution(solutions, seed=solution_seed)
    guesses: List[Tuple[str, List[str]]] = []
    keyboard = {c: None for c in 'abcdefghijklmnopqrstuvwxyz'}

    for turn in range(1, attempts + 1):
        try:
            raw = input_provider.next_guess(f"Guess {turn}/{attempts} — enter a 5-letter word: ")
        except StopIteration:
            if verbose:
                print("No more guesses available from input provider — aborting game.")
            break
        except Exception as e:
            # Defensive: if an input provider unexpectedly raises (e.g., OSError),
            # abort the interactive flow and treat as game over.
            if verbose:
                print(f"Input provider raised an exception: {e} — aborting game.")
            break

        guess = (raw or '').strip().lower()

        # In interactive mode we usually want to re-prompt for invalid guesses. In
        # non-interactive modes, we can't re-prompt, so we'll skip invalid guesses
        # and continue to the next available one.
        if len(guess) != 5 or not guess.isalpha():
            if verbose:
                print(f"Skipping invalid guess: '{raw}'. Must be 5 alphabetic letters.")
            continue
        # Accept any valid 5-letter word (warn if it's not in the allowed list)
        if guess not in allowed and guess not in solutions and verbose:
            print(f"Note: '{guess}' not in allowed list — accepting it for evaluation.")

        fb = get_feedback(guess, solution)
        guesses.append((guess, fb))

        # Update keyboard
        for ch, status in zip(guess, fb):
            prev = keyboard[ch]
            if prev == 'green':
                continue
            if status == 'green':
                keyboard[ch] = 'green'
            elif status == 'yellow' and prev != 'green':
                keyboard[ch] = 'yellow'
            elif status == 'gray' and prev is None:
                keyboard[ch] = 'gray'

        # Render feedback
        if verbose:
            print(render_feedback(guess, fb, use_color=use_color))

        if guess == solution:
            if verbose:
                print(f"\n🎉 Congratulations — you guessed the word in {turn} attempt(s)! The word was: {solution.upper()}")
            return True, turn, guesses

        # Optionally show keyboard
        if verbose:
            row1 = 'qwertyuiop'
            row2 = 'asdfghjkl'
            row3 = 'zxcvbnm'

            def kb_row(row):
                out = []
                for c in row:
                    s = keyboard[c]
                    if use_color and _HAS_COLORAMA:
                        if s == 'green':
                            out.append(Back.GREEN + Fore.BLACK + f' {c.upper()} ' + Style.RESET_ALL)
                        elif s == 'yellow':
                            out.append(Back.YELLOW + Fore.BLACK + f' {c.upper()} ' + Style.RESET_ALL)
                        elif s == 'gray':
                            out.append(Back.WHITE + Fore.BLACK + f' {c.upper()} ' + Style.RESET_ALL)
                        else:
                            out.append(f' {c.upper()} ')
                    else:
                        emoji = {'green': '🟩', 'yellow': '🟨', 'gray': '⬛'}.get(s, '▫️')
                        out.append(emoji)
                return ' '.join(out)

            print('\nKeyboard:')
            print(kb_row(row1))
            print(kb_row(row2))
            print(kb_row(row3))
            print('\n')

    if verbose:
        print(f"😭 Out of attempts or no more guesses available. The word was: {solution.upper()}")
    return False, len(guesses), guesses


# --- Tests ---

def _test_get_feedback():
    # Repeated letters: solution has two 'p's
    fb = get_feedback('paper', 'apple')
    # p a p e r  vs a p p l e
    # guess p a p e r
    # expected: yellow (p in word but wrong pos), green (a==a), green (p==p), yellow (e in word), gray (r not in word)
    assert fb == ['yellow', 'green', 'green', 'yellow', 'gray'], f"fb={fb}"

    # Simple exact match
    assert get_feedback('cigar', 'cigar') == ['green'] * 5

    # No matches
    assert get_feedback('apple', 'cigar') == ['gray'] * 5

    print('get_feedback tests passed')


def _test_play_wordle_with_fileinput():
    # Simulate a game where the guesses file includes the correct answer on the 3rd guess
    solutions = ['abcde']
    allowed = ['abcde', 'xxxxx', 'aaaaa', 'bbbbb', 'ccccc']
    # Create a temporary guesses file content in memory (we'll use FileInput-like provider)
    class DummyFileInput(InputProvider):
        def __init__(self, guesses):
            self._iter = iter(guesses)
        def next_guess(self, prompt: str) -> str:
            return next(self._iter)

    guesses_sequence = ['xxxxx', 'aaaaa', 'abcde']
    provider = DummyFileInput(guesses_sequence)
    won, used, hist = play_wordle(solutions, allowed, provider, attempts=6, use_color=False, verbose=False)
    assert won is True
    assert used == 3
    assert hist[-1][0] == 'abcde'
    print('play_wordle fileinput simulation passed')


def _test_autoinput_determinism():
    # AutoInput with a seed should produce deterministic first guess order when strategy=random
    allowed = ['aaaaa', 'bbbbb', 'ccccc', 'abcde', 'zzzzz']
    provider1 = AutoInput(allowed, strategy='random', seed=12345)
    provider2 = AutoInput(allowed, strategy='random', seed=12345)
    first1 = provider1.next_guess('')
    first2 = provider2.next_guess('')
    assert first1 == first2, (first1, first2)
    print('autoinput determinism test passed')


def _test_fileinput_exhausted_behavior():
    # If FileInput runs out of guesses, play_wordle should stop gracefully
    solutions = ['xxxxx']
    allowed = ['xxxxx']
    class SmallFile(InputProvider):
        def __init__(self):
            self._iter = iter(['abcde'])
        def next_guess(self, prompt: str) -> str:
            return next(self._iter)
    provider = SmallFile()
    won, used, hist = play_wordle(solutions, allowed, provider, attempts=6, use_color=False, verbose=False)
    # provider had only 1 guess and it was invalid (not allowed), so no guesses were recorded
    assert won is False
    assert used == 0
    assert hist == []
    print('fileinput exhausted behavior test passed')


def _run_tests():
    _test_get_feedback()
    _test_play_wordle_with_fileinput()
    _test_autoinput_determinism()
    _test_fileinput_exhausted_behavior()
    print('All tests passed')


# --- CLI / Entrypoint ---

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='CLI Wordle (sandbox-safe)')
    parser.add_argument('--gui', action='store_true', help='Launch GUI instead of CLI')
    parser.add_argument('--cli', action='store_true', help='Force CLI mode (useful for running in terminals)')
    parser.add_argument('--solutions', type=str, default='solutions.txt')
    parser.add_argument('--allowed', type=str, default='allowed.txt')
    parser.add_argument('--guesses-file', type=str, default=None,
                        help='Non-interactive: read guesses from this newline-separated file')
    parser.add_argument('--autoplay', action='store_true', help='Non-interactive auto-guess from allowed list')
    parser.add_argument('--auto-strategy', type=str, default='random', choices=['random', 'sequential'])
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--run-tests', action='store_true', help='Run internal unit tests and exit')
    parser.add_argument('--no-color', action='store_true', help='Disable colorama even if available')
    args = parser.parse_args(argv)

    if args.run_tests:
        _run_tests()
        return 0
    if args.gui or (not args.cli and not args.autoplay and not args.guesses_file):
        # Launch GUI by default when no explicit --cli and not in autoplay/guesses-file mode
        style = TBStyle(theme="flatly")
        root = style.master
        app = WordleUI(root)
        root.mainloop()
        return 0

    solutions = load_wordlist(args.solutions) or FALLBACK_SOLUTIONS
    allowed = load_wordlist(args.allowed) or FALLBACK_ALLOWED

    # Ensure allowed contains solutions
    for w in solutions:
        if w not in allowed:
            allowed.append(w)

    # Decide input provider
    interactive = sys.stdin.isatty()
    provider: InputProvider

    if interactive and not args.autoplay and not args.guesses_file:
        # Use interactive input (safe because stdin is a tty)
        provider = InteractiveInput()
    else:
        # Non-interactive preferences
        if args.guesses_file:
            try:
                provider = FileInput(args.guesses_file)
            except Exception as e:
                print(f"Failed to open guesses file '{args.guesses_file}': {e}")
                print("Falling back to autoplay mode.")
                provider = AutoInput(allowed, strategy=args.auto_strategy, seed=args.seed)
        elif args.autoplay:
            provider = AutoInput(allowed, strategy=args.auto_strategy, seed=args.seed)
        else:
            # Non-interactive but no guesses specified: choose autoplay so script doesn't call input()
            print("Non-interactive environment detected and no guesses file provided. Entering autoplay mode.")
            provider = AutoInput(allowed, strategy=args.auto_strategy, seed=args.seed)

    use_color = (not args.no_color) and _HAS_COLORAMA

    # If interactive, keep prompting to play again. Otherwise run one game and exit.
    try:
        if interactive and isinstance(provider, InteractiveInput):
            print("Welcome to CLI Wordle — guess the 5-letter word in 6 tries!")
            print("Press Ctrl+C to quit any time.\n")
            while True:
                play_wordle(solutions, allowed, provider, attempts=6, use_color=use_color, solution_seed=args.seed)
                try:
                    again = input('\nPlay again? (y/n): ').strip().lower()
                except Exception:
                    # If input becomes unavailable mid-run, stop gracefully
                    break
                if not again or again[0] != 'y':
                    print('Thanks for playing — goodbye!')
                    break
                clear_console()
        else:
            # Non-interactive single run
            print("Running non-interactive Wordle (autoplay / guesses-file).")
            won, used, hist = play_wordle(solutions, allowed, provider, attempts=6, use_color=use_color, solution_seed=args.seed)
            print(f"Finished: won={won}, attempts_used={used}")
    except KeyboardInterrupt:
        print('\nInterrupted. Goodbye!')
        return 0
    return 0


# Entry point moved to the bottom to ensure GUI classes are defined before running main()
# (See end of file for actual entrypoint)

WORD_LENGTH = 5
MAX_ATTEMPTS = 6
# small sample word list (replace/extend as needed)
WORD_LIST = ["apple", "grape", "lemon", "melon", "mango", "banjo", "crane", "flame"]

# colors (Wordle-like)
COLOR_CORRECT = "#6aaa64"   # green
COLOR_PRESENT = "#c9b458"   # yellow
COLOR_ABSENT = "#787c7e"    # gray
COLOR_EMPTY = "#1e1e1e"
TEXT_COLOR = "#000000"

class WordleUI:
    def __init__(self, master):
        self.style = TBStyle(theme="flatly")
        self.root = master

        self.target = random.choice(FALLBACK_SOLUTIONS).lower()
        self.attempt = 0
        self.col = 0
        self.board = [[""] * WORD_LENGTH for _ in range(MAX_ATTEMPTS)]
        self.labels = [[None] * WORD_LENGTH for _ in range(MAX_ATTEMPTS)]
        self.key_buttons = {}
        self.guess_buffer = [""] * WORD_LENGTH
        self.disabled = False

        self.setup_ui()
        self.root.bind("<Key>", self.on_key)

    def setup_ui(self):
        self.root.title("Wordle (Tkinter)")

        # Main layout: left reveal panel, center grid, right controls
        # Outer frame fills the window; content_frame is centered inside it so the layout stays centered in fullscreen
        outer_frame = tk.Frame(self.root)
        outer_frame.pack(fill='both', expand=True)

        content_frame = tk.Frame(outer_frame)
        # place it centered at the top (so it doesn't stretch across entire window)
        content_frame.place(relx=0.5, rely=0.02, anchor='n')
        # configure three columns inside content_frame: reveal (col0), center (col1), controls (col2)
        content_frame.columnconfigure(0, minsize=140)
        content_frame.columnconfigure(1, minsize=350)
        content_frame.columnconfigure(2, minsize=120)

        # Left: reveal panel (hidden initially) - will be gridded into column 0 when used
        self.reveal_panel = tk.Frame(content_frame, width=160)
        self.reveal_panel.grid_columnconfigure(0, weight=1)
        self.reveal_panel.pack_propagate(False)
        self._reveal_labels = []
        # do not grid it now; it will be shown on reveal with grid()

        # Center: grid and status (placed in column 1, centered)
        center_frame = tk.Frame(content_frame)
        center_frame.grid(row=0, column=1, sticky='n')

        grid_frame = tk.Frame(center_frame)
        grid_frame.pack()
        for r in range(MAX_ATTEMPTS):
            for c in range(WORD_LENGTH):
                lbl = tk.Label(grid_frame, text="",
                               width=4, height=2, font=("Helvetica", 20, "bold"),
                               bg=COLOR_EMPTY, relief="solid", borderwidth=2)
                lbl.grid(row=r, column=c, padx=5, pady=5)
                self.labels[r][c] = lbl

        self.status = tk.Label(center_frame, text=f"Guess the {WORD_LENGTH}-letter word", fg="black")
        self.status.pack(pady=(6, 8))

        # Controls: place immediately to the right of the center grid so they're nearby
        # Controls are placed into the centered content_frame's column 2 so they remain close to the grid
        ctrl_frame = tk.Frame(content_frame)
        ctrl_frame.grid(row=0, column=2, sticky='n', padx=(8,6))

        submit_btn = tk.Button(ctrl_frame, text="Submit", command=self.submit_guess, width=10)
        submit_btn.pack(pady=4)
        restart_btn = tk.Button(ctrl_frame, text="Restart", command=self.restart_game, width=10)
        restart_btn.pack(pady=4)
        hint_btn = tk.Button(ctrl_frame, text="Reveal", command=self.reveal_answer, width=10)
        hint_btn.pack(pady=4)

        # on-screen keyboard (centered under the grid)
        kb_frame = tk.Frame(center_frame)
        # reduce vertical spacing so keyboard uses less screen space
        kb_frame.pack(pady=6)
        # allow the window to be resized and set a sensible minimum size
        self.root.resizable(True, True)
        self.root.minsize(420, 440)

        # store default key background colors so we can reliably reset later
        self.key_default_bg = {}
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for ri, row in enumerate(rows):
            row_frame = tk.Frame(kb_frame)
            # center rows and make them compact
            row_frame.pack(anchor='center', pady=1)
            # smaller spacer for the third row
            if ri == 2:
                spacer = tk.Frame(row_frame, width=8)
                spacer.pack(side="left")
            for ch in row:
                # make buttons compact so the keyboard takes less horizontal space
                btn = tk.Button(row_frame, text=ch, width=3, height=1, font=("Helvetica", 10),
                                command=lambda ch=ch: self.on_screen_key(ch))
                btn.pack(side="left", padx=1, pady=1)
                self.key_buttons[ch] = btn
                self.key_default_bg[ch] = btn.cget("bg")

    # keyboard handlers
    def on_screen_key(self, ch):
        if self.disabled:
            return
        self.input_letter(ch)

    def on_key(self, event):
        if self.disabled:
            return
        k = event.keysym
        if k == "BackSpace":
            self.delete_letter()
        elif k in ("Return", "KP_Enter"):
            self.submit_guess()
        else:
            ch = event.char.upper()
            if ch and ch in string.ascii_uppercase and len(ch) == 1:
                self.input_letter(ch)

    # input helpers
    def input_letter(self, ch):
        if self.col >= WORD_LENGTH or self.attempt >= MAX_ATTEMPTS:
            return
        self.guess_buffer[self.col] = ch
        lbl = self.labels[self.attempt][self.col]
        lbl.config(text=ch)
        # briefly highlight pressed on-screen key if present
        btn = self.key_buttons.get(ch)
        if btn:
            btn.config(relief="sunken")
            self.root.after(120, lambda b=btn: b.config(relief="raised"))
        self.col += 1

    def delete_letter(self):
        if self.col == 0:
            return
        self.col -= 1
        self.guess_buffer[self.col] = ""
        lbl = self.labels[self.attempt][self.col]
        lbl.config(text="")

    def submit_guess(self):
        if self.col != WORD_LENGTH:
            self.status.config(text=f"Enter {WORD_LENGTH} letters.", fg="red")
            return
        guess = "".join(self.guess_buffer).lower()
        # optional: require guess in list
        # if guess not in WORD_LIST:
        #     self.status.config(text="Not in word list.", fg="red")
        #     return

        # feedback algorithm: mark greens first, then yellows with counts
        status = ["absent"] * WORD_LENGTH
        target_counts = {}
        for i in range(WORD_LENGTH):
            if guess[i] == self.target[i]:
                status[i] = "correct"
            else:
                target_counts[self.target[i]] = target_counts.get(self.target[i], 0) + 1

        for i in range(WORD_LENGTH):
            ch = guess[i]
            lbl = self.labels[self.attempt][i]
            if status[i] == "correct":
                lbl.config(bg=COLOR_CORRECT, fg="white")
                self.update_key_color(ch, "correct")
            elif target_counts.get(ch, 0) > 0:
                status[i] = "present"
                target_counts[ch] -= 1
                lbl.config(bg=COLOR_PRESENT, fg="white")
                self.update_key_color(ch, "present")
            else:
                lbl.config(bg=COLOR_ABSENT, fg="white")
                self.update_key_color(ch, "absent")

        # Check win/loss
        if guess == self.target:
            self.status.config(text=f"🎉 You got it! {self.target.upper()}", fg="green")
            self.end_game(win=True)
            return

        # move to next attempt
        self.attempt += 1
        self.col = 0
        self.guess_buffer = [""] * WORD_LENGTH
        if self.attempt >= MAX_ATTEMPTS:
            self.status.config(text=f"Out of attempts. Answer: {self.target.upper()}", fg="red")
            self.end_game(win=False)
        else:
            self.status.config(text=f"Attempt {self.attempt+1}/{MAX_ATTEMPTS}", fg="black")

    def update_key_color(self, ch, new_status):
        ch = ch.upper()
        btn = self.key_buttons.get(ch)
        if not btn:
            return
        # priority: correct > present > absent (don't downgrade)
        current_bg = btn.cget("bg")
        if new_status == "correct":
            btn.config(bg=COLOR_CORRECT, fg="white")
        elif new_status == "present":
            if current_bg != COLOR_CORRECT:
                btn.config(bg=COLOR_PRESENT, fg="white")
        elif new_status == "absent":
            if current_bg not in (COLOR_CORRECT, COLOR_PRESENT):
                btn.config(bg=COLOR_ABSENT, fg="white")

    def end_game(self, win):
        self.disabled = True
        # optionally disable keyboard buttons
        for b in self.key_buttons.values():
            b.config(state="disabled")

    def restart_game(self):
        self.target = random.choice(FALLBACK_SOLUTIONS).lower()
        self.attempt = 0
        self.col = 0
        self.guess_buffer = [""] * WORD_LENGTH
        self.disabled = False
        self.status.config(text=f"Guess the {WORD_LENGTH}-letter word", fg="black")
        # reset grid
        for r in range(MAX_ATTEMPTS):
            for c in range(WORD_LENGTH):
                lbl = self.labels[r][c]
                lbl.config(text="", bg=COLOR_EMPTY, fg=TEXT_COLOR)
        # reset keys to their original background and re-enable them
        for ch, b in self.key_buttons.items():
            default_bg = self.key_default_bg.get(ch)
            if default_bg is not None:
                b.config(bg=default_bg, fg="black", state="normal")
            else:
                b.config(fg="black", state="normal")
        # hide/clear reveal panel
        for child in self.reveal_panel.winfo_children():
            child.destroy()
        self._reveal_labels = []
        # hide reveal panel if it's shown (use grid_forget since we grid it when visible)
        try:
            self.reveal_panel.grid_forget()
        except Exception:
            pass
        # rebind keys
        self.root.bind("<Key>", self.on_key)

    def reveal_answer(self):
        # Show a left-side panel with the answer rendered as Wordle-like boxes
        for child in self.reveal_panel.winfo_children():
            child.destroy()
        # Title
        title = tk.Label(self.reveal_panel, text="Answer", font=("Helvetica", 12, "bold"))
        title.pack(pady=(6, 8))
        box_frame = tk.Frame(self.reveal_panel)
        box_frame.pack(pady=6)
        for ch in self.target.upper():
            lbl = tk.Label(box_frame, text=ch, width=4, height=2, font=("Helvetica", 18, "bold"),
                           bg=COLOR_CORRECT, fg="white", relief="solid", borderwidth=2)
            lbl.pack(pady=4)
            self._reveal_labels.append(lbl)

        # ensure the panel is visible (grid into column 0); set explicit width and force layout update
        try:
            self.reveal_panel.configure(width=140)
            self.reveal_panel.grid(row=0, column=0, sticky='n', padx=(0,12), pady=6)
            self.reveal_panel.lift()
            self.root.update_idletasks()
        except Exception:
            # If layout fails, fallback to a popup so the user still sees the answer
            messagebox.showinfo("Answer", f"The word is: {self.target.upper()}")
            self.status.config(text=f"Answer revealed (popup).", fg="black")
            return

        # Verify the panel is actually visible; if not, show a popup as a fallback
        try:
            if not self.reveal_panel.winfo_ismapped():
                messagebox.showinfo("Answer", f"The word is: {self.target.upper()}")
                self.status.config(text=f"Answer revealed (popup).", fg="black")
                return
        except Exception:
            # ignore and continue
            pass

        # show a hint in the status as well
        self.status.config(text=f"Answer revealed.", fg="black")


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        code = e.code if hasattr(e, 'code') else None
        if code and code != 0:
            print(f"Program exited with SystemExit({code})", file=sys.stderr)
    except Exception as e:
        print(f"Unhandled exception while running main(): {e}", file=sys.stderr)
