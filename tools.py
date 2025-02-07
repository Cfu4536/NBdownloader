import os
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def sanitize_filename(filename):
    '''
    去掉文件名中的非法字符，并截断文件名长度
    :param filename:
    :return:
    '''
    # 定义不合法字符
    invalid_chars = r'[<>:"/\\|?*\']'

    # 使用正则表达式替换非法字符为下划线
    sanitized = re.sub(invalid_chars, '_', filename)

    # 检查文件名的长度，若过长则截断
    if len(sanitized) > 255:
        sanitized = sanitized[:255]

    # Windows保留的文件名
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL',
                      'COM1', 'COM2', 'COM3', 'COM4',
                      'COM5', 'COM6', 'COM7', 'COM8',
                      'COM9', 'LPT1', 'LPT2', 'LPT3',
                      'LPT4', 'LPT5', 'LPT6', 'LPT7',
                      'LPT8', 'LPT9'}

    # 去掉扩展名进行检查
    name_without_extension = os.path.splitext(sanitized)[0].upper()
    # 如果转化后的文件名是保留名，则将其后缀替换掉或加上下划线
    if name_without_extension in reserved_names:
        sanitized = f"{sanitized}_file"

    return sanitized


def extract_bvid(url: str) -> Optional[str]:
    """
    从URL中提取bvid
    :param url: 输入的URL
    :return: 提取到的bvid，如果没有找到则返回None
    """
    # 使用正则表达式查找bvid（假设bvid以'BV'开头，后接字符）
    match = re.search(r'(BV[a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)  # 返回第一个捕获的bvid
    return None  # 如果没有找到bvid，返回None


def replace_bvid(url, new_bvid):
    '''
    替换URL中的bvid
    :param url:
    :param new_bvid:
    :return:
    '''
    # 找到bvid的位置，假设bvid总是以'BV'开头并且后面有一些字符
    bvid_index = url.find('BV')
    if bvid_index == -1:
        return "URL中没有找到bvid"

    # 从bvid的位置提取到下一个'/'
    end_index = url.find('/', bvid_index)

    # 如果没有找到'/'
    if end_index == -1:
        end_index = len(url)

    # 替换bvid
    new_url = url[:bvid_index] + new_bvid + url[end_index:]
    return new_url


def modify_url_parameter(url, param_name, new_value):
    # 解析URL
    url_parts = urlparse(url)

    # 解析查询参数
    query_params = parse_qs(url_parts.query)

    # 修改或添加参数
    query_params[param_name] = [new_value]

    # 重新构建查询字符串
    new_query = urlencode(query_params, doseq=True)

    # 重新构建完整的URL
    new_url = urlunparse(url_parts._replace(query=new_query))

    return new_url


def format_size(size_bytes):
    """将字节数转换为更可读的格式（KB, MB, GB, TB）。"""
    # 定义单位
    units = ['B', 'KB', 'MB', 'GB', 'TB']

    # 计算大小
    if size_bytes == 0:
        return "0 B"

    size_index = 0
    while size_bytes >= 1024 and size_index < len(units) - 1:
        size_bytes /= 1024.0
        size_index += 1

    # 格式化输出
    return f"{size_bytes:.1f} {units[size_index]}"
