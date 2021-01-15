from . import tags


def parse(text):
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
                parts.append( tags.TagText(l[last:k], '') )

            k = max(last, k+1)

            parts.append( tags.TagText(l[k:i], l[i+1:j]) )

            last = j+1

        if last < len(l):
            parts.append( tags.TagText(l[last:len(l)], '') )

        lines.append(parts)

    return lines


def parser_from_string_args(in_args):
    return parse
