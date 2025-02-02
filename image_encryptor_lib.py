import struct
import zlib
import tkinter as tk
from tkinter import filedialog
import os
import re
import time
from cryptography.fernet import Fernet
import hashlib
import base64


TIMESTAMP = time.time()
root = tk.Tk()
root.withdraw()

def validate_png_header(file_path: str) -> None:
    with open(file_path, 'rb') as f:
        header = f.read(8)
    if header != b'\x89PNG\r\n\x1a\n':
        raise ValueError("文件不是有效的PNG格式")

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def select_png_file(purpose: str) -> str:
    while True:
        try:
            file_path = filedialog.askopenfilename(
                title=purpose,
                filetypes=[("PNG Files", "*.png")]
            )
            if not file_path:
                return
            validate_png_header(file_path)
            print(f"已选择PNG文件：{file_path}")
            return file_path
        except ValueError as e:
            print(f"错误：{e}")

def select_encrypted_png_file(purpose) -> str:
    while True:
        try:
            file_path = filedialog.askopenfilename(
                title=purpose,
                filetypes=[("PNG Files", "*.png")]
            )
            if not file_path:
                return

            validate_png_header(file_path)  

            chunks = read_png_chunks(file_path)
            iend_data = chunks[-1][1]  
            
            if b'\0' not in iend_data:
                print(
                    "该文件不包含有效加密数据（缺失数据分隔符）\n"
                    "可能原因：\n"
                    "1. 文件未经过加密处理\n"
                    "2. 文件已损坏"
                )
                 
                return 1

            print(f"[成功] 加密文件已验证：{file_path}")
            return file_path

        except ValueError as e:
            error_msg = f"""
            {'-'*40}
            文件选择错误：{e}
            请重新选择有效的加密PNG文件！
            {'-'*40}
            """
            print(error_msg)
            continue  

def select_any_file(purpose) -> str:
    while True:
        file_path = filedialog.askopenfilename(title=purpose)
        if file_path:
            print(f"已选择文件：{file_path}")
            return file_path
        else:
            return

def select_output_dir(purpose) -> str:

    while True:
        dir_path = filedialog.askdirectory(title=purpose)
        if dir_path:
            print(f"输出目录：{dir_path}")
            return dir_path
        else:
            return

def generate_encryption_key(user_input) -> bytes:
   hashed = hashlib.sha256(user_input.encode()).digest()
   return base64.urlsafe_b64encode(hashed)

def encrypt_file_data(key: bytes, input_data: str, judgment) -> bytes:
    cipher = Fernet(key)
    if judgment == 0:
        with open(input_data, 'rb') as f:
            return cipher.encrypt(f.read())
    else:
        out_put = input_data.encode('utf-8')
        return cipher.encrypt(out_put)

def decrypt_data(key: bytes, encrypted_data: bytes) -> bytes:
    try:
        decrypt = Fernet(key).decrypt(encrypted_data)
        if isinstance(decrypt, str):
            decrypt = decrypt.decode('utf-8')
        return decrypt
    except Exception as e:
        raise ValueError(f"解密失败：{e}") from e

def read_png_chunks(file_path: str) -> list:
    validate_png_header(file_path)
    chunks = []
    with open(file_path, 'rb') as f:
        f.read(8)  
        while True:
            length_bytes = f.read(4)
            if not length_bytes: break
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = struct.unpack(">I", f.read(4))[0]
            chunks.append((chunk_type, data, crc))
            if chunk_type == b'IEND': break
    return chunks

def hide_file_in_png(png_path: str, data: str, output_path: str, key, judgment) -> None:
    if judgment == 1:
        encrypted_data = encrypt_file_data(key, data, judgment)
    else:
        encrypted_data = encrypt_file_data(key, data, judgment)
    
    acquiescent_name = '.txt'
    if not os.path.splitext(data)[1].encode():
        file_extension = acquiescent_name.encode() + b'\0'
    else:
        file_extension = os.path.splitext(data)[1].encode() + b'\0'
    file_size = len(encrypted_data)

    payload = file_extension + struct.pack(">I", file_size) + encrypted_data

    chunks = read_png_chunks(png_path)
    last_chunk_type, last_chunk_data, _ = chunks[-1]

    modified_data = last_chunk_data + payload
    new_crc = zlib.crc32(modified_data)
    chunks[-1] = (last_chunk_type, modified_data, new_crc)

    with open(output_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        for chunk_type, data, crc in chunks:
            f.write(struct.pack(">I", len(data)))
            f.write(chunk_type)
            f.write(data)
            f.write(struct.pack(">I", crc))
    
    print(f"文件已隐藏至：{output_path}")


def extract_files_from_png(png_path: str, output_dir: str, key) -> None:

    chunks = read_png_chunks(png_path)
    _, iend_data, _ = chunks[-1]  
    os.makedirs(output_dir, exist_ok=True)

    offset = 0
    extracted_files = 0

    while offset < len(iend_data):
        null_byte_index = iend_data.find(b'\0', offset)
        if null_byte_index == -1:
            print("未找到更多隐藏文件，提取完成。")
            break

        file_extension = iend_data[offset:null_byte_index]
        offset = null_byte_index + 1  

        if offset + 4 > len(iend_data):
            print("文件大小字段损坏，提取失败。")
            break
        file_size = struct.unpack(">I", iend_data[offset:offset+4])[0]
        offset += 4

        if offset + file_size > len(iend_data):
            print(f"文件数据损坏，提取失败。（文件大小: {file_size} 字节, 剩余数据: {len(iend_data) - offset} 字节）")
            break

        encrypted_data = iend_data[offset:offset + file_size]
        offset += file_size  

        try:
            decrypted_data = decrypt_data(key, encrypted_data)
            if not decrypted_data:
                print("解密失败，跳过此文件。")
                continue
        except Exception as e:
            print(f"文件 {file_extension} 解密失败，错误: {e}")
            continue
        
        file_extension = file_extension.decode()
        print(f'debug2{decrypted_data}')

        if isinstance(decrypted_data,(bytes, bytearray)):
            print(f'debug1{decrypted_data}')
            decrypted_data = decrypted_data.decode()
            print(f'debug3{decrypted_data}')
            decrypted_data = str(decrypted_data)
            print(f'debug{decrypted_data}')
        safe_filename = f"extracted_{int(time.time())}{extracted_files}{file_extension}"
        output_path = os.path.join(output_dir, safe_filename)

        try:
            with open(output_path, 'w') as f:
                f.write(decrypted_data)
            print(f"文件成功提取: {output_path}")
        except Exception as e:
            print(f"文件写入失败: {e}")

        extracted_files += 1

    print(f"提取完成，提取数量：{extracted_files}")

