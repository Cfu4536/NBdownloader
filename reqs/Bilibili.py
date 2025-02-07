import os
import subprocess
import time
from pprint import pprint

import tools
from tqdm import tqdm
import requests
import re
import json
import CONST


class Bilibili:
    def __init__(self, is_UI: bool = False):
        '''
        task info =  {
            "title1": {
                'status': '等待中',
                'total_size': 0,
                'size': 0,
                'speed': 0,
            },
        }
        :param is_UI:
        '''
        self.is_UI = is_UI  # 默认不显示UI
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62",
            "Referer": "https://www.bilibili.com/",
            "cookie": CONST.COOKIE_BILIBILI
        }
        self.max_quality = -1  # 最高质量
        self.accept_option = {}  # 可选择的清晰度
        self.task_info = {}  # 任务信息

        self.play_info_json_data = None
        self.inital_state_json_data = None

    def download_file(self, url: str, headers: dict, file_path: str, title: str) -> bool:
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()  # 检查请求是否成功

            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            self.task_info[title]['total_size'] += total_size

            # # 使用 tqdm 显示进度条
            # with open(file_path, mode="wb") as f, tqdm(
            #         total=total_size, unit='B', unit_scale=True, desc=file_path
            # ) as bar:
            #     for chunk in response.iter_content(chunk_size=8192):
            #         f.write(chunk)
            #         bar.update(len(chunk))
            #         self.task_info[title]['size'] += 8192

            with open(file_path, mode="wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    self.task_info[title]['size'] += 8192

            return True

        except Exception as e:
            print(f"发生错误: {str(e)}")
            return False

    def get_video(self, url):
        try:
            resp = requests.get(url=url, headers=self.headers)
        except:
            print("requests.get error")
            return False
        # 解析数据
        self.status = "数据解析"

        title = re.findall('<title data-vue-meta="true">(.*?)</title>', resp.text)[0]
        title = tools.sanitize_filename(title)
        title = title.replace("&quot;", '"') + "_" + str(int(time.time()))

        play_info = re.findall('<script>window.__playinfo__=(.*?)</script>', resp.text)[0]
        self.play_info_json_data = json.loads(play_info)
        initial_state = re.findall('<script>window.__INITIAL_STATE__=(.*?);\(function', resp.text)[0]
        self.inital_state_json_data = json.loads(initial_state)

        amt = re.findall('<div class="amt" data-v-116f0ccc>（(.*?)）</div>', resp.text)
        page_len = 1
        if len(amt) > 0:  # 有合集的视频-合集数量
            page_len = int(str(amt[0]).split("/")[1])

        bvid_list = []
        title_list = []
        p_list = []
        page_cnt = 0
        for dict_v in self.inital_state_json_data['availableVideoList']:
            bvid_cur_list = [i.get('bvid') for i in dict_v['list']]
            title_cur_list = [i.get('title') for i in dict_v['list']]
            cur_p_list = [i.get('p') for i in dict_v['list']]
            bvid_list.extend(bvid_cur_list)
            title_list.extend(title_cur_list)
            p_list.extend(cur_p_list)
            page_cnt += len(cur_p_list)
            if page_cnt >= page_len:
                break

        self.task_info[title] = {
            'status': '等待中',
            'total_size': 0,
            'size': 0,
            'speed': 0,
        }

        # 获取视频质量
        self.max_quality = self.play_info_json_data['data']['dash']['video'][0]['id']  # 最高质量
        accept_description = self.play_info_json_data['data']['accept_description']  # 质量
        accept_quality = self.play_info_json_data['data']['accept_quality']  # 质量-id
        self.accept_option = dict(zip(accept_quality, accept_description))

        return title, list(zip(bvid_list[:page_len], title_list[:page_len], p_list[:page_len]))

    def get_video_url(self, accept_id: int or str):
        duration = self.play_info_json_data['data']['dash']['duration']  # 时长s

        audio_dash = self.play_info_json_data['data']['dash']['audio']
        video_dash = self.play_info_json_data['data']['dash']['video']
        # 更新视频质量
        if video_dash[0]['id'] < accept_id:
            accept_id = video_dash[0]['id']
        # 获取音频和视频url
        audio_url = audio_dash[0]['baseUrl']
        video_url = ''  # 视频url
        for i in range(len(video_dash)):
            if video_dash[i]['id'] == int(accept_id):
                video_url = video_dash[i]['baseUrl']
                break
        # print("视频质量：", self.accept_option[int(accept_id)])
        # print("视频时长：", duration)
        # print("音频url：", audio_url)
        # print("视频url：", video_url)
        return audio_url, video_url

    def request_video(self, audio_url: str, video_url: str, title: str):
        # 下载音频
        self.task_info[title]['status'] = "下载音频中"
        if not self.download_file(audio_url, self.headers, os.path.join(CONST.TEMP_DIR, title + ".mp3"), title):
            print("音频请求失败！")
            self.task_info[title]['status'] = "音频失败"
            return False

        # 下载视频
        self.task_info[title]['status'] = "下载视频中"
        if not self.download_file(video_url, self.headers, os.path.join(CONST.TEMP_DIR, title + ".mp4"), title):
            print("视频请求失败！")
            self.task_info[title]['status'] = "视频失败"
            return False

        self.task_info[title]['size'] = self.task_info[title]['total_size']  # 防止不一致
        return True

    def merge_video(self, title):
        self.task_info[title]['status'] = "合并文件中"
        '''
        ffmpeg -i b.mp4 -i a.mp3 -c:v copy -c:a aac -strict experimental test.mp4
         # 输入文件路径
        video_file = "C:\\path\\to\\your\\video.mp4"
        audio_file = "C:\\path\\to\\your\\audio.mp3"
        output_file = "C:\\path\\to\\your\\output.mp4"
        '''

        # FFmpeg命令
        command = [
            "./bin/ffmpeg.exe",
            "-i", os.path.join(CONST.TEMP_DIR, title + ".mp4"),
            "-i", os.path.join(CONST.TEMP_DIR, title + ".mp3"),
            "-c:v", "copy",
            "-c:a", "copy",
            "-loglevel", "quiet",
            "-strict", "experimental",
            os.path.join(CONST.OUTPUTS_DIR, title + ".mp4")
        ]

        # 执行命令
        subprocess.run(command)

        # 删除临时文件
        os.remove(os.path.join(CONST.TEMP_DIR, title + ".mp4"))
        os.remove(os.path.join(CONST.TEMP_DIR, title + ".mp3"))

        self.task_info[title]['status'] = "完成"

        return True

    def download(self, audio_url: str, video_url: str, title: str):
        '''
        请求和合并的封装
        :param audio_url:
        :param video_url:
        :param title:
        :return:
        '''
        if not self.request_video(audio_url, video_url, title):
            return False
        if not self.merge_video(title):
            return False
        return True

    def get_task_info(self):
        '''
        获取全部任务信息
        :return:
        '''

        # 格式化输出
        for title, info in self.task_info.items():
            total_size = tools.format_size(info['total_size'])
            size = tools.format_size(info['size'])
            if info['status'] == '完成':
                self.task_info[title]['size_ratio'] = str(total_size)
            else:
                self.task_info[title]['size_ratio'] = f"{size}/{total_size}"
        return self.task_info

    def remove_task(self, title):
        '''
        删除任务信息
        :param title:
        :return:
        '''
        self.task_info.pop(title)


def main():
    Bili = Bilibili()
    while True:
        url = input("请输入视频url：")
        audio_url, video_url, title = Bili.get_video(url)
        if not Bili.request_video(audio_url, video_url, title):
            print("视频请求失败！")
        if not Bili.merge_video(title):
            print("视频合并失败！")


if __name__ == '__main__':
    main()
