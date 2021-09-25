import rubysubs
from PyQt5.QtGui import QGuiApplication


def main():
    import sys
    
    if len(sys.argv) < 3:
        print('Usage: %s <source subtitle> <output subtitle> [<tag parser> [arg0] [arg1] ...]' % sys.argv[0])
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    if len(sys.argv) >= 4:
        tag_parser_requested = sys.argv[3].lower().replace('-', '_')

        tag_parser_builders = {
            'ruby':     rubysubs.tag_parse_ruby.parser_from_string_args,
            'ja':       rubysubs.tag_parse_migaku_ja.parser_from_string_args,
            'zh':       rubysubs.tag_parse_migaku_zh.parser_from_string_args,
            'zh_hk':    rubysubs.tag_parse_migaku_zh.parser_from_string_args_HK,
            'eu':       rubysubs.tag_parse_migaku_eu.parser_from_string_args,
            'ko':       rubysubs.tag_parse_migaku_ko.parser_from_string_args,
        }

        if not tag_parser_requested in tag_parser_builders:
            print('Invalid tag parser.')
            sys.exit(1)

        tag_parser = tag_parser_builders[tag_parser_requested](sys.argv[4:])
    else:
        tag_parser = rubysubs.tag_parse_ruby.parse

    # Required for QFontMetrics
    qapp = QGuiApplication(sys.argv)

    rubysubs.convert_sub_file(in_path, out_path, tag_parser)

    sys.exit(0)


if __name__ == "__main__":
    main()