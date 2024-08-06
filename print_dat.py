import logging
import sys
import warnings

import compoundfiles
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, filename='output.log', format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

warnings.filterwarnings("ignore")
doc = compoundfiles.CompoundFileReader(r"C:\Users\Read\Desktop\pkq.eif")
print(doc.root)


def bytes_to_escaped_string(byte_string):
    return ''.join(f'\\x{byte:02x}' for byte in byte_string)


def find_key(line_bytes, start_idx):
    """ 寻找重复三次的key """
    for i, byte in enumerate(line_bytes[start_idx:], start=start_idx):
        if i + 4 >= len(line_bytes):
            break
        if byte == line_bytes[i + 2] and byte == line_bytes[i + 4]:
            key = byte
            seek = i  # 记录位置
            last_value = line_bytes[start_idx:seek - 1]
            return key, seek
    return None, 0


def get_part(line_bytes, key, start_idx):
    """ 根据key寻找段落 """
    end = 0
    for i in range(start_idx, len(line_bytes), 2):
        byte = line_bytes[i]
        if byte != key:
            end = i - 1
            break
    if end == 0:  # 到达结尾
        end = len(line_bytes) - 1
    p = line_bytes[start_idx - 1:end]
    return p, end


def decode(line_bytes):
    """ 解码 """
    idx = 0
    while idx < len(line_bytes):
        key, seek = find_key(line_bytes, idx)
        if key is None:
            break
        value = bytes_to_escaped_string(line_bytes[idx:seek - 1])
        print(value, end=' ')
        part, end = get_part(line_bytes, key, seek)
        idx = end
        d_part = ''.join([chr(a ^ key) for a in part if (a ^ key) != 0])  # 异或
        print(d_part, end=' ')


face_dat = 'Face.dat'
with doc.open(doc.root[face_dat]) as stream:
    for line in stream:
        s = line.strip()
        decode(s)
        print('')
