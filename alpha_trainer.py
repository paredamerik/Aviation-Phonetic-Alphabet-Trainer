# =====================================================================
# Aviation Phonetic Alphabet Trainer
# Copyright (C) 2026 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =====================================================================

import difflib
import io
import queue
import random
import subprocess
import threading
import wave
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import tkinter as tk
from tkinter import ttk

# Official ICAO Aviation Phonetic Alphabet Reference Table
PHONETIC_CHART = [
    ("A", "ALFA", "AL fah"),
    ("B", "BRAVO", "BRAH VOH"),
    ("C", "CHARLIE", "CHAR lee"),
    ("D", "DELTA", "DELL tah"),
    ("E", "ECHO", "ECK oh"),
    ("F", "FOXTROT", "FOKS trot"),
    ("G", "GOLF", "GOLF"),
    ("H", "HOTEL", "Hoh TELL"),
    ("I", "INDIA", "IN dee ah"),
    ("J", "JULIETT", "JEW lee ETT"),
    ("K", "KILO", "KEY loh"),
    ("L", "LIMA", "LEE mah"),
    ("M", "MIKE", "MIKE"),
    ("N", "NOVEMBER", "No VEM ber"),
    ("O", "OSCAR", "OSS cah"),
    ("P", "PAPA", "Pah PAH"),
    ("Q", "QUEBEC", "Keh BECK"),
    ("R", "ROMEO", "ROW me oh"),
    ("S", "SIERRA", "See AIR ah"),
    ("T", "TANGO", "TANG go"),
    ("U", "UNIFORM", "YOU nee form"),
    ("V", "VICTOR", "VIK tah"),
    ("W", "WHISKEY", "WISS key"),
    ("X", "X-RAY", "ECKS Ray"),
    ("Y", "YANKEE", "YANG key"),
    ("Z", "ZULU", "ZOO loo")
]

PHONETIC_ALPHABET = {item[0]: item[1] for item in PHONETIC_CHART}
PHONETIC_PRONUNCIATION = {item[0]: item[2] for item in PHONETIC_CHART}
PHONETIC_DISPLAY_FORMAT = {item[0]: f"{item[0]} - {item[1]} - {item[2]}" for item in PHONETIC_CHART}

# Expanded aliases including common speech recognition quirks
PHONETIC_ALIASES = {
    'A': ['ALFA', 'ALPHA', 'ALBA'],
    'B': ['BRAVO'],
    'C': ['CHARLIE', 'SHARLIE'],
    'D': ['DELTA'],
    'E': ['ECHO'],
    'F': ['FOXTROT', 'FOX TROT'],
    'G': ['GOLF', 'CALL', 'GO', 'GOL'],
    'H': ['HOTEL'],
    'I': ['INDIA'],
    'J': ['JULIETT', 'JULIET'],
    'K': ['KILO', 'KEY LOW'],
    'L': ['LIMA', 'LEEMA'],
    'M': ['MIKE'],
    'N': ['NOVEMBER'],
    'O': ['OSCAR'],
    'P': ['PAPA'],
    'Q': ['QUEBEC'],
    'R': ['ROMEO'],
    'S': ['SIERRA', 'CIERRA', 'CIARA', 'SEERA', 'SERRA'],
    'T': ['TANGO', 'TENGO'],
    'U': ['UNIFORM'],
    'V': ['VICTOR'],
    'W': ['WHISKEY'],
    'X': ['XRAY', 'X-RAY', 'EXRAY'],
    'Y': ['YANKEE', 'YANG key', 'YANKY', 'FRANKIE'],
    'Z': ['ZULU']
}

class AviationTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aviation Phonetic Alphabet Trainer")
        self.root.geometry("520x960")
        self.root.config(bg="#1e1e1e")

        # Tracking variables
        self.letters = list(PHONETIC_ALPHABET.keys())
        self.miss_counts = {letter: 0 for letter in self.letters}
        self.success_counts = {letter: 0 for letter in self.letters}
        self.unheard_counts = {letter: 0 for letter in self.letters}
        
        # Progression Queues
        self.initial_queue = []
        self.review_queue = set()
        self.mastered_letters = set()
        
        # Word Speedrun Queues & Tracking
        self.word_speedrun_queue = []
        self.word_speedrun_round = 0
        self.word_speedrun_total_rounds = 15
        self.current_word_sequence = []
        self.word_round_logs = []  # Stores details of each 4-letter round for summary review
        
        # Log actual understood/heard words per letter for single-letter modes
        self.letter_logs = {letter: {'success': [], 'miss': [], 'unheard': []} for letter in self.letters}
        
        self.total_attempts = 0
        self.correct_attempts = 0
        self.current_letter = None
        
        # State control variables
        self.is_running = False
        self.is_paused = False
        self.is_listening = False
        
        # Thread-safe communication queue
        self.queue = queue.Queue()

        self.recognizer = sr.Recognizer()
        self.samplerate = 16000
        self.channels = 1

        self.setup_ui()
        
        # Start checking the thread-safe queue from the main thread
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        # Main Title
        title_label = tk.Label(
            self.root, text="✈️ Aviation Alphabet Trainer", 
            font=("Helvetica", 16, "bold"), fg="white", bg="#1e1e1e"
        )
        title_label.pack(pady=8)

        # Control Panel Frame (Start, Pause, Stop, Reset)
        control_frame = tk.Frame(self.root, bg="#1e1e1e")
        control_frame.pack(pady=3)

        self.start_btn = tk.Button(control_frame, text="▶ Start", font=("Helvetica", 10, "bold"), bg="#28a745", fg="white", padx=8, command=self.start_trainer)
        self.start_btn.grid(row=0, column=0, padx=3)

        self.pause_btn = tk.Button(control_frame, text="⏸ Pause", font=("Helvetica", 10, "bold"), bg="#ffc107", fg="black", padx=8, command=self.pause_trainer, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=3)

        self.stop_btn = tk.Button(control_frame, text="⏹ Stop & Summary", font=("Helvetica", 10, "bold"), bg="#dc3545", fg="white", padx=8, command=self.stop_trainer, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=3)

        self.reset_btn = tk.Button(control_frame, text="🔄 Reset", font=("Helvetica", 10, "bold"), bg="#6c757d", fg="white", padx=8, command=self.reset_trainer)
        self.reset_btn.grid(row=0, column=3, padx=3)

        # --- GAME FRAME ---
        self.game_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.game_frame.pack(fill="both", expand=True)

        # Progress Tracker Label in Main Window
        self.progress_tracker_label = tk.Label(
            self.game_frame, text="Alphabet Mastery: 0 / 26 letters mastered", 
            font=("Helvetica", 11, "bold"), fg="#ffcc00", bg="#1e1e1e"
        )
        self.progress_tracker_label.pack(pady=4)

        # Traffic Light Canvas
        self.canvas = tk.Canvas(self.game_frame, width=80, height=80, bg="#1e1e1e", highlightthickness=0)
        self.light_circle = self.canvas.create_oval(10, 10, 70, 70, fill="gray")
        self.canvas.pack(pady=2)

        # Letter / Sequence Display
        self.letter_label = tk.Label(
            self.game_frame, text="-", 
            font=("Helvetica", 32, "bold"), fg="#ffcc00", bg="#1e1e1e"
        )
        self.letter_label.pack(pady=2)

        # Status Indicator Label (Shows Red or Green Microphone)
        self.mic_status_label = tk.Label(
            self.game_frame, text="🎙️ (Standby)", 
            font=("Helvetica", 14, "bold"), fg="#ff4d4d", bg="#1e1e1e"
        )
        self.mic_status_label.pack(pady=2)

        # Pronunciation Guide Sub-label
        self.guide_label = tk.Label(
            self.game_frame, text="", 
            font=("Helvetica", 12, "bold"), fg="#4da6ff", bg="#1e1e1e"
        )
        self.guide_label.pack(pady=2)

        # Status Label
        self.status_label = tk.Label(
            self.game_frame, text="Click 'Start' to begin training.", 
            font=("Helvetica", 10), fg="#aaaaaa", bg="#1e1e1e", wraplength=420
        )
        self.status_label.pack(pady=4)

        # Mode Selection Frame (Radio Buttons for Mode Selection)
        mode_frame = tk.LabelFrame(
            self.game_frame, text=" Training Mode ", 
            font=("Helvetica", 9, "bold"), fg="#aaaaaa", bg="#1e1e1e", padx=10, pady=4
        )
        mode_frame.pack(pady=2, fill="x", padx=30)

        # Mode Variable: 0 = Learning Mode, 1 = Speedrun Mode, 2 = Word Speedrun Mode
        self.mode_var = tk.IntVar(value=0)

        self.mode_rb1 = tk.Radiobutton(
            mode_frame, text="🔊 Learning Mode",
            variable=self.mode_var, value=0,
            font=("Helvetica", 9), fg="#4da6ff", bg="#1e1e1e",
            selectcolor="#333333", activebackground="#1e1e1e", activeforeground="white"
        )
        self.mode_rb1.pack(anchor="w", pady=1)

        self.mode_rb2 = tk.Radiobutton(
            mode_frame, text="⚡ Speedrun Mode (Instant Next)",
            variable=self.mode_var, value=1,
            font=("Helvetica", 9), fg="#ffdd57", bg="#1e1e1e",
            selectcolor="#333333", activebackground="#1e1e1e", activeforeground="white"
        )
        self.mode_rb2.pack(anchor="w", pady=1)

        self.mode_rb3 = tk.Radiobutton(
            mode_frame, text="🔤 Word Speedrun (4 Letters, 15 Rounds)",
            variable=self.mode_var, value=2,
            font=("Helvetica", 9), fg="#00ffcc", bg="#1e1e1e",
            selectcolor="#333333", activebackground="#1e1e1e", activeforeground="white"
        )
        self.mode_rb3.pack(anchor="w", pady=1)

        # Custom Words Input for Word Speedrun
        custom_frame = tk.Frame(mode_frame, bg="#1e1e1e")
        custom_frame.pack(anchor="w", fill="x", padx=20, pady=2)

        tk.Label(
            custom_frame, text="Custom Words (Word Speedrun, space-separated):", 
            font=("Helvetica", 8), fg="#aaaaaa", bg="#1e1e1e"
        ).pack(anchor="w")

        self.custom_words_cb = ttk.Combobox(custom_frame, font=("Helvetica", 9), width=32)
        self.custom_words_cb.pack(anchor="w", pady=2)
        self.custom_words_cb['values'] = ("TEST CODE FLIGHT", "AVION RADAR PILOT", "SKY JET WING")

        # Reference Chart Button
        self.chart_btn = tk.Button(
            self.game_frame, text="📖 Alphabet Reference Chart", 
            font=("Helvetica", 9, "bold"), bg="#495057", fg="white",
            padx=8, pady=3, command=self.show_reference_chart, relief="flat"
        )
        self.chart_btn.pack(pady=4)

        # Stats Label
        self.stats_label = tk.Label(
            self.game_frame, text="Score: 0/0 (0%) | Review Queue: 0", 
            font=("Helvetica", 9), fg="#888888", bg="#1e1e1e"
        )
        self.stats_label.pack(side="bottom", pady=4)

        # --- SUMMARY FRAME (Hidden Initially) ---
        self.summary_frame = tk.Frame(self.root, bg="#1e1e1e")

        summary_title = tk.Label(self.summary_frame, text="📊 Session Summary", font=("Helvetica", 14, "bold"), fg="white", bg="#1e1e1e")
        summary_title.pack(pady=10)

        self.summary_text_box = tk.Text(self.summary_frame, height=20, width=58, bg="#2d2d2d", fg="white", font=("Courier", 10))
        self.summary_text_box.pack(pady=5)

    def set_light(self, color):
        self.canvas.itemconfig(self.light_circle, fill=color)

    def start_trainer(self):
        self.is_running = True
        self.is_paused = False
        
        current_mode = self.mode_var.get()
        if current_mode == 2:
            self.word_speedrun_round = 0
            self.word_round_logs.clear()
            
            custom_input = self.custom_words_cb.get().strip()
            custom_sequences = []
            if custom_input:
                raw_words = custom_input.split()
                for word in raw_words:
                    clean_word = "".join([c.upper() for c in word if c.upper() in self.letters])
                    if clean_word:
                        if len(clean_word) < 4:
                            while len(clean_word) < 4:
                                clean_word += random.choice(self.letters)
                        elif len(clean_word) > 4:
                            clean_word = clean_word[:4]
                        custom_sequences.append(list(clean_word))
            
            random.shuffle(custom_sequences)
            self.word_speedrun_queue = list(custom_sequences)
            while len(self.word_speedrun_queue) < self.word_speedrun_total_rounds:
                self.word_speedrun_queue.append(random.choices(self.letters, k=4))
            
            if len(self.word_speedrun_queue) > self.word_speedrun_total_rounds:
                self.word_speedrun_queue = self.word_speedrun_queue[:self.word_speedrun_total_rounds]
        else:
            self.initial_queue = list(self.letters)
            random.shuffle(self.initial_queue)
            self.review_queue.clear()
            self.mastered_letters.clear()
        
        self.start_btn.config(state=tk.DISABLED)
        self.mode_rb1.config(state=tk.DISABLED)
        self.mode_rb2.config(state=tk.DISABLED)
        self.mode_rb3.config(state=tk.DISABLED)
        self.custom_words_cb.config(state=tk.DISABLED)
        
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.update_progress_display()
        self.run_countdown(3)

    def run_countdown(self, count):
        if not self.is_running:
            return
        if count > 0:
            self.letter_label.config(text=str(count), fg="#ffcc00")
            self.mic_status_label.config(text="🎙️ (Wait)", fg="#ff4d4d")
            self.guide_label.config(text="")
            self.status_label.config(text="Get ready...")
            self.set_light("red")
            self.root.after(1000, lambda: self.run_countdown(count - 1))
        elif count == 0:
            self.letter_label.config(text="GO!", fg="#28a745")
            self.mic_status_label.config(text="🎙️ (Live)", fg="#28a745")
            self.status_label.config(text="Training started!")
            self.set_light("green")
            self.root.after(600, self.begin_actual_trainer)

    def begin_actual_trainer(self):
        if not self.is_running:
            return
        self.pause_btn.config(state=tk.NORMAL, text="⏸ Pause")
        self.stop_btn.config(state=tk.NORMAL)
        self.next_letter()

    def pause_trainer(self):
        if not self.is_running:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.config(text="⏸ Pause")
            self.status_label.config(text="Resuming...")
            self.next_letter()
        else:
            self.is_paused = True
            self.pause_btn.config(text="▶ Resume")
            self.set_light("gray")
            self.mic_status_label.config(text="🎙️ (Paused)", fg="#888888")
            self.status_label.config(text="Trainer Paused.")

    def stop_trainer(self):
        self.is_running = False
        self.is_paused = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏸ Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.set_light("gray")
        self.mic_status_label.config(text="🎙️ (Standby)", fg="#ff4d4d")
        self.guide_label.config(text="")

        self.show_summary_screen()

    def reset_trainer(self):
        self.is_running = False
        self.is_paused = False
        self.total_attempts = 0
        self.correct_attempts = 0
        self.current_letter = None
        self.current_word_sequence = []
        self.word_speedrun_round = 0
        self.word_round_logs.clear()
        self.miss_counts = {letter: 0 for letter in self.letters}
        self.success_counts = {letter: 0 for letter in self.letters}
        self.unheard_counts = {letter: 0 for letter in self.letters}
        self.initial_queue = []
        self.review_queue.clear()
        self.mastered_letters.clear()
        self.letter_logs = {letter: {'success': [], 'miss': [], 'unheard': []} for letter in self.letters}
        
        self.start_btn.config(state=tk.NORMAL)
        self.mode_rb1.config(state=tk.NORMAL)
        self.mode_rb2.config(state=tk.NORMAL)
        self.mode_rb3.config(state=tk.NORMAL)
        self.custom_words_cb.config(state=tk.NORMAL)
        
        self.pause_btn.config(state=tk.DISABLED, text="⏸ Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.set_light("gray")
        self.letter_label.config(text="-", fg="#ffcc00")
        self.mic_status_label.config(text="🎙️ (Standby)", fg="#ff4d4d")
        self.guide_label.config(text="")
        self.status_label.config(text="Trainer reset. Click 'Start' to begin.")
        self.progress_tracker_label.config(text="Alphabet Mastery: 0 / 26 letters mastered")
        self.stats_label.config(text="Score: 0/0 (0%) | Review Queue: 0")
        self.summary_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)

    def show_reference_chart(self):
        chart_win = tk.Toplevel(self.root)
        chart_win.title("Phonetic Alphabet Reference Chart")
        chart_win.geometry("450x550")
        chart_win.config(bg="#1e1e1e")

        title = tk.Label(chart_win, text="Phonetic Alphabet Reference", font=("Helvetica", 14, "bold"), fg="white", bg="#1e1e1e")
        title.pack(pady=10)

        chart_text = tk.Text(chart_win, height=26, width=48, bg="#2d2d2d", fg="white", font=("Courier", 10))
        chart_text.pack(pady=5)

        lines = ["Alphabet   Pronunciation"]
        lines.append("-" * 30)
        for letter, word, pron in PHONETIC_CHART:
            lines.append(f"{letter} – {word:<9} {pron}")

        chart_text.insert(tk.END, "\n".join(lines))
        chart_text.config(state=tk.DISABLED)

    def show_summary_screen(self):
        self.game_frame.pack_forget()
        self.summary_frame.pack(fill="both", expand=True)

        accuracy = int((self.correct_attempts / self.total_attempts) * 100) if self.total_attempts > 0 else 0
        summary_lines = []
        current_mode = self.mode_var.get()
        
        if current_mode == 2:
            summary_lines.append(f"🔤 WORD SPEEDRUN MODE SUMMARY\n")
            summary_lines.append(f"Total Rounds Completed: {self.word_speedrun_round} / {self.word_speedrun_total_rounds}")
            summary_lines.append(f"Total Attempts : {self.total_attempts}")
            summary_lines.append(f"Correct Answers: {self.correct_attempts}")
            summary_lines.append(f"Overall Accuracy: {accuracy}%\n")
            
            summary_lines.append("=== ✅ SUCCESSFUL WORD SEQUENCES ===")
            successful_rounds = [r for r in self.word_round_logs if r['success']]
            if successful_rounds:
                for idx, r in enumerate(successful_rounds, 1):
                    letters_str = "".join(r['letters'])
                    summary_lines.append(f" {idx}. [{letters_str}] -> Expected: {r['expected']}")
                    summary_lines.append(f"    Heard: '{r['spoken']}'")
            else:
                summary_lines.append("    (None recorded yet)")

            summary_lines.append("\n=== ❌ MISSED WORD SEQUENCES ===")
            missed_rounds = [r for r in self.word_round_logs if not r['success']]
            if missed_rounds:
                for idx, r in enumerate(missed_rounds, 1):
                    letters_str = "".join(r['letters'])
                    summary_lines.append(f" {idx}. [{letters_str}] -> Expected: {r['expected']}")
                    summary_lines.append(f"    Heard: '{r['spoken']}'")
            else:
                summary_lines.append("    (None!)")
        else:
            is_perfect_run = (self.total_attempts == 26 and self.correct_attempts == 26 and 
                             sum(self.miss_counts.values()) == 0 and sum(self.unheard_counts.values()) == 0)
            
            if is_perfect_run:
                summary_lines.append("🏆 ACE PILOT ACHIEVEMENT UNLOCKED! 🏆")
                summary_lines.append("✨ PERFECT 26 / 26 ON YOUR FIRST PASS! ✨\n")
            else:
                summary_lines.append("🎉 100% ALPHABET COMPLETE SESSION SUMMARY\n")
                
            summary_lines.append(f"Total Attempts : {self.total_attempts}")
            summary_lines.append(f"Correct Answers: {self.correct_attempts}")
            summary_lines.append(f"Overall Accuracy: {accuracy}%\n")
        
            summary_lines.append("=== ✅ SUCCESSFUL LETTERS ===")
            successful_items = [(l, c) for l, c in self.success_counts.items() if c > 0]
            successful_items.sort(key=lambda x: x[1], reverse=True)
            if successful_items:
                for letter, count in successful_items:
                    word = PHONETIC_ALPHABET[letter]
                    pron = PHONETIC_PRONUNCIATION[letter]
                    heard_list = ", ".join(set(self.letter_logs[letter]['success']))
                    summary_lines.append(f" • {letter} - {word} - {pron} : {count} correct")
                    summary_lines.append(f"    Heard: [{heard_list}]")
            else:
                summary_lines.append("    (None recorded yet)")

            summary_lines.append("\n=== ⚠️ UNHEARD / NOT UNDERSTOOD ===")
            unheard_items = [(l, c) for l, c in self.unheard_counts.items() if c > 0]
            unheard_items.sort(key=lambda x: x[1], reverse=True)
            if unheard_items:
                for letter, count in unheard_items:
                    word = PHONETIC_ALPHABET[letter]
                    pron = PHONETIC_PRONUNCIATION[letter]
                    summary_lines.append(f" • {letter} - {word} - {pron} : Unheard {count} time(s)")
            else:
                summary_lines.append("    (None)")

            summary_lines.append("\n=== ❌ INCORRECT / MISSED LETTERS ===")
            missed_items = [(l, c) for l, c in self.miss_counts.items() if c > 0]
            missed_items.sort(key=lambda x: x[1], reverse=True)
            if missed_items:
                for letter, count in missed_items:
                    word = PHONETIC_ALPHABET[letter]
                    pron = PHONETIC_PRONUNCIATION[letter]
                    heard_list = ", ".join(set(self.letter_logs[letter]['miss']))
                    summary_lines.append(f" • {letter} - {word} - {pron} : Missed {count} time(s)")
                    summary_lines.append(f"    Heard: [{heard_list}]")
            else:
                summary_lines.append("    (None!)")

        self.summary_text_box.config(state=tk.NORMAL)
        self.summary_text_box.delete("1.0", tk.END)
        self.summary_text_box.insert(tk.END, "\n".join(summary_lines))
        self.summary_text_box.config(state=tk.DISABLED)

    def update_progress_display(self):
        current_mode = self.mode_var.get()
        if current_mode == 2:
            self.progress_tracker_label.config(text=f"Word Speedrun: Round {self.word_speedrun_round} / {self.word_speedrun_total_rounds}")
        else:
            mastered_count = len(self.mastered_letters)
            self.progress_tracker_label.config(text=f"Alphabet Mastery: {mastered_count} / 26 letters mastered")

    def next_letter(self):
        if not self.is_running or self.is_paused:
            return

        current_mode = self.mode_var.get()

        if current_mode == 2:
            if self.word_speedrun_round >= self.word_speedrun_total_rounds or not self.word_speedrun_queue:
                self.status_label.config(text="🎉 Word Speedrun Complete! Generating summary...")
                self.set_light("green")
                self.root.after(1500, self.stop_trainer)
                return

            self.current_word_sequence = self.word_speedrun_queue.pop(0)
            self.word_speedrun_round += 1
            self.update_progress_display()

            display_str = "  ".join(self.current_word_sequence)
            self.letter_label.config(text=display_str, fg="#00ffcc")
            self.mic_status_label.config(text="🎙️ Red Mike (Get Ready)", fg="#ff4d4d")
            self.set_light("red")
            self.guide_label.config(text="")
            self.status_label.config(text="⚡ Word Speedrun... Say the 4 words in order!")
            self.root.after(200, self.trigger_listening)
            return

        if self.initial_queue:
            self.current_letter = self.initial_queue.pop(0)
        elif self.review_queue:
            self.current_letter = self.review_queue.pop()
        else:
            self.status_label.config(text="🎉 100% Alphabet Complete! Generating summary...")
            self.set_light("green")
            self.root.after(1500, self.stop_trainer)
            return

        self.summary_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)

        self.letter_label.config(text=self.current_letter, fg="#ffcc00")
        self.mic_status_label.config(text="🎙️ Red Mike (Get Ready)", fg="#ff4d4d")
        self.set_light("red")
        
        expected_word = PHONETIC_ALPHABET[self.current_letter]
        
        if current_mode == 0:
            self.guide_label.config(text=PHONETIC_DISPLAY_FORMAT[self.current_letter])
            self.status_label.config(text=f"Red Light! Listen to pronunciation...")
            threading.Thread(target=self._speak_and_then_listen, args=(expected_word,), daemon=True).start()
        else:
            self.guide_label.config(text="")
            self.status_label.config(text="⚡ Speedrun Active... Speak when Green!")
            self.root.after(150, self.trigger_listening)

    def _speak_text(self, text):
        try:
            cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}');"
            subprocess.run(["powershell", "-Command", cmd], creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
        except Exception as e:
            print(f"TTS Error: {e}")

    def _speak_and_then_listen(self, text):
        self._speak_text(text)
        if self.is_running and not self.is_paused:
            self.root.after(200, lambda: self.trigger_listening())

    def trigger_listening(self):
        if not self.is_running or self.is_paused or self.is_listening:
            return
        self.is_listening = True
        
        self.mic_status_label.config(text="🎙️ Green Mike (Speak Now!)", fg="#28a745")
        self.set_light("green")
        
        current_mode = self.mode_var.get()
        if current_mode == 0:
            self.status_label.config(text="🎙️ Listening... Speak now! (3 seconds)")
        elif current_mode == 2:
            self.status_label.config(text="🎙️ Listening... Speak 4 words! (4.5 seconds)")

        threading.Thread(target=self.listen_process, daemon=True).start()

    def listen_process(self):
        try:
            current_mode = self.mode_var.get()
            if current_mode == 2:
                duration = 4.5
            elif current_mode == 1:
                duration = 1.8
            else:
                duration = 3.0

            audio_data = sd.rec(int(duration * self.samplerate), samplerate=self.samplerate, channels=self.channels, dtype='int16')
            sd.wait()

            if not self.is_running:
                self.queue.put(('state_change', False))
                return

            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.samplerate)
                wf.writeframes(audio_data.tobytes())
            
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio).upper()
                self.queue.put(('success', text))

        except sr.UnknownValueError:
            self.queue.put(('unheard', "Could not understand audio. Try again!"))
        except sr.RequestError as e:
            self.queue.put(('failure', f"Speech service error: {e}"))
        except Exception as e:
            self.queue.put(('failure', f"Audio error: {e}"))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == 'success':
                    self.evaluate_response(data)
                elif msg_type == 'unheard':
                    self.handle_unheard(data)
                elif msg_type == 'failure':
                    self.handle_failure(data)
                elif msg_type == 'state_change':
                    self.is_listening = False
                self.queue.task_done()
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queue)

    def evaluate_response(self, spoken_text):
        if not self.is_running:
            self.is_listening = False
            return
        
        current_mode = self.mode_var.get()

        if current_mode == 2:
            self.total_attempts += 1
            
            # --- FIXED TOKENIZATION FOR X-RAY ---
            norm_spoken = spoken_text.upper().replace("X RAY", "XRAY").replace("X-RAY", "XRAY")
            spoken_tokens = [w.strip() for w in norm_spoken.split() if w.strip()]
            
            is_sequence_match = True
            if len(spoken_tokens) < 4:
                is_sequence_match = False
            else:
                for i, letter in enumerate(self.current_word_sequence):
                    allowed_aliases = PHONETIC_ALIASES.get(letter, [PHONETIC_ALPHABET[letter]])
                    token = spoken_tokens[i] if i < len(spoken_tokens) else ""
                    
                    matched_token = False
                    for alias in allowed_aliases:
                        cleaned_alias = alias.replace("-", "").replace(" ", "")
                        cleaned_token = token.replace("-", "").replace(" ", "")
                        if cleaned_token == cleaned_alias:
                            matched_token = True
                            break
                        matcher = difflib.SequenceMatcher(None, cleaned_token, cleaned_alias)
                        if matcher.ratio() >= 0.75:
                            matched_token = True
                            break
                    if not matched_token:
                        is_sequence_match = False
                        break

            expected_phrase = " ".join([PHONETIC_ALPHABET[l] for l in self.current_word_sequence])

            self.word_round_logs.append({
                'letters': self.current_word_sequence,
                'expected': expected_phrase,
                'spoken': spoken_text,
                'success': is_sequence_match
            })

            if is_sequence_match:
                self.correct_attempts += 1
                for letter in self.current_word_sequence:
                    self.success_counts[letter] += 1
                    self.letter_logs[letter]['success'].append(spoken_text)
                    self.mastered_letters.add(letter)

                self.set_light("green")
                self.mic_status_label.config(text="🎙️ Correct Sequence!", fg="#28a745")
                self.status_label.config(text=f"Correct! You said '{spoken_text}'.")
                
                if self.is_running and not self.is_paused:
                    self.root.after(300, self.next_letter)
            else:
                for letter in self.current_word_sequence:
                    self.miss_counts[letter] += 1
                    self.letter_logs[letter]['miss'].append(spoken_text)

                self.set_light("red")
                self.mic_status_label.config(text="🎙️ Incorrect Sequence!", fg="#ff4d4d")
                self.status_label.config(text=f"Heard: '{spoken_text}' (Expected: {expected_phrase})")
                
                if self.is_running and not self.is_paused:
                    self.root.after(1000, self.next_letter)

            self.update_stats()
            self.is_listening = False
            return

        self.total_attempts += 1
        allowed_aliases = PHONETIC_ALIASES.get(self.current_letter, [PHONETIC_ALPHABET[self.current_letter]])
        cleaned_spoken = spoken_text.replace("-", "").replace(" ", "").strip()
        
        is_match = False
        for alias in allowed_aliases:
            cleaned_alias = alias.replace("-", "").replace(" ", "")
            if cleaned_spoken == cleaned_alias:
                is_match = True
                break
            matcher = difflib.SequenceMatcher(None, cleaned_spoken, cleaned_alias)
            if matcher.ratio() >= 0.75:
                is_match = True
                break

        expected_word = PHONETIC_ALPHABET[self.current_letter]
        phonetic_pron = PHONETIC_PRONUNCIATION[self.current_letter]

        if is_match:
            self.correct_attempts += 1
            self.success_counts[self.current_letter] += 1
            self.letter_logs[self.current_letter]['success'].append(spoken_text)
            self.mastered_letters.add(self.current_letter)
            self.review_queue.discard(self.current_letter)

            self.set_light("green")
            self.mic_status_label.config(text="🎙️ Correct!", fg="#28a745")
            self.status_label.config(text=f"Correct! '{spoken_text}' matches {self.current_letter} - {expected_word}.")
        else:
            self.miss_counts[self.current_letter] += 1
            self.letter_logs[self.current_letter]['miss'].append(spoken_text)
            self.review_queue.add(self.current_letter)

            self.set_light("red")
            self.mic_status_label.config(text="🎙️ Incorrect!", fg="#ff4d4d")
            self.status_label.config(text=f"Heard: '{spoken_text}' | Expected: {expected_word} ({phonetic_pron})")

        self.update_stats()
        self.is_listening = False

        if self.is_running and not self.is_paused:
            delay = 1200 if current_mode == 1 else 1800
            self.root.after(delay, self.next_letter)

    def handle_unheard(self, message):
        if not self.is_running:
            self.is_listening = False
            return
        self.total_attempts += 1
        self.unheard_counts[self.current_letter] += 1
        self.letter_logs[self.current_letter]['unheard'].append("Unheard")
        self.review_queue.add(self.current_letter)

        self.set_light("red")
        self.mic_status_label.config(text="🎙️ Unheard", fg="#ff4d4d")
        expected_word = PHONETIC_ALPHABET[self.current_letter]
        self.status_label.config(text=f"Unheard. Expected: {expected_word}. Try again!")
        
        self.update_stats()
        self.is_listening = False

        if self.is_running and not self.is_paused:
            self.root.after(1500, self.next_letter)

    def handle_failure(self, message):
        if not self.is_running:
            self.is_listening = False
            return
        self.status_label.config(text=message)
        self.is_listening = False

    def update_stats(self):
        accuracy = int((self.correct_attempts / self.total_attempts) * 100) if self.total_attempts > 0 else 0
        current_mode = self.mode_var.get()
        if current_mode != 2:
            mastered_count = len(self.mastered_letters)
            self.progress_tracker_label.config(text=f"Alphabet Mastery: {mastered_count} / 26 letters mastered")
        self.stats_label.config(text=f"Score: {self.correct_attempts}/{self.total_attempts} ({accuracy}%) | Review Queue: {len(self.review_queue)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AviationTrainerApp(root)
    root.mainloop()
