from compressor import LZOCompressor
from decompressor import LZ0Decompressor
import io


class LZO:
    def compress(self, data: bytes) -> bytes:
        compressed = LZOCompressor.compress1x(data)
        if len(compressed) == 0:
            raise ValueError("Compression failed")
        compression_ratio = len(data) // len(compressed) + 1
        result = bytes([compression_ratio]) + compressed
        return result

    def decompress(self, data: bytes) -> bytes:
        compression_ratio = data[0]
        compressed = data[1:]
        if compression_ratio == 0:
            return compressed
        try:
            decompressed = LZ0Decompressor.decompress1x(compressed)
        except Exception as e:
            raise RuntimeError(f"Decompression failed: {e}")
        ratio_check = len(decompressed) // len(compressed) + 1
        if ratio_check != compression_ratio:
            raise ValueError(
                f"Failed to decompress payload. Got bad ratio. Expected {compression_ratio}, got {ratio_check}"
            )
        return decompressed

# EXAMPLE
original = b"hello world"
compressed = b'\x1chello world\x11\x00\x00'
print("Original:", original)
print("Compressed:", compressed)
print("Compressed size:", len(compressed))
reader = io.BufferedReader(io.BytesIO(compressed))
decompressor = LZ0Decompressor()
decompressed = decompressor.decompress1x(reader, len(compressed))

print("Decompressed:", decompressed)