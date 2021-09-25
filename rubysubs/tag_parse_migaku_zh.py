from . import tags

from enum import Enum
from itertools import zip_longest


def pinyin_number_to_tone(syllable):
    replacements = {
        'a': ['ā', 'á', 'ǎ', 'à'],
        'e': ['ē', 'é', 'ě', 'è'],
        'u': ['ū', 'ú', 'ǔ', 'ù'],
        'i': ['ī', 'í', 'ǐ', 'ì'],
        'o': ['ō', 'ó', 'ǒ', 'ò'],
        'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
    }

    medials = ['i', 'u', 'ü']

    if len(syllable) < 1:
        return syllable
    
    try:
        tone_idx = int(syllable[-1])
    except ValueError:
        return syllable

    if not (1 <= tone_idx <= 5):
        return syllable

    ret = syllable.replace('v', 'ü')

    if tone_idx == 5:
        return ret[:-1]

    for i in range(len(ret)):
        c1 = ret[i]
        c2 = ret[i+1]   # safe because of tone idx

        if c1 in medials and c2 in replacements:
            return ret[:i+1] + replacements[c2][tone_idx-1] + ret[i+2:-1]
        if c1 in replacements:
            return ret[:i] + replacements[c1][tone_idx-1] + ret[i+1:-1]
    
    return syllable


def zhuyin_number_to_tone(syllable):
    tones = [ '', 'ˊ', 'ˇ', 'ˋ', '˙' ]

    if len(syllable) < 1:
        return syllable

    try:
        tone_idx = int(syllable[-1])
    except ValueError:
        return syllable

    if not (1 <= tone_idx <= 5):
        return syllable

    return syllable[:-1] + tones[tone_idx-1]



hanzi_ranges = [
    (    0x4e00,     0x9fff),
    (    0x3400,     0x4DBF),
    (0x00020000, 0x0002A6DF),
    (0x0002B740, 0x0002B81F),
    (0x0002B820, 0x0002CEAF),
    (0x0002CEB0, 0x0002EBEF),
    (    0xF900,     0xFAFF),
    (0x0002F800, 0x0002FA1F),
]

def is_hanzi(text):
    for c in text:
        return any([s <= ord(c) <= e for (s,e) in hanzi_ranges])



color_table_mandarin = [
    'E60000',
    'E68A00',
    '00802B',
    '005CE6',
    '808080',
]

color_table_cantonese = [
    'E60000',
    'E68A00',
    '00802B',
    '005CE6',
    'AC00E6',
    '808080',
]


class DecoMode(Enum):
    NONE = 0,
    PINYIN = 1,
    ZHUYIN = 2,
    JYUTPING = 3,


class Mode:

    def __init__(self, is_cantonese, mode_txt=''):
        txt = mode_txt.lower()

        self.deco_mode = DecoMode.NONE
        self.is_cantonese = is_cantonese

        if is_cantonese:
            self.only_unknown = txt.startswith('unknown')
            if self.only_unknown or txt == 'jyutping' or txt == '':
                self.deco_mode = DecoMode.JYUTPING
        else:
            self.only_unknown = txt.startswith('unknown')
            if self.only_unknown:
                txt = txt[len('unknown'):]
            if txt == 'pinyin' or txt == '':
                self.deco_mode = DecoMode.PINYIN
            elif txt == 'zhuyin':
                self.deco_mode = DecoMode.ZHUYIN


    def color_tags_for_syllable(self, syllable, tone_highlighting):
        if not tone_highlighting or len(syllable) < 1:
            return '', ''

        try:
            idx = int(syllable[-1]) - 1
        except ValueError:
            return '', ''

        color_table = color_table_cantonese if self.is_cantonese else color_table_mandarin
        idx = min(idx, len(color_table)-1)
        color = color_table[idx]

        co = '{\\c&H' + color[4:6] + color[2:4] + color[0:2] + '&}'
        cc = '{\\c}'

        return co, cc


    def markup_word(self, text, syllables, tone_highlighting, is_unknown):
        if len(text) != len(syllables):
            return (text, '?')

        ret_text = ''
        ret_deco = ''

        for h, s in zip(text, syllables):
            co, cc = self.color_tags_for_syllable(s, tone_highlighting)
            ret_text += co + h + cc
            if self.deco_mode != DecoMode.NONE and ((not self.only_unknown) or is_unknown):
                if self.deco_mode == DecoMode.PINYIN:
                    s = pinyin_number_to_tone(s)
                elif self.deco_mode == DecoMode.ZHUYIN:
                    s = zhuyin_number_to_tone(s)
                ret_deco += co + s + cc

        return (ret_text, ret_deco)


def frequency_color(freq):
    if freq == 0:
        return (255, 211,   0, 0.5)
    if (freq < 1500):
        return ( 44, 173, 246, 0.5)
    if (freq < 5000):
        return ( 65, 208, 182, 0.5)
    if (freq < 15000):
        return (253, 255,  22, 0.5)
    if (freq < 30000):
        return (226, 116,  32, 0.5)
    if (freq < 60000):
        return (249,  28,  28, 0.5)
    return (203, 203, 203, 0.5)


def parse(text, mode, tone_highlighting, unknown_underlining, one_t_marking, one_t_frequency_marking):

    lines_tags = []

    for line_text in text.split('\n'):
        line_tags = []

        last = 0

        while True:
            bracket_open = line_text.find('[', last)
            if bracket_open < 0:
                break
            bracket_close = line_text.find(']', bracket_open+1)
            if bracket_close < 0:
                break

            # Walk back and find hanzi range to decorate
            hanzi_start = bracket_open
            while True:
                if hanzi_start <= last:
                    break
                if is_hanzi(line_text[hanzi_start-1]):
                    hanzi_start -= 1
                else:
                    break
            hanzi_end = bracket_open

            if last < hanzi_start:
                line_tags.append(tags.TagText(line_text[last:hanzi_start]))

            if hanzi_start < hanzi_end:
                hanzi_text = line_text[hanzi_start:hanzi_end]
                bracket_text = line_text[bracket_open+1:bracket_close]
                bracket_parts = bracket_text.split(';')

                syllables = []
                if len(bracket_parts) >= 1:
                    syllables = bracket_parts[0].split()

                learning_status = 2
                if len(bracket_parts) >= 2:
                    learning_status = int(bracket_parts[1])
                
                is_one_t = False
                one_t_frequency = 0
                if len(bracket_parts) >= 3:
                    one_t_info_parts = bracket_parts[2].split(',')
                    is_one_t = one_t_info_parts[0] == '1'
                    if len(one_t_info_parts) >= 2 and one_t_frequency_marking:
                        one_t_frequency = int(one_t_info_parts[1])

                # Unknown/1T opening tags
                if one_t_marking and is_one_t:
                    color = frequency_color(one_t_frequency)
                    line_tags.append( tags.TagHighlightStart(*color) )

                if unknown_underlining and learning_status < 2:
                    if learning_status == 1:
                        line_tags.append( tags.TagUnderlineStart(241, 187, 78) )
                    else:
                        line_tags.append( tags.TagUnderlineStart(241, 78, 78) )

                # Hanzi/Deco
                tag_hanzi, tag_deco = mode.markup_word(hanzi_text, syllables, tone_highlighting, learning_status==0)
                line_tags.append(tags.TagText(tag_hanzi, tag_deco))                                

                # Unknown/1T closing tags
                if unknown_underlining and learning_status < 2:
                    line_tags.append( tags.TagUnderlineEnd )

                if one_t_marking and is_one_t:
                    line_tags.append( tags.TagHighlightEnd )

            last = bracket_close+1

        if last < len(line_text):
            line_tags.append(tags.TagText(line_text[last:]))

        lines_tags.append(line_tags)

    return lines_tags



def args_from_strings(in_args, is_cantonese):
    out_args = [Mode(is_cantonese), True, True, True, True]

    if len(in_args) >= 1:
        out_args[0] = Mode(is_cantonese, in_args[0])

    if len(in_args) >= 2:
        out_args[1] = in_args[1].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 3:
        out_args[2] = in_args[2].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 4:
        out_args[3] = in_args[3].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 5:
        out_args[4] = in_args[4].lower() not in ['no', 'n', 'false', 'f', '0']

    return out_args


def parser_from_string_args(in_args):
    args = args_from_strings(in_args, False)
    return (lambda text: parse(text, *args))

def parser_from_string_args_HK(in_args):
    args = args_from_strings(in_args, True)
    return (lambda text: parse(text, *args))
