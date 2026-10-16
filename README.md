# ✈️ Aviation Phonetic Alphabet Trainer

An interactive desktop application built with Python and Tkinter designed for student pilots, aviation enthusiasts, air traffic controllers, and radio operators to master the official ICAO aviation phonetic alphabet (**Alfa, Bravo, Charlie...**) using real-time speech recognition.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)

---

## ✨ Features

* **🔊 Learning Mode:** Listen to native text-to-speech audio pronunciation of the phonetic word, followed by a live microphone prompt to speak your response.
* **⚡ Speedrun Mode:** Fast-paced, instant-next prompts to test your quick-fire reflex recall.
* **🔤 Word Speedrun Mode:** Practice spelling and speaking 4-letter aviation words or custom space-separated phrases across 15 dynamic rounds with robust multi-word sequence validation.
* **🎙️ Real-time Speech Recognition:** Powered by `sounddevice` and Google Speech Recognition with custom fuzzy string matching (`difflib`) and alias handling to accommodate common speech-to-text quirks (e.g., handling variants like *Alpha/Alfa* or hyphenated terms like *X-RAY*).
* **📊 Detailed Session Summaries:** View comprehensive performance breakdowns upon completion, including overall accuracy, successful responses, unheard audio attempts, and troublesome letters/words that require extra practice.
* **📖 Built-in Reference Chart:** Quick-access modal displaying the official ICAO reference table with spellings and phonetic pronunciations.

---

## 🛠️ Prerequisites & Requirements

* **Python 3.8 or higher**
* A working microphone
* **Operating System:** Designed with Windows PowerShell Text-to-Speech integration (`System.Speech`) for audio pronunciation prompts.

### Python Dependencies
Install the required Python packages using `pip`:
```bash
pip install sounddevice SpeechRecognition numpy

```markdown
# ✈️ Aviation Phonetic Alphabet Trainer

An interactive desktop application built with Python and Tkinter designed for student pilots, aviation enthusiasts, air traffic controllers, and radio operators to master the official ICAO aviation phonetic alphabet (**Alfa, Bravo, Charlie...**) using real-time speech recognition.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)

---

## ✨ Features

* **🔊 Learning Mode:** Listen to native text-to-speech audio pronunciation of the phonetic word, followed by a live microphone prompt to speak your response.
* **⚡ Speedrun Mode:** Fast-paced, instant-next prompts to test your quick-fire reflex recall.
* **🔤 Word Speedrun Mode:** Practice spelling and speaking 4-letter aviation words or custom space-separated phrases across 15 dynamic rounds with robust multi-word sequence validation.
* **🎙️ Real-time Speech Recognition:** Powered by `sounddevice` and Google Speech Recognition with custom fuzzy string matching (`difflib`) and alias handling to accommodate common speech-to-text quirks (e.g., handling variants like *Alpha/Alfa* or hyphenated terms like *X-RAY*).
* **📊 Detailed Session Summaries:** View comprehensive performance breakdowns upon completion, including overall accuracy, successful responses, unheard audio attempts, and troublesome letters/words that require extra practice.
* **📖 Built-in Reference Chart:** Quick-access modal displaying the official ICAO reference table with spellings and phonetic pronunciations.

---

## 🛠️ Prerequisites & Requirements

* **Python 3.8 or higher**
* A working microphone
* **Operating System:** Designed with Windows PowerShell Text-to-Speech integration (`System.Speech`) for audio pronunciation prompts.

### Python Dependencies
Install the required Python packages using `pip`:
```bash
pip install sounddevice SpeechRecognition numpy

```

---

## 🚀 Installation & Running

1. **Clone the repository:**
```bash
git clone [https://github.com/paredamerik/aviation-phonetic-trainer.git](https://github.com/paredamerik/aviation-phonetic-trainer.git)
cd aviation-phonetic-trainer

```


2. **Run the application:**
```python
python alpha_trainer.py

```



---

## 🕹️ How to Use

1. Launch the app and select your desired **Training Mode** using the radio buttons:
* **Learning Mode:** Best for beginners wanting audio guidance.
* **Speedrun Mode:** Best for testing quick recall.
* **Word Speedrun:** Best for spelling and pronouncing callsigns or custom aviation words (you can input custom space-separated words in the text box provided).


2. Click **▶ Start** and wait for the countdown.
3. Watch the traffic light indicator change to **Green** and speak the correct ICAO phonetic word(s) clearly into your microphone.
4. Click **⏹ Stop & Summary** at any time to view your progress report.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to check out the [issues page](https://github.com/paredamerik/aviation-phonetic-trainer/issues).

---

## 📄 License

This project is open-source software licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](https://www.gnu.org/licenses) file for details.

```

```
