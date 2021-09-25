from . import tags

def is_word_char(c):
    return c not in ' ·"“”“”\'『』「」。.、,~-_()[]{}|\\/!?'

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


def parse(text, unknown_underlining=True, one_t_marking=True, one_t_frequency_marking=True):
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

            word_start = bracket_open
            while True:
                if word_start <= last:
                    break
                if is_word_char(line_text[word_start-1]):
                    word_start -= 1
                else:
                    break
            
            if last < word_start:
                line_tags.append(tags.TagText(line_text[last:word_start]))

            word = line_text[word_start:bracket_open]
            bracket_text = line_text[bracket_open+1:bracket_close]
            bracket_parts = bracket_text.split(';')


            if len(bracket_parts) != 2:
                line_tags.append( tags.TagText(word, '?') )
            else:
                learning_status = int(bracket_parts[0])

                is_one_t = False
                one_t_frequency = 0

                one_t_info_parts = bracket_parts[1].split(',')
                is_one_t = one_t_info_parts[0] == '1'
                if len(one_t_info_parts) >= 2 and one_t_frequency_marking:
                    one_t_frequency = int(one_t_info_parts[1])

                if one_t_marking and is_one_t:
                    color = frequency_color(one_t_frequency)
                    line_tags.append( tags.TagHighlightStart(*color) )

                if unknown_underlining and learning_status < 2:
                    if learning_status == 1:
                        line_tags.append( tags.TagUnderlineStart(241, 187, 78) )
                    else:
                        line_tags.append( tags.TagUnderlineStart(241, 78, 78) )

                line_tags.append( tags.TagText(word) )

                if unknown_underlining and learning_status < 2:
                    line_tags.append( tags.TagUnderlineEnd )

                if one_t_marking and is_one_t:
                    line_tags.append( tags.TagHighlightEnd )


            last = bracket_close+1

        if last < len(line_text):
            line_tags.append( tags.TagText(line_text[last:], '') )

        lines_tags.append(line_tags)
    
    return lines_tags



def args_from_strings(in_args):
    out_args = [True, True, True]

    if len(in_args) >= 1:
        out_args[0] = in_args[0].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 2:
        out_args[1] = in_args[1].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 3:
        out_args[2] = in_args[2].lower() not in ['no', 'n', 'false', 'f', '0']

    return out_args


def parser_from_string_args(in_args):
    args = args_from_strings(in_args)
    return (lambda text: parse(text, *args))