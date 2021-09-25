from . import tags
from . import ja_util

from enum import Enum


# Entries: (main_text, ruby_text, following_text, accent_list, dictionary_form, learning_status, is_one_t, one_t_frequency)

def parse_migaku(text):
    lines = []

    for l in text.split('\n'):
        parts = []

        last = 0
        
        while True:
            i = l.find('[', last)
            if i < 0:
                break
            j = l.find(']', i+1)
            if j < 0:
                break
            
            k = l.rfind(' ', last, i)

            if last < k:
                parts.append( (l[last:k], '', '', [], None, 2, False, 0) )

            k = max(last, k+1)

            m = l.find(' ', j+1)
            if m < 0:
                m = len(l)

            bracket_parts = l[i+1:j].split(';')
            
            # TODO: Workaround.
            if len(bracket_parts) == 3:
                bracket_parts.insert(1, '')

            ruby_text = ''
            accent_list = []
            dictionary_form = None
            learning_status = 2     # Learned
            is_one_t = False
            one_t_frequency = 0

            bracket_parts_1 = bracket_parts[0].replace('、', ',').split(',')    # Replace to support both browser and anki syntax
            ruby_text = bracket_parts_1[0]
            if len(bracket_parts_1) >= 2:
                dictionary_form = bracket_parts_1[1]
            if len(bracket_parts) >= 2:
                accent_list = bracket_parts[1].replace('、', ',').split(',')    # Replace to support both browser and anki syntax
            if len(bracket_parts) >= 3:
                learning_status = int(bracket_parts[2])
            if len(bracket_parts) >= 4:
                one_t_info_parts = bracket_parts[3].split(',')
                is_one_t = one_t_info_parts[0] == '1'
                if len(one_t_info_parts) >= 2:
                    one_t_frequency = int(one_t_info_parts[1])

            parts.append( (l[k:i], ruby_text, l[j+1:m], accent_list, dictionary_form, learning_status, is_one_t, one_t_frequency) )

            last = m+1

        if last < len(l):
            parts.append( (l[last:len(l)], '', '', [], None, 2, False, 0) )

        lines.append(parts)

    return lines


class Mode(Enum):
    KANJI = 0,
    KANJI_READING = 1,
    READING = 2,
    KANJI_READING_UNKNOWN = 3,

    @classmethod
    def from_string(cls, key):
        associations = {
            'kanji':            cls.KANJI,
            'kanjireading':     cls.KANJI_READING,
            'reading':          cls.READING,
            'unknown':          cls.KANJI_READING_UNKNOWN,
            'furigana':         cls.KANJI_READING,
            'kana':             cls.READING,
            'furigana_unknown': cls.KANJI_READING_UNKNOWN,
        }
        return associations.get(key.lower(), cls.KANJI_READING)


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


def migaku_to_ruby(parsed_lines, mode=Mode.KANJI_READING, pitch_highlighting=True, pitch_shapes=False, unknown_underlining=True, one_t_highlighting=True, one_t_frequency_marking=True):

    coloring = {
        'h': '005CE6',  # Heiban
        'a': 'E60000',  # Atamadaka
        'n': 'E68A00',  # Nakadaka
        'o': '00802B',  # Odaka
        'k': 'AC00E6',  # Kifuku
    }

    def deco_for_accent_list(accent_list):
        if pitch_highlighting and len(accent_list) and len(accent_list[0]):
            color = coloring.get(accent_list[0][0])
            if color:
                co = '{\\c&H' + color[4:6] + color[2:4] + color[0:2] + '&}'
                cc = '{\\c}'
                return co, cc
        return '', ''

    def pitch_shapes_text(accent_list):
        ret = ''
        for a in accent_list[1:]:
            color = coloring.get(a[0])
            if color:
                ret += '{\\c&H' + color[4:6] + color[2:4] + color[0:2] + '&}⬩{\\c}'
        return ret

    # List if tag lists for each line
    ret = []

    for l in parsed_lines:
        
        # Line tags
        retl = []

        for (main_text, ruby_text, following_text, accent_list, dictionary_form, learning_status, is_one_t, one_t_frequency) in l:
            co, cc = deco_for_accent_list(accent_list)

            # Unknown/1T opening tags
            if one_t_highlighting and is_one_t:
                if not one_t_frequency_marking:
                    one_t_frequency = 0
                color = frequency_color(one_t_frequency)
                retl.append( tags.TagHighlightStart(*color) )

            if unknown_underlining and learning_status < 2:
                if learning_status == 1:
                    retl.append( tags.TagUnderlineStart(241, 187, 78) )
                else:
                    retl.append( tags.TagUnderlineStart(241, 78, 78) )

            # Tags for content
            # TODO: Remove spaces from Kanji/Furigana modes
            if mode == Mode.READING:
                # Use ruby text instead of normal text if available
                txt = co + (ruby_text if ruby_text else main_text) + following_text + cc
                retl.append( tags.TagText(txt, '') )

            elif mode == Mode.KANJI:
                # Discard ruby text
                txt = co + main_text + following_text + cc
                retl.append( tags.TagText(txt, '') )

            else:   # Mode.KANJI_READING and Mode.KANJI_READING_UNKNOWN
                if ruby_text and (mode != mode.KANJI_READING_UNKNOWN or learning_status == 0):
                    groups = ja_util.distribute_furigana(main_text, ruby_text)
                    for expression, reading in groups:
                        tag_text = co + expression + cc
                        tag_ruby_text = ''
                        if reading:
                            tag_ruby_text = co + reading + cc
                        retl.append( tags.TagText(tag_text, tag_ruby_text) )
                else:
                    tag_text = co + main_text + cc
                    retl.append( tags.TagText(tag_text, '') )

                if following_text:
                    retl.append( tags.TagText(co + following_text + cc, '') )

            # Pitch shapes
            if pitch_shapes:
                retl.append( tags.TagText(pitch_shapes_text(accent_list), '') )

            # Unknown/1T closing tags
            if unknown_underlining and learning_status < 2:
                retl.append( tags.TagUnderlineEnd )

            if one_t_highlighting and is_one_t:
                retl.append( tags.TagHighlightEnd )

            # TODO: Emit spaces if in kana mode

        # Post processing to reduce number of elements
        retl_pp = []

        for tag in retl:
            # If the last and current tags are text and have no ruby, combine them
            if len(retl_pp) and tag.isof(tags.TagText) and not tag.ruby_text:
                last_tag = retl_pp[-1]
                if last_tag.isof(tags.TagText) and not last_tag.ruby_text:
                    last_tag.text = last_tag.text + tag.text
                    continue
            retl_pp.append(tag)

        ret.append(retl_pp)

    return ret


def parse(text, mode=Mode.KANJI_READING, pitch_highlighting=True, pitch_shapes=False, unknown_underlining=True, one_t_marking=True, one_t_frequency_marking=True):
    migaku_parsed = parse_migaku(text)
    return migaku_to_ruby(migaku_parsed, mode, pitch_highlighting, pitch_shapes, unknown_underlining, one_t_marking, one_t_frequency_marking)


def args_from_strings(in_args):
    out_args = [Mode.KANJI_READING, True, False, True, True, True]

    if len(in_args) >= 1:
        out_args[0] = Mode.from_string(in_args[0])

    if len(in_args) >= 2:
        out_args[1] = in_args[1].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 3:
        out_args[2] = in_args[2].lower() in ['yes', 'y', 'true', 't', '1']

    if len(in_args) >= 4:
        out_args[3] = in_args[3].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 5:
        out_args[4] = in_args[4].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 6:
        out_args[5] = in_args[5].lower() not in ['no', 'n', 'false', 'f', '0']

    return out_args


def parser_from_string_args(in_args):
    args = args_from_strings(in_args)
    return (lambda text: parse(text, *args))
