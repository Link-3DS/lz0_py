from . import defs


class LZOCompressor:

    def append_multi(self, out: bytearray, t: int):
        while t > 255:
            out.append(0)
            t -= 255
        out.append(t)
        return out

    def compress(self, data: bytes):
        out = bytearray()
        dict_table = [-1] * (1 << defs.d_BITS)
        in_len = len(data)
        ip_len = in_len - defs.m2_MAX_LEN - 5
        ii = 0
        ip = 4

        while ip < ip_len:
            key = (data[ip + 3] << 6) ^ data[ip + 2]
            key = (key << 5) ^ data[ip + 1]
            key = (key << 5) ^ data[ip]
            dindex = ((0x21 * key) >> 5) & defs.d_MASK
            m_pos = dict_table[dindex]

            if m_pos < 0 or ip == m_pos or (ip - m_pos) > defs.m4_MAX_OFFSET:
                goto_literal = True
            else:
                m_off = ip - m_pos
                if m_off <= defs.m2_MAX_OFFSET or data[m_pos + 3] == data[ip + 3]:
                    goto_literal = False
                else:
                    dindex = (dindex & (defs.d_MASK & 0x7FF)) ^ (defs.d_HIGH | 0x1F)
                    m_pos = dict_table[dindex]
                    if m_pos < 0 or ip == m_pos or (ip - m_pos) > defs.m4_MAX_OFFSET:
                        goto_literal = True
                    else:
                        m_off = ip - m_pos
                        if m_off <= defs.m2_MAX_OFFSET or data[m_pos + 3] == data[ip + 3]:
                            goto_literal = False
                        else:
                           goto_literal = True

            if goto_literal:
                dict_table[dindex] = ip
                ip += 1 + ((ip - ii) >> 5)
                continue

            if (
                data[m_pos] != data[ip]
                or data[m_pos + 1] != data[ip + 1]
                or data[m_pos + 2] != data[ip + 2]
            ):
                dict_table[dindex] = ip
                ip += 1 + ((ip - ii) >> 5)
                continue

            dict_table[dindex] = ip
            if ip != ii:
                t = ip - ii
                if t <= 3:
                    out[-2] |= t
                elif t <= 18:
                    out.append(t - 3)
                else:
                    out.append(0)
                    self.append_multi(out, t - 18)
                out += data[ii:ip]
                ii = ip

            ip += 3
            i = 3
            while i < 9 and ip < in_len and data[m_pos + i] == data[ip]:
                ip += 1
                i += 1

            m_len = ip - ii
            m_off = ip - m_pos

            if i < 9:
                if m_off <= defs.m2_MAX_OFFSET:
                    m_off -= 1
                    out.append(((m_len - 1) << 5) | ((m_off & 7) << 2))
                    out.append(m_off >> 3)
                elif m_off <= defs.m3_MAX_OFFSET:
                    m_off -= 1
                    out += [defs.m3_MARKER | (m_len - 2), ((m_off & 63) << 2), m_off >> 6]
                else:
                    m_off -= 0x4000
                    out += [
                        defs.m4_MARKER | ((m_off & 0x4000) >> 11) | (m_len - 2),
                        (m_off & 63) << 2,
                        m_off >> 6,
                    ]
            else:
                m = m_pos + defs.m2_MAX_LEN + 1
                while ip < in_len and data[m] == data[ip]:
                    m += 1
                    ip += 1
                m_len = ip - ii
                if m_off <= defs.m3_MAX_OFFSET:
                    m_off -= 1
                    if m_len <= 33:
                        out.append(defs.m3_MARKER | (m_len - 2))
                    else:
                        m_len -= 33
                        out.append(defs.m3_MARKER)
                        self.append_multi(out, m_len)
                else:
                    m_off -= 0x4000
                    if m_len <= defs.m4_MAX_LEN:
                        out.append(defs.m4_MARKER | ((m_off & 0x4000) >> 11) | (m_len - 2))
                    else:
                        m_len -= defs.m4_MAX_LEN
                        out.append(defs.m4_MARKER | ((m_off & 0x4000) >> 11))
                        self.append_multi(out, m_len)
                out += [(m_off & 63) << 2, m_off >> 6]

            ii = ip

        sz = in_len - ii
        return out, sz

    def compress1x(self, data: bytes):
        out = bytearray()
        in_len = len(data)
        if in_len <= defs.m2_MAX_LEN + 5:
            t = in_len
        else:
            out, t = self.compress(data)

        if t > 0:
            ii = in_len - t
            if len(out) == 0 and t <= 238:
                out.append(17 + t)
            elif t <= 3:
                out[-2] |= t
            elif t <= 18:
                out.append(t - 3)
            else:
                out.append(0)
                self.append_multi(out, t - 18)
            out += data[ii : ii + t]

        out += bytearray([defs.m4_MARKER | 1, 0, 0])
        # out += [defs.m4_MARKER | 1, 0, 0]
        return bytes(out)
