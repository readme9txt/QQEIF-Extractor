import msvcrt
import os
import warnings

import compoundfiles
from tqdm import tqdm

warnings.filterwarnings("ignore")

print('==================================')
print('QQ表情EIF包表情文件提取工具 by Readme9txt')
print('v1.0.0 Build 2024/08/03')
print('==================================')
print('功能：提取PC版QQ导出的EIF格式表情包中的图片，并保留分组和分组中的表情排序(云端分组不支持排序)')
print('关于作者: https://remilia-scarlet.com/')
print('-------------------------------------------------------')

while True:
    user_input = input("请输入EIF文件路径或者直接拖入: ")
    if user_input.startswith('"') and user_input.endswith('"'):
        user_input = user_input[1:-1]
    if os.path.exists(user_input) and user_input.endswith('.eif'):
        break
    print('路径不正确，请重新输入')

doc = compoundfiles.CompoundFileReader(user_input)


# print(doc.root)

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


e_str_file_org = b'\x98\xeb\x9f\xeb\x99\xeb\xad\xeb\x82\xeb\x87\xeb\x8e\xeb\x84\xeb\x99\xeb\x8c\xeb'  # strFileorg对应密文

# 建立索引
group_dict = {}
face_dat = 'Face.dat'
with doc.open(doc.root[face_dat]) as stream:
    for line in tqdm(stream, desc='建立索引'):
        s = line.strip()
        start = s.find(e_str_file_org)
        if start != -1:
            part = s[start + len(e_str_file_org) + 4:]
            key, idx = find_key(part, 0)
            e_str_file_org_value, _ = get_part(part, key, idx)
            d_part = ''.join([chr(a ^ key) for a in e_str_file_org_value if (a ^ key) != 0])
            if len(d_part.split(':')) > 1:
                # 多分组
                if d_part.startswith('UserDataCustomFace'):
                    d_part = d_part[len('UserDataCustomFace:'):]
                else:
                    continue
            s_arr = d_part.split('\\')
            group = s_arr[0]
            filename = s_arr[1]
            if group_dict.get(group) is None:
                group_dict[group] = {}
            group_dict[group][filename] = len(group_dict[group])

# 导出表情
output = 'output'
if not os.path.exists(output):
    os.mkdir(output)
for entry in doc.root:
    if entry.isdir:
        group = os.path.join(output, entry.name)
        if not os.path.exists(group):
            os.mkdir(group)
        for sub in tqdm(entry, desc=f'导出分组: {entry.name:0>4}'):
            name, ext = sub.name.split('.')
            if name.endswith('fix') or name.endswith('tmp') or name.endswith('tmb'):
                continue
            if len(entry.name) < 4 and entry.name in group_dict and sub.name in group_dict[entry.name]:
                path = f'{group}/{group_dict[entry.name][sub.name]}.{ext}'
            else:
                path = f'{group}/index_loss_{sub.name}'
            with doc.open(sub) as stream:
                with open(path, 'wb') as file:
                    file.write(stream.read())
print(f'导出结束，输出路径{os.path.abspath(output)}')
print(f'按任意键退出')
msvcrt.getch()
