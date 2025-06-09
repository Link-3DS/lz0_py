import utils
import defs
import io


class LZ0Decompressor:

    def decompress1x(self, r: io.BufferedReader, in_len: int, out_len: int = 0) -> bytes:
        out = bytearray()
        in_reader = utils.Reader(r, in_len)

        def safe_read_u8():
            if not in_reader.cur:
                in_reader.rebuffer()
            return in_reader.read_u8()

        try:
            ip = safe_read_u8()
            t = ip - 17
            if ip > 17:
                if t < 4:
                    pass
                else:
                    in_reader.read_append(out, t)
                ip = safe_read_u8()

            while True:
                t = ip
                if t >= 16:
                    pass
                else:
                    if t == 0:
                        t = in_reader.read_multi(15)
                    in_reader.read_append(out, t + 3)
                    ip = safe_read_u8()
                    t = ip
                    if t >= 16:
                        pass
                    else:
                        m_pos = len(out) - (1 + defs.m2_MAX_OFFSET)
                        m_pos -= t >> 2
                        ip = safe_read_u8()
                        m_pos -= ip << 2
                        if m_pos < 0:
                            raise utils.LookBehindUnderrun()
                        utils.copy_match(out, m_pos, 3)
                        ip = safe_read_u8()
                        t = ip
                        if t & 3:
                            in_reader.read_append(out, t & 3)
                            ip = safe_read_u8()
                        continue

                while True:
                    t = ip
                    if t >= 64:
                        m_pos = len(out) - 1 - ((t >> 2) & 7)
                        ip = safe_read_u8()
                        m_pos -= ip << 3
                        utils.copy_match(out, m_pos, (t >> 5) - 1 + 2)
                    elif t >= 32:
                        t &= 31
                        if t == 0:
                            t = in_reader.read_multi(31)
                        v16 = in_reader.read_u16()
                        m_pos = len(out) - 1 - (v16 >> 2)
                        if m_pos < 0:
                            raise utils.LookBehindUnderrun()
                        utils.copy_match(out, m_pos, t + 2)
                    elif t >= 16:
                        m_pos = len(out) - ((t & 8) << 11)
                        t &= 7
                        if t == 0:
                            t = in_reader.read_multi(7)
                        v16 = in_reader.read_u16()
                        m_pos -= v16 >> 2
                        if m_pos == len(out):
                            return bytes(out)
                        m_pos -= 0x4000
                        if m_pos < 0:
                            raise utils.LookBehindUnderrun()
                        utils.copy_match(out, m_pos, t + 2)
                    else:
                        m_pos = len(out) - 1 - (t >> 2)
                        ip = safe_read_u8()
                        m_pos -= ip << 2
                        if m_pos < 0:
                            raise utils.LookBehindUnderrun()
                        utils.copy_match(out, m_pos, 2)
                        ip = safe_read_u8()
                        t = ip
                        if t & 3:
                            in_reader.read_append(out, t & 3)
                            ip = safe_read_u8()
                        continue

                    t = ip & 3
                    if t == 0:
                        ip = safe_read_u8()
                        break
                    in_reader.read_append(out, t)
                    ip = safe_read_u8()

        except IndexError:
            raise EOFError("Unexpected end of input")
        return bytes(out)