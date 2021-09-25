from . import tags
from . import tag_parse_ruby

import math
import codecs
import cchardet as chardet
import pysubs2
from PyQt5.QtGui import QFont, QFontMetrics


# Removes all curly brace tags
def strip_ass_tags(text):
    ret = ''
    in_curly = False
    for c in text:
        if c == '{':
            in_curly = True
        elif c == '}':
            in_curly = False
        elif not in_curly:
            ret += c
    return ret


class RubySubParser():

    def __init__(self, frame_width, frame_height, bottom_margin, font_name, font_size, ruby_font_size, bold, tag_parser=tag_parse_ruby.parse):

        self.tag_parser = tag_parser

        # ASS font size is actually the line height, not the cap height like regularly
        probe_size = 1000
        probe_font = QFont(font_name, probe_size)
        probe_font.setBold(bold)
        probe_font_metrics = QFontMetrics(probe_font)
        ass_font_factor = probe_size / probe_font_metrics.height()

        self.normal_line_height = round(font_size)
        self.font_size = math.ceil(font_size * ass_font_factor)
        
        if ruby_font_size is None:
            self.ruby_font_size = round(font_size / 2)
        else:
            self.ruby_font_size = round(ruby_font_size * ass_font_factor)

        font = QFont(font_name, self.font_size)

        font.setBold(bold)
        self.font_metrics = QFontMetrics(font)
        self.font_height = self.font_metrics.height()

        ruby_font = QFont(font_name, self.ruby_font_size)
        ruby_font.setBold(bold)
        self.ruby_font_metrics = QFontMetrics(ruby_font)
        self.ruby_font_height = self.ruby_font_metrics.height()

        self.frame_width = frame_width
        self.sub_origin = math.floor(frame_height - (font_size/2 + bottom_margin))

    def get_line_height(self, line):
        for tag in line:
            if tag.isof(tags.TagText) and tag.ruby_text:
                return math.floor(self.normal_line_height * 1.5)
        return self.normal_line_height

    # Returns list of (layer, style, text) and postion of the next subtitle if a collision occurs
    def parse_sub(self, sub_text, start_position=None):
        sub_text = sub_text.replace('\\N', '\n')

        parsed_lines = self.tag_parser(sub_text)

        # Calculate line y positions
        # The origin of y positions is the center of the main line
        line_y_positions = [self.sub_origin if start_position is None else start_position]
        for line in reversed(parsed_lines):
            line_y_positions.insert(0, line_y_positions[0] - self.get_line_height(line))

        collision_position = line_y_positions.pop(0)

        # Process lines
        ret = []

        for line, y in zip(parsed_lines, line_y_positions):

            # Calculate part and line width
            widths = []

            for tag in line:
                if tag.isof(tags.TagText):
                    txt_no_tags = strip_ass_tags(tag.text)
                    ruby_txt_no_tags = strip_ass_tags(tag.ruby_text)

                    txt_width = self.font_metrics.horizontalAdvance(txt_no_tags)
                    ruby_txt_width = self.ruby_font_metrics.horizontalAdvance(ruby_txt_no_tags)

                    widths.append(max(txt_width, ruby_txt_width))
                else:
                    widths.append(0)

            line_width = sum(widths)

            # Center vertical position of ruby text
            ruby_y = math.floor(y - self.font_height/2 - self.ruby_font_size/2)

            # Left side of current part
            curr_x = round(self.frame_width/2 - line_width/2)

            # States for opened underlines
            underline_start_tag = None
            underline_start_x = None

            # States for opened highlights
            highlight_start_tag = None
            highlight_start_x = None
            highlight_height = None


            for (tag, width) in zip(line, widths):
                # Center of current part
                x = round(curr_x + width/2)

                # Text
                if tag.isof(tags.TagText):
                    if tag.text.strip():
                        # Insert zero width spaces around exposed spaces to prevent them collapsing
                        text = tag.text
                        text_stripped = strip_ass_tags(text)
                        if len(text_stripped) > 1:
                            if text_stripped.startswith(' '):
                                text = '\u200B' + text
                            if text_stripped.endswith(' '):
                                text = text + '\u200B'
                        ret.append( (3, 'Default', '{\\pos(%d,%d)}%s' % (x, y, text)) )

                    if tag.ruby_text.strip():
                        ret.append( (2, 'Ruby', '{\\pos(%d,%d)}%s' % (x, ruby_y, tag.ruby_text)) )
                        highlight_height = self.normal_line_height * 1.5

                # Underlines
                elif tag.isof(tags.TagUnderlineStart):
                    underline_start_tag = tag
                    underline_start_x = x

                elif tag.isof(tags.TagUnderlineEnd):
                    if underline_start_tag:
                        x1 = underline_start_x
                        x2 = x
                        y1 = math.ceil(y + self.font_height/2)
                        y2 = math.ceil(y1 + self.font_height*0.05)
                        c = '%02X%02X%02X' % (underline_start_tag.b, underline_start_tag.g, underline_start_tag.r)
                        ret.append( (1, 'Underline', '{\\pos(0,0)}{\c&H%s&}{\p1}m %d %d l %d %d %d %d %d %d{\p0}{\c}' % (c, x1, y1, x2, y1, x2, y2, x1, y2)) )

                # Highlights
                elif tag.isof(tags.TagHighlightStart):
                    highlight_start_tag = tag
                    highlight_start_x = x
                    highlight_height = self.font_height

                elif tag.isof(tags.TagHighlightEnd):
                    if highlight_start_tag:
                        x1 = highlight_start_x
                        x2 = x
                        y1 = math.ceil(y + self.font_height/2)
                        y2 = math.ceil(y1 - highlight_height)
                        c = '%02X%02X%02X' % (highlight_start_tag.b, highlight_start_tag.g, highlight_start_tag.r)
                        ca_raw = max(0, min(1, highlight_start_tag.a))
                        ca = round((1-ca_raw) * 255)
                        ret.append( (0, 'Highlight', '{\\pos(0,0)}{\c&H%s&\\1a&H%02X&}{\p1}m %d %d l %d %d %d %d %d %d{\p0}{\c\\1a}' % (c, ca, x1, y1, x2, y1, x2, y2, x1, y2)) )

                curr_x += width

        return ret, collision_position


def convert_sub_file(in_path, out_path, tag_parser=tag_parse_ruby.parse):

    # Determine encoding
    f = open(in_path, 'rb')
    subs_data = f.read()
    f.close()

    boms_for_enc = [
        ('utf-32',      (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)),
        ('utf-16',      (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)),
        ('utf-8-sig',   (codecs.BOM_UTF8,)),
    ]

    for enc, boms in boms_for_enc:
        if any(subs_data.startswith(bom) for bom in boms):
            subs_encoding = enc
            break
    else:
        chardet_ret = chardet.detect(subs_data)
        subs_encoding = chardet_ret['encoding']

    # Load subs
    with open(in_path, encoding=subs_encoding, errors='replace') as f:
        subs = pysubs2.SSAFile.from_file(f)

    # Determine frame size
    frame_width = int(subs.info.get('PlayResX', '1920'))
    frame_height = int(subs.info.get('PlayResY', '1080'))

    bottom_margin = round(frame_height * 0.04)

    # Create styles
    style = subs.styles.get('Default')
    if style is None:
        # TODO: Set better default style if Default is not found
        style = pysubs2.SSAStyle()
    else:
        bottom_margin = round(style.marginv)

    style.fontsize = math.floor(style.fontsize)
    style.italic = False
    style.underline = False
    style.strikeout = False
    style.scalex = 100.0
    style.scaley = 100.0
    style.spacing = 0.0
    style.angle = 0.0
    style.alignment = 5     # Center alignment
    style.marginl = 0
    style.marginr = 0
    style.marginv = 0

    ruby_style = style.copy()
    ruby_style.fontsize = math.floor(style.fontsize / 2)

    underline_style = style.copy()
    underline_style.alignment = 7   # Top-left alignment

    highlight_style = style.copy()
    highlight_style.outline = 0
    highlight_style.shadow = 0
    highlight_style.alignment = 7   # Top-left alignment

    subs.styles.clear()
    subs.styles['Default'] = style
    subs.styles['Ruby'] = ruby_style
    subs.styles['Underline'] = underline_style
    subs.styles['Highlight'] = highlight_style

    font_name = style.fontname
    font_size = style.fontsize
    ruby_font_size = ruby_style.fontsize
    bold = style.bold
    
    parser = RubySubParser(frame_width, frame_height, bottom_margin, font_name, font_size, ruby_font_size, bold, tag_parser)

    # Create parsed subtitle events
    original_events = subs.events.copy()
    original_events.sort()
    subs.events.clear()

    collision_stack = []    # (end, position)

    for e in original_events:
        position = None
        for collision_end, collision_position in reversed(collision_stack):
            if collision_end <= e.start:
                del collision_stack[-1]
            else:
                position = collision_position
                break
        
        parts, collision_position = parser.parse_sub(e.text, position)
        collision_stack.append((e.end, collision_position))

        for (layer, style, text) in parts:
            e = e.copy()
            e.layer = layer
            e.style = style
            e.text = text
            subs.events.append(e)

    subs.save(out_path, header_notice='Generated by rubysubs')
