class TagBaseMeta(type):

    def __repr__(cls):
        return cls.__name__

class TagBase(metaclass=TagBaseMeta):

    @classmethod
    def isof(cls, tag_type):
        return issubclass(cls, tag_type)


class TagText(TagBase):

    def __init__(self, text='', ruby_text=''):
        self.text = text
        self.ruby_text = ruby_text

    def __repr__(self):
        return '%s(\'%s\', \'%s\')' % (self.__class__.__name__, self.text, self.ruby_text)


class TagUnderlineStart(TagBase):

    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return '%s(r=%d, g=%d, b=%d)' % (self.__class__.__name__, self.r, self.g, self.b)

class TagUnderlineEnd(TagBase):
    pass


class TagHighlightStart(TagBase):

    def __init__(self, r=0, g=0, b=0, a=255):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __repr__(self):
        return '%s(r=%d, g=%d, b=%d, a=%d)' % (self.__class__.__name__, self.r, self.g, self.b, self.a)

class TagHighlightEnd(TagBase):
    pass
