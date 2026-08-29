# picoCTF 2021 — "Transformation" (Reverse Engineering)
### Complete Documentation & Writeup

**Category:** Reverse Engineering
**Difficulty:** Easy
**Source Event:** picoCTF 2021
**Author:** madStacks
**Platform used:** CyLab Security Academy (picoCTF challenge mirror)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Background Concepts](#2-background-concepts)
3. [Challenge Description](#3-challenge-description)
4. [Getting the Encoded File](#4-getting-the-encoded-file)
5. [Writing the Decoder](#5-writing-the-decoder-reversing-the-encoding)
6. [Result](#6-result)
7. [Flag](#7-flag)
8. [Full Source Code](#8-full-source-code)
9. [Summary / Lessons Learned](#9-summary--lessons-learned)
10. [Tools Used](#10-tools-used)
11. [Repository Structure](#11-repository-structure)

---

## 1. Overview

This document is a complete, beginner-friendly walkthrough of how the picoCTF
2021 challenge **"Transformation"** was solved. The goal of this writeup isn't
just to show the final answer — it's to explain **why** every command and
every line of code was used, so that someone with little to no background in
reverse engineering or scripting can still follow the logic from start to
finish.

The challenge itself falls under the **Reverse Engineering** category, which
generally means: "here is something that was transformed or obscured — figure
out how it was transformed, and undo it." Unlike cryptography challenges,
which usually rely on mathematically hard problems, reverse engineering
challenges (especially "Easy" ones like this) tend to rely on **understanding
a process** and simply running it backwards. That is exactly what happens
here: we are given the *exact* code used to scramble the flag, and our entire
task is to write the mirror-image of that code.

The write-up below follows the same order the challenge was actually solved
in: reading the challenge, downloading and inspecting the encoded file,
writing and testing a decoder, and finally confirming the flag. Screenshots
from the actual solving session are included at each stage so the process is
fully visible and reproducible.

---

## 2. Background Concepts

A few underlying computer-science concepts show up throughout this challenge.
Understanding them makes every command below much easier to follow, so they
are explained here up front rather than assumed knowledge.

**ASCII / character codes** — Every character on a keyboard (letters, digits,
symbols) is stored inside a computer as a number, not as the symbol itself.
For example, the letter `A` is stored as the number `65`. This numeric
mapping is called ASCII (for standard English characters) or, more broadly,
Unicode. Python's `ord()` function converts a character into this number, and
`chr()` does the reverse — turning a number back into its character.

**Bits and bytes** — A single ASCII character normally fits inside **8 bits**
(also called **1 byte**), which can represent numbers from 0 to 255. This
challenge's name is a hint: instead of keeping each character as a normal
8-bit byte, the encoding script combines *two* characters into a single
**16-bit** value (2 bytes), which is unusual and is exactly the "trick" we
need to undo.

**Bitwise left shift (`<<`)** — Shifting a number's bits to the left by 8
positions is mathematically the same as multiplying that number by 256 (2 to
the power of 8). This is a common, fast way for code to make room to "stack"
a second value underneath it, which is precisely what happens in this
challenge's encoding formula.

**Endianness (byte order)** — When a value spans more than one byte, there
are two common conventions for which byte comes first when it's stored or
transmitted: **big-endian** (the most significant/largest part of the value
first) and **little-endian** (the least significant/smallest part first).
Different systems and pieces of code default to different conventions, so
when reversing an unknown encoding, it's standard practice to try both and
see which one produces sensible output.

**Encoding vs. Encryption** — It's worth being clear that what this challenge
calls "encoding" is not encryption. There is no secret key involved, and
nothing here is cryptographically secure — it is simply a reversible
transformation of data. That's precisely why it's categorized as *Reverse
Engineering* rather than *Cryptography*, and why the fix is a matter of
understanding and reversing a process rather than breaking an algorithm.

---

## 3. Challenge Description

The challenge page gives us one hint straight away — the small snippet of
Python code that was used to *scramble* (encode) the original flag:

```python
enc = "".join([chr((ord(flag[i]) << 8) + ord(flag[i + 1])) for i in range(0, len(flag), 2)])
```

In plain English, here is what that line is doing to the original flag before
handing it to us as a file called `enc`:

- It walks through the flag **two characters at a time**.
- For each pair of characters, it takes the **numeric code** of the first
  character (`ord()` converts a letter into its number, e.g. `A` → 65).
- It **shifts that number 8 bits to the left** (`<< 8`), which is the same as
  multiplying it by 256. This effectively moves the first character into the
  "upper half" of a bigger number.
- It then **adds the numeric code of the second character** into the
  "lower half" of that same number.
- Finally, `chr()` turns that combined number back into a **single new
  character** — meaning every *pair* of original letters becomes *one* new,
  often unreadable, character in the output.

So two 8-bit characters get squeezed together into one 16-bit character.
That's the "16 bits instead of 8" joke that ends up inside the flag itself
once we solve it.

Our job: reverse this process and pull the original flag back out of the
scrambled `enc` file.

It's worth pointing out how deliberately this challenge is designed: because
the entire encoding formula is handed to us upfront, there's no "black box"
to crack. The real task is purely comprehension — read the formula carefully,
understand what mathematical operation each part performs on the flag's
characters, and then design a script that performs the exact opposite
sequence of operations. This "read the forward process, build the backward
process" approach is one of the most common problem-solving patterns in
reverse engineering as a discipline, and it's why this challenge is a good
introductory example of the category.

![Challenge page showing the encoding script and flag submission box](images/01-challenge-page.png)
*The "Transformation" challenge page, showing the encoding script and the flag submission field.*

---

## 4. Getting the Encoded File

Before any code could be written, the actual encoded file needed to be
located and inspected. This step is just as important as the scripting
itself — you can't reverse-engineer a transformation without first seeing
exactly what its output looks like. Opened a terminal on Kali Linux and
located the downloaded challenge file:

```bash
ls
```
**What this does:** Lists everything in the current folder (home directory) so
we can see what files/folders are available.

```bash
cd Downloads
```
**What this does:** Moves us *into* the `Downloads` folder, since that's where
browser downloads land by default.

```bash
ls
```
**What this does:** Lists the files inside `Downloads`. This is where we
confirm the challenge file `enc` is actually present, alongside unrelated
tools/files already in the folder.

```bash
cat enc
```
**What this does:** Prints the raw contents of the `enc` file straight to the
screen. This is our first look at the "scrambled" flag.

**Result:** A row of unreadable, garbled-looking characters (they render as
Chinese-looking symbols in the terminal). This is expected — because the
encoding script above jammed two ASCII letters together into a single 16-bit
character, the terminal doesn't know how to display these values as normal
English letters, so it falls back to rendering them as CJK (Chinese/Japanese/
Korean) symbols instead. This confirms the file is genuinely encoded and not
just plain text.

This visual observation is actually a useful diagnostic skill on its own:
whenever a text file that's supposed to contain something meaningful instead
renders as unfamiliar foreign-looking script, or as a wall of unprintable
boxes/question marks, it's a strong signal that you're looking at raw
multi-byte data being forced through a text display rather than genuine
human-readable content. Recognizing that pattern quickly is what pointed
directly toward "this file contains packed/combined byte values" rather than
some other form of obfuscation like Base64 or a substitution cipher.

![Terminal showing navigation into Downloads and the garbled output of cat enc](images/02-locating-and-viewing-enc-file.png)
*Locating the `enc` file inside `Downloads` and printing its raw, scrambled contents with `cat`.*

---

## 5. Writing the Decoder (Reversing the Encoding)

Since the encoding script squashed two characters into one, decoding means
doing the **opposite**: take each scrambled character, split it back into its
two original 8-bit halves, and rebuild the string.

Rather than writing and saving a separate `.py` file straight away, the
decoder was first drafted and tested directly inside Python's interactive
shell (the `>>>` prompt). This is a common and efficient workflow for small,
exploratory reverse-engineering scripts — it allows each line to be typed and
its result checked immediately, without needing to re-run an entire saved
script for every small change. Once the logic was confirmed to work
correctly, it was cleaned up and saved as the standalone `decode.py` file
included later in this document.

I dropped into the Python interactive shell and wrote this short script:

```python
from pathlib import Path
s = Path("enc").read_text(encoding="utf-8")
for endian in ("big", "little"):
    raw = b"".join(ord(c).to_bytes(2, endian) for c in s)
    print(endian, repr(raw))
```

### Line-by-line, in plain language:

**`from pathlib import Path`**
Brings in Python's built-in tool for working with files and folders in a
clean, modern way (instead of older-style file-handling code).

**`s = Path("enc").read_text(encoding="utf-8")`**
Opens the `enc` file and reads its entire content into a variable called `s`,
treating the file as UTF-8 text (a standard way computers represent
characters, including the "squashed together" ones from the encoding step).

**`for endian in ("big", "little"):`**
This is the key trick. When the original script combined two characters into
one 16-bit number, there are two possible ways to "unpack" that number back
into bytes — starting from the most significant half first (**big-endian**) or
the least significant half first (**little-endian**). Since we don't know
which order the challenge intended, we simply **try both** and see which one
gives us something readable.

**`raw = b"".join(ord(c).to_bytes(2, endian) for c in s)`**
For every character `c` in the scrambled text:
- `ord(c)` converts the character back into its numeric value.
- `.to_bytes(2, endian)` splits that number back into **2 raw bytes**, in
  either big or little order (depending on which round of the loop we're on).
- `b"".join(...)` glues all those byte-pairs back together into one long
  sequence of raw bytes.

**`print(endian, repr(raw))`**
Prints which ordering we tried (`big` or `little`) next to the resulting raw
byte string, so we can visually compare both attempts and spot the real flag.
Using `repr()` here (instead of just printing the bytes directly) is a
deliberate choice — it displays the byte string in an unambiguous, quoted
form (like `b'...'`), which makes it much easier to spot the exact characters
returned, including telling apart genuinely readable ASCII text from any
stray unprintable bytes that might otherwise be invisible on screen.

**Why loop over both endian options instead of picking one?** Because the
challenge's encoding formula doesn't explicitly say "big-endian" or
"little-endian" anywhere in its code — that detail is implicit in how the
shift and addition were written. Rather than manually tracing through the
math to work out the exact order by hand, looping over both options and
letting the output speak for itself is faster, less error-prone, and scales
well even if the byte order isn't obvious at a glance. This is a practical,
commonly used shortcut in reverse engineering: when a value has a small,
known set of possibilities (here, just two), it's often quicker to try all of
them programmatically than to reason out the one correct answer manually.

---

## 6. Result

Running the script produced two outputs — one for each byte order:

```
big    b'picoCTF{16_bits_inst34d_of_8_b7f62ca5}'
little b'ipocTC{F61b_ti_snits43_dfo8_b_f726ac}5'
```

![Python interactive shell showing the decoder script and both endian outputs, with the flag visible](images/03-decoder-script-and-flag.png)
*Running the decoder in the Python interactive shell — the big-endian result is the clean, readable flag.*

The **big-endian** attempt immediately reads as clean, valid text — this
matches how the original challenge script combined the characters (most
significant byte first). The **little-endian** attempt is just the same bytes
in the wrong order, which is why it comes out scrambled and unreadable.

It's worth taking a moment to notice *why* the little-endian output looks the
way it does: it isn't random garbage, but the correct characters in a
shuffled, byte-swapped order (compare `picoCTF{...}` with `ipocTC{...}` and
you can see letters have simply swapped positions within each pair). This is
a useful sanity check when working with endianness issues in general — a
"wrong-endian" result will often still contain recognizable fragments of the
correct data, just rearranged, whereas a completely different type of error
(like using the wrong encoding entirely) would usually produce output with no
resemblance to the expected result at all.

---

## 7. Flag

Once the big-endian output was confirmed to read as clean, properly formatted
text — matching the standard `picoCTF{...}` flag format used throughout the
competition — it was copied directly from the terminal output and submitted
on the challenge page shown in the earlier screenshot.

```
picoCTF{16_bits_inst34d_of_8_b7f62ca5}
```

Breaking down the flag text itself is a nice confirmation that the challenge
was solved correctly and for the right reasons, not just by luck: it
literally spells out the core lesson of the challenge — that characters were
packed using **16 bits instead of** the usual **8**.

---

## 8. Full Source Code

The decoder script below (`decode.py`) is the standalone, fully commented
version of the solution used above. It's kept as a separate file in this
repository so it can be run directly.

```python
"""
picoCTF 2021 - "Transformation" (Reverse Engineering, Easy)
Decoder script

The original challenge scrambled the flag using this logic:

    enc = "".join(
        [chr((ord(flag[i]) << 8) + ord(flag[i + 1])) for i in range(0, len(flag), 2)]
    )

In plain terms: it grabbed the flag two characters at a time, turned each
character into its numeric code, shifted the first one's code 8 bits to the
left (multiplying it by 256), added the second character's code on top of it,
and converted that combined number back into a single new character.

The result is that every PAIR of original 8-bit characters becomes ONE new
16-bit character in the output file ("enc").

To decode it, we do the reverse: take each scrambled character, split its
number back into two original bytes, and rebuild the string. Since we don't
know upfront whether the original packing was big-endian or little-endian,
this script tries both and prints each result so you can see which one comes
out as clean, readable text.

Usage:
    python3 decode.py
    (expects a file named "enc" in the same directory)
"""

from pathlib import Path

# Read the scrambled/encoded file as UTF-8 text.
# This is the file we downloaded from the challenge, containing the
# "squashed together" 16-bit characters.
s = Path("enc").read_text(encoding="utf-8")

# Try both possible byte orders, since we don't know which one the
# original encoding script effectively used.
for endian in ("big", "little"):
    # For every character in the scrambled text:
    #   1. ord(c)            -> turn the character back into its number
    #   2. .to_bytes(2, ...)  -> split that number into its 2 original bytes,
    #                            in either big-endian or little-endian order
    #   3. b"".join(...)     -> glue all the byte pairs back together
    raw = b"".join(ord(c).to_bytes(2, endian) for c in s)

    # Print which ordering we tried, next to the resulting bytes, so we can
    # visually compare and spot the real, readable flag.
    print(endian, repr(raw))

# Expected output:
#   big    b'picoCTF{16_bits_inst34d_of_8_b7f62ca5}'   <-- this is the flag
#   little b'ipocTC{F61b_ti_snits43_dfo8_b_f726ac}5'   <-- wrong byte order, garbled
```

**Verified working:** this script was tested against a freshly generated `enc`
file (built from the encoding formula above) and correctly reproduced the
flag on the `big` endian pass. This verification step matters for a
writeup that others might reuse or learn from — it confirms the script isn't
just a one-off result copied from a single terminal session, but a genuinely
reproducible solution that will work correctly on any `enc` file generated by
the same encoding formula, not only the specific one from this particular
challenge instance.

---

## 9. Summary / Lessons Learned

- The challenge combined pairs of 8-bit ASCII characters into single 16-bit
  values using bit-shifting (`<<`) and addition — a lightweight, custom
  "encoding," not real encryption.
- Reversing bit-shift-based encodings usually just means undoing the same math
  in the opposite direction — here, splitting 16-bit values back into their
  original two bytes.
- Byte order (endianness) matters when packing/unpacking multi-byte values.
  When it's not specified, trying both **big-endian** and **little-endian** is
  a fast, reliable way to find the correct one without needing to reverse-
  engineer the exact byte order by hand.
- Garbled/CJK-looking text in a terminal is a common visual sign that you're
  looking at raw bytes or multi-byte values being misinterpreted as text —
  worth recognizing as a clue during reverse engineering challenges.
- When an encoding process is fully known (as it was here, since the source
  code was given), the fastest path to a solution is almost always to write
  the mathematically exact inverse of that process, rather than searching for
  external tools or generic "decoders" that may not match the challenge's
  specific, custom logic.
- Testing ambiguous parameters (like byte order) by trying every reasonable
  possibility and letting the output confirm which one is correct is a
  practical and time-efficient technique, especially for challenges rated
  "Easy," where the goal is usually to test understanding of a concept rather
  than to demand painstakingly precise manual analysis.
- Keeping a short, well-commented script (like `decode.py` in this repo)
  rather than only a one-off interactive session makes the solution easy to
  re-run, re-use on similar future challenges, and easy for someone else
  reading this writeup to learn from directly.

---

## 10. Tools Used

- **Kali Linux** — the operating system and terminal environment used
  throughout the challenge, chosen for its built-in security and scripting
  tooling.
- **Python 3 interactive shell** — used to write, test, and iterate on the
  decoding logic quickly, using the built-in `pathlib` module for simple,
  reliable file reading.
- **CyLab Security Academy** — the platform used to browse and access this
  picoCTF 2021 challenge, including its description, hints, and flag
  submission form.

---

## 11. Repository Structure

```
.
├── picoCTF-Transformation-Complete-Documentation.md   # This document
├── decode.py                                          # Standalone, commented decoder script
└── images/
    ├── 01-challenge-page.png
    ├── 02-locating-and-viewing-enc-file.png
    └── 03-decoder-script-and-flag.png
```

Run the decoder yourself with:

```bash
python3 decode.py
```
