from . import tags

gender_colors = {
    'm': '005CE6',
    'f': 'E60000',
    'n': '808080',
}

def is_word_char(c):
    return c.isalnum()


def parse(text, gender_highlighting=True, unknown_underlining=True, one_t_marking=True):
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


            if len(bracket_parts) != 3:
                line_tags.append( tags.TagText(word, '?') )
            else:
                gender = bracket_parts[0]
                learning_status = int(bracket_parts[1])
                is_one_t = bracket_parts[2] == '1'

                if gender_highlighting:
                    color = gender_colors.get(gender)
                    if color:
                        co = '{\\c&H' + color[4:6] + color[2:4] + color[0:2] + '&}'
                        cc = '{\\c}'
                        word = co + word + cc

                if one_t_marking and is_one_t:
                    line_tags.append( tags.TagHighlightStart(255, 211, 20, 102) )

                if unknown_underlining and learning_status < 2:
                    if learning_status == 1:
                        line_tags.append( tags.TagUnderlineStart(241, 187, 78) )
                    else:
                        line_tags.append( tags.TagUnderlineStart(241, 78, 78) )

                line_tags.append( tags.TagText(word) )

                if unknown_underlining and learning_status < 2:
                    line_tags.append( tags.TagUnderlineEnd )


            last = bracket_close+1

        if last < len(line_text):
            line_tags.append( tags.TagText(line_text[last:], '') )

        lines_tags.append(line_tags)
    
    return lines_tags



def args_from_strings(in_args, is_cantonese):
    out_args = [True, True, True]

    if len(in_args) >= 1:
        out_args[0] = in_args[0].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 2:
        out_args[1] = in_args[1].lower() not in ['no', 'n', 'false', 'f', '0']

    if len(in_args) >= 3:
        out_args[2] = in_args[2].lower() not in ['no', 'n', 'false', 'f', '0']

    return out_args


def parser_from_string_args(in_args):
    args = args_from_strings(in_args, False)
    return (lambda text: parse(text, *args))