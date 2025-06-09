import io


class LZOError(Exception):
    pass


class InputUnderrun(LZOError):
    pass


class LookBehindUnderrun(LZOError):
    pass


class Reader:
    def __init__(self, reader: io.BufferedReader, inlen: int):
        self.r = reader
        self.len = inlen if inlen != 0 else -1
        self.buf = bytearray(4096)
        self.cur = bytearray()
        self.err = None
        self.rebuffer()

    def rebuffer(self):
        RBUF_WND = 32
        if len(self.cur) > RBUF_WND or self.len == 0:
            return

        rb = self.cur[:]
        self.cur = bytearray()
        self.cur.extend(rb)

        cur = self.buf[:4096 - len(rb)]
        if self.len >= 0 and len(cur) > self.len:
            cur = cur[:self.len]

        try:
            n = self.r.readinto(cur)
        except Exception as e:
            self.err = e
            self.cur = None
            return

        if n == 0:
            if len(rb) == 0:
                self.err = io.EOFError()
                self.cur = None
            return

        self.cur.extend(cur[:n])
        if self.len >= 0:
            self.len -= n

    def read_u8(self):
        ch = self.cur[0]
        self.cur = self.cur[1:]
        return ch

    def read_u16(self):
        b0, b1 = self.cur[0], self.cur[1]
        self.cur = self.cur[2:]
        return b0 + (b1 << 8)

    def read_multi(self, base):
        b = 0
        while True:
            for i, v in enumerate(self.cur):
                if v == 0:
                    b += 255
                else:
                    b += v + base
                    self.cur = self.cur[i+1:]
                    return b
            self.cur.clear()
            self.rebuffer()
            if not self.cur:
                self.err = io.EOFError()
                return

    def read_append(self, out: bytearray, n):
        while n > 0:
            m = min(len(self.cur), n)
            out.extend(self.cur[:m])
            self.cur = self.cur[m:]
            n -= m
            if len(self.cur) == 0:
                self.rebuffer()
                if not self.cur:
                    self.err = io.EOFError()
                    return

def copy_match(out: bytearray, m_pos: int, n: int):
    if m_pos + n > len(out):
        for i in range(n):
            out.append(out[m_pos])
            m_pos += 1
    else:
        out.extend(out[m_pos:m_pos+n])