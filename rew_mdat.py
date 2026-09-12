"""Read the data-only Java serialization subset used by supplied REW sessions.

Does not load Java classes or execute serialized methods. Unsupported stream
constructs fail explicitly. Format: Oracle Serialization Specification, §6.
"""
from pathlib import Path
import struct
import numpy as np


class Reader:
    def __init__(self, data):
        self.data, self.pos, self.refs = data, 0, []
        if self.take(4) != b'\xac\xed\x00\x05':
            raise ValueError('Not a Java serialization v5 stream')

    def take(self, n):
        if n < 0 or self.pos + n > len(self.data):
            raise ValueError(f'Truncated/invalid stream at {self.pos}')
        result = self.data[self.pos:self.pos+n]
        self.pos += n
        return result

    def number(self, fmt):
        return struct.unpack('>' + fmt, self.take(struct.calcsize('>' + fmt)))[0]

    def utf(self, long=False):
        n = self.number('q' if long else 'H')
        return self.take(n).replace(b'\xc0\x80', b'\x00').decode('utf8', 'surrogatepass')

    def register(self, value):
        self.refs.append(value)
        return value

    def annotation(self):
        values = []
        while self.data[self.pos] != 0x78:
            values.append(self.read())
        self.pos += 1
        return values

    def read(self):
        tag = self.number('B')
        if tag == 0x70:
            return None
        if tag == 0x71:
            return self.refs[self.number('I') - 0x7e0000]
        if tag in (0x74, 0x7c):
            return self.register(self.utf(tag == 0x7c))
        if tag in (0x77, 0x7a):
            return self.take(self.number('B' if tag == 0x77 else 'I'))
        if tag == 0x79:
            self.refs.clear()
            return None
        if tag == 0x72:
            name, uid = self.utf(), self.number('q')
            cls = self.register({'name': name, 'uid': uid})
            cls['flags'] = self.number('B')
            fields = []
            for _ in range(self.number('H')):
                kind, name = chr(self.number('B')), self.utf()
                descriptor = self.read() if kind in '[L' else None
                fields.append((kind, name, descriptor))
            cls['fields'] = fields
            cls['annotation'] = self.annotation()
            cls['super'] = self.read()
            return cls
        if tag == 0x73:
            cls = self.read()
            obj = self.register({'_class': cls['name']})
            chain = []
            while cls:
                chain.append(cls)
                cls = cls['super']
            for cls in reversed(chain):
                flags = cls['flags']
                if flags & 4:
                    if not flags & 8:
                        raise ValueError('Unframed externalizable object')
                    obj['_extra_' + cls['name']] = self.annotation()
                    continue
                for kind, name, _ in cls['fields']:
                    obj[name] = (self.read() if kind in '[L' else
                                 self.number(dict(B='b', C='H', D='d', F='f',
                                                  I='i', J='q', S='h', Z='?')[kind]))
                if flags & 1:
                    obj['_extra_' + cls['name']] = self.annotation()
            return obj
        if tag == 0x75:
            cls = self.read()
            index = len(self.refs)
            values = self.register([])
            n = self.number('i')
            kind = cls['name'][1]
            dtype = {'B': 'i1', 'Z': '?', 'C': '>u2', 'S': '>i2', 'I': '>i4',
                     'J': '>i8', 'F': '>f4', 'D': '>f8'}.get(kind)
            if dtype:
                values = np.frombuffer(self.take(n * np.dtype(dtype).itemsize), dtype=dtype).copy()
                self.refs[index] = values
            else:
                values.extend(self.read() for _ in range(n))
            return values
        if tag == 0x7e:
            cls = self.read()
            obj = self.register({'_enum': cls['name']})
            obj['value'] = self.read()
            return obj
        if tag == 0x76:
            return self.register({'_class_object': self.read()})
        raise ValueError(f'Unsupported Java stream tag {tag:#x} at {self.pos-1}')


def load(path):
    reader = Reader(Path(path).read_bytes())
    values = []
    while reader.pos < len(reader.data):
        values.append(reader.read())
    return values
