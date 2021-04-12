hiragana = 'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬ' \
           'ねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ'
katakana = 'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌ' \
           'ネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ'
kana = hiragana + katakana

trans_hiragana2katakana = str.maketrans(hiragana, katakana)
trans_katakana2hiragana = str.maketrans(katakana, hiragana)


def hiragana2katakana(text):
    return text.translate(trans_hiragana2katakana)

def katakana2hiragana(text):
    return text.translate(trans_katakana2hiragana)


def is_hiragana(text):
    return all(c in hiragana for c in text)

def is_katakana(text):
    return all(c in katakana for c in text)

def is_kana(text):
    return all(c in kana for c in text)


def _distribute_furigana_groups(reading, reading_h, groups):
    if len(groups) < 1:
        return []

    is_kana, text, text_h = groups[0]
    text_len = len(text)

    if is_kana:
        if reading_h.startswith(text_h):
            segs = _distribute_furigana_groups(reading[text_len:], reading_h[text_len:], groups[1:])

            if segs is not None:
                furigana = '' if reading.startswith(text) else reading[:text_len]
                segs.insert(0, (text, furigana))
                return segs

        return None

    else:
        result = None

        for i in range(len(reading), text_len-1, -1):
            segs = _distribute_furigana_groups(reading[i:], reading_h[i:], groups[1:])

            if segs is not None:
                if result is not None:
                    return None     # Ambiguous

                furigana = reading[:i]
                segs.insert(0, (text, furigana))
                result = segs

            if len(groups) == 1:
                break

        return result


def distribute_furigana(expression, reading):

    if not reading or reading == expression:
        return [(expression, '')]

    groups = []
    ik_last = None

    for c in expression:
        ik = is_kana(c)
        if ik == ik_last:
            groups[-1][1] += c
        else:
            groups.append([ik, c])
            ik_last = ik

    for g in groups:
        g.append(katakana2hiragana(g[1]))

    reading_h = katakana2hiragana(reading)

    segs = _distribute_furigana_groups(reading, reading_h, groups)

    if segs:
        return segs

    return [(expression, reading)]


def distribute_furigana_html(expression, reading):
    r = []
    for txt, ruby in distribute_furigana(expression, reading):
        if not ruby:
            r.append(txt)
        else:
            r.extend['<ruby>', txt, '<rt>', ruby, '</rt></ruby>']
    return ''.join(r)
