from . import tags

from enum import Enum


# Entries: (main_text, ruby_text, following_text, accent_list, dictionary_form, learning_status, is_one_t)

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
                parts.append( (l[last:k], '', '', [], None, 2, False) )

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

            bracket_parts_1 = bracket_parts[0].replace('、', ',').split(',')    # Replace to support both browser and anki syntax
            ruby_text = bracket_parts_1[0]
            if len(bracket_parts_1) >= 2:
                dictionary_form = bracket_parts_1[1]
            if len(bracket_parts) >= 2:
                accent_list = bracket_parts[1].replace('、', ',').split(',')    # Replace to support both browser and anki syntax
            if len(bracket_parts) >= 3:
                learning_status = int(bracket_parts[2])
            if len(bracket_parts) >= 4:
                is_one_t = bracket_parts[3] == '1'

            parts.append( (l[k:i], ruby_text, l[j+1:m], accent_list, dictionary_form, learning_status, is_one_t) )

            last = m+1

        if last < len(l):
            parts.append( (l[last:len(l)], '', '', [], None, 2, False) )

        lines.append(parts)

    return lines


class Mode(Enum):
    KANJI = 0,
    KANJI_READING = 1,
    READING = 2,

    @classmethod
    def from_string(cls, key):
        associations = {
            'kanji':        cls.KANJI,
            'kanjireading': cls.KANJI_READING,
            'reading':      cls.READING,
            'furigana':     cls.KANJI_READING,
            'kana':         cls.READING,
        }
        return associations.get(key.lower(), cls.KANJI_READING)


def migaku_to_ruby(parsed_lines, mode=Mode.KANJI_READING, pitch_highlighting=True, pitch_shapes=False, unknown_underlining=True, one_t_highlighting=True):

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

        for (main_text, ruby_text, following_text, accent_list, dictionary_form, learning_status, is_one_t) in l:
            co, cc = deco_for_accent_list(accent_list)

            # Unknown/1T opening tags
            if one_t_highlighting and is_one_t:
                retl.append( tags.TagHighlightStart(255, 211, 20, 102) )

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

            else:   # Mode.KANJI_READING
                tag_text = co + main_text + cc
                tag_ruby_text = ''
                if ruby_text:
                    tag_ruby_text = co + ruby_text + cc
                retl.append( tags.TagText(tag_text, tag_ruby_text) )

                if following_text:
                    retl.append( tags.TagText(co + following_text + cc, '') )

            # Pitch shapes
            if pitch_shapes:
                retl.append( tags.TagText(pitch_shapes_text(accent_list), '') )

            # Unknown/1T closing tags
            if unknown_underlining and learning_status < 2:
                retl.append( tags.TagUnderlineEnd )

            if is_one_t:
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


def parse(text, mode=Mode.KANJI_READING, pitch_highlighting=True, pitch_shapes=False, unknown_underlining=True, one_t_marking=True):
    migaku_parsed = parse_migaku(text)
    return migaku_to_ruby(migaku_parsed, mode, pitch_highlighting, pitch_shapes, unknown_underlining, one_t_marking)


def args_from_strings(in_args):
    out_args = [Mode.KANJI_READING, True, False, True, True]

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

    return out_args


def parser_from_string_args(in_args):
    args = args_from_strings(in_args)
    return (lambda text: parse(text, *args))
