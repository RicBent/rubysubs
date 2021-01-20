# Migaku rubysubs

Tool/library to add ruby text to Advanced SubStation Alpha (.ass) subtitles using the same syntax as in Anki or the Migaku Anki plugins.

![](https://i.imgur.com/7B4drNw.jpg)

rubysubs is licensed under LGPLv3. See LICENSE for further detail.

## Installation

Run the following to install:

```
pip install rubysubs
```
For binary releases refer to the [releases page](https://github.com/RicBent/rubysubs/releases/).

## Usage as tool

```
rubysubs <source subtitle> <output subtitle> [<tag parser> [arg0] [arg1] ...]
```

- Source subtilte: Path to source subtitle file
- Output subtilte: Path to output subtitle file
- Tag parser (optional):
  - ruby (default): Ruby square bracket tags, no arguments
  - ja: Migaku Japanese tag parser
    - arg0: mode (furigana/kanji/kana, default: furigana)
    - arg1: pitch highlighting (yes/no, default: yes)
    - arg2: pitch shapes (yes/no, default: no)
    - arg3: unknown word underlining (yes/no, default: yes)
    - arg4: 1T word highlighting (yes/no, default: yes)

Examples:

```
rubysubs source.ass out.ass
rubysubs source_ja.ass out_ja_furigana_no_markings.ass ja furigana no no no no
rubysubs source_ja.ass out_ja_kana_all_markings.ass ja kana yes yes yes yes
```

Notes:
- Style info is pulled from the style called ``Default``
  - ``ScaleX`` and ``ScaleY`` are reset to 100
  - ``Spacing`` and ``Angle`` are reset to 0
  - ``Italic``, ``Underline`` and ``Strikeout`` are reset. ``Bold`` is supported
  - ``Alignment`` is currently fixed to bottom-center with ``MarginV`` being considered
- ``PlayResX`` and ``PlayResY`` script info tags should be set to allow screen postion calculations. Defaults to 1920x1080
- No ASS tags are supported

## Usage as library

```python
import sys
import rubysubs
from PyQt5.QtGui import QGuiApplication

# Required for QFontMetrics
qapp = QGuiApplication(sys.argv)

rubysubs.convert_sub_file('source.ass', 'out.ass', rubysubs.tag_parse_ruby.parse)
rubysubs.convert_sub_file('source_jp.ass', 'out_ja.ass', rubysubs.tag_parse_migaku_ja.parse)
```

## Used libraries
- [cChardet](https://github.com/PyYoshi/cChardet) for subtitle file encoding detection
- [pysubs2](https://github.com/tkarabela/pysubs2) for subtitle file reading/writing
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for text measurements
