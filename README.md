This is a Wordle game implementation with both CLI and GUI modes. Here's what it does:

Core Features:
Game Logic: Classic Wordle gameplay — guess a 5-letter word in 6 attempts with color-coded feedback (green for correct position, yellow for correct letter wrong position, gray for absent)
Feedback System: Handles repeated letters correctly using a two-pass algorithm
Multiple Input Modes:
Interactive CLI: Direct user input via terminal
File-based: Read guesses from a file
Auto-play: Automatically generate guesses (random or sequential)
GUI: Full Tkinter interface with on-screen keyboard and visual feedback
GUI Components:
Game Board: 6x5 grid showing guesses with color-coded tiles
On-screen Keyboard: QWERTY layout that highlights key states as you play
Controls: Submit, Restart, and Reveal buttons
Answer Reveal: Shows the correct word in a side panel or popup
Additional Features:
Word Lists: Uses fallback word lists (hardcoded) but can load custom lists from solutions.txt and allowed.txt
Color Support: Optional colorama library for terminal colors
Deterministic Mode: Seed support for reproducible games
Unit Tests: Built-in tests for game logic validation
Sandbox-Safe: Designed to avoid input() calls in non-interactive environments
