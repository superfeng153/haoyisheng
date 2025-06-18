import requests
import time
import random
import json
from typing import Dict

class ProgressReporter:
    """
    用于上报视频学习进度的类。
    """
    def __init__(self, 
                 login_name: str, 
                 course_id: str, 
                 ware_id: str, 
                 playlog_userid: str, 
                 playlog_videoid: str, 
                 playlog_upid: str,
                 video_duration_ms: int, 
                 ts_url: str, 
                 ts_key: str, 
                 ts_t: str, 
                 client_uuid: str, 
                 client_cdn: str, 
                 cookies: Dict[str, str], 
                 user_agent: str):
        """
        初始化 ProgressReporter.

        Args:
            login_name (str): 登录名/手机号.
            course_id (str): 课程 ID.
            ware_id (str): 课件 ID.
            playlog_userid (str): playlog 中的用户 ID.
            playlog_videoid (str): playlog 中的视频 ID.
            playlog_upid (str): playlog 中的 upid.
            video_duration_ms (int): 视频总时长 (毫秒).
            ts_url (str): .ts 视频切片的基础 URL.
            ts_key (str): .ts 请求的 key.
            ts_t (str): .ts 请求的 t (时间戳或令牌).
            client_uuid (str): client 心跳请求的 uuid.
            client_cdn (str): client 心跳请求的 cdn.
            cookies (Dict[str, str]): 用于请求的 cookies.
            user_agent (str): User-Agent 请求头.
        """
        self.login_name = login_name
        self.course_id = course_id
        self.ware_id = ware_id
        self.playlog_userid = playlog_userid
        self.playlog_videoid = playlog_videoid
        self.playlog_upid = playlog_upid
        self.video_duration_ms = video_duration_ms
        self.ts_url = ts_url
        self.ts_key = ts_key
        self.ts_t = ts_t
        self.client_uuid = client_uuid
        self.client_cdn = client_cdn
        self.cookies = cookies
        self.user_agent = user_agent

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
        })
        requests.utils.add_dict_to_cookiejar(self.session.cookies, self.cookies)
        
    def _send_ccstate(self):
        """发送 ccstate.jsp 请求以保持会话."""
        url = "https://www.cmechina.net/webcam/ccstate.jsp"
        params = {
            'loginName': self.login_name,
            'course_id': self.course_id,
            'ware_id': self.ware_id,
            'expiresTime': 10,
            't': int(time.time() * 1000)
        }
        headers = {
            "Referer": f"https://www.cmechina.net/cme/study2.jsp?course_id={self.course_id}&courseware_id={self.ware_id}",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"[{time.strftime('%H:%M:%S')}] Sent ccstate request successfully.")
        except requests.RequestException as e:
            print(f"Error sending ccstate request: {e}")

    def _send_playlog(self, play_position: int):
        """发送 playlog 请求以上报播放进度."""
        url = "https://m-flare.bokecc.com/flash/playlog"
        params = {
            'stage': 77,
            'upid': self.playlog_upid,
            'userid': self.playlog_userid,
            'videoid': self.playlog_videoid,
            'play_position': play_position,
            'video_duration': self.video_duration_ms,
            'time': int(time.time() * 1000),
            'random': random.randint(1000000, 9999999),
            'terminal_type': 40,
            'player_status': 1,
            'play_speed': 1,
            'custom_id': ''
        }
        headers = {
            "Referer": "https://www.cmechina.net/",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
        }
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"[{time.strftime('%H:%M:%S')}] Sent playlog request, progress: {play_position / 1000}s.")
        except requests.RequestException as e:
            print(f"Error sending playlog request: {e}")

    def _send_ts(self, video_param: int):
        """发送 .ts 视频切片请求 (不下载内容)."""
        params = {
            'video': video_param,
            'key': self.ts_key,
            't': self.ts_t,
            'tpl': 10,
            'tpt': 112,
        }
        headers = {
            "Origin": "https://www.cmechina.net",
            "Referer": "https://www.cmechina.net/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }
        try:
            # 使用 stream=True, 并且不读取 response.content, 以避免下载
            response = self.session.get(self.ts_url, params=params, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            print(f"[{time.strftime('%H:%M:%S')}] Sent .ts request (video={video_param}) successfully.")
        except requests.RequestException as e:
            print(f"Error sending .ts request: {e}")
        finally:
            if 'response' in locals() and response:
                response.close()

    def _send_client_heartbeat(self, num_param: int):
        """发送 client 心跳事件."""
        url = "https://logger.csslcloud.net/event/vod/v1/client"
        data = {
            "ua": self.user_agent,
            "platform": "h5-pc",
            "uuid": self.client_uuid,
            "rid": int(time.time() * 1000),
            "ver": "v1.0.7",
            "appver": "3.5.14",
            "business": "1001",
            "userid": "",
            "appid": self.playlog_userid, # appid 与 playlog_userid 相同
            "event": "heartbeat",
            "vid": self.playlog_videoid, # vid 与 playlog_videoid 相同
            "retry": 0,
            "code": 200,
            "cdn": self.client_cdn,
            "heartinter": 60,
            "num": num_param,
            "playerstatus": 1,
            "blocktimes": 0,
            "blockduration": 0
        }
        headers = {
            "Origin": "https://www.cmechina.net",
            "Referer": "https://www.cmechina.net/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            # Body 是 urlencoded 的 JSON 字符串
            response = self.session.post(url, data=json.dumps(data), headers=headers, timeout=10)
            response.raise_for_status()
            print(f"[{time.strftime('%H:%M:%S')}] Sent client heartbeat (num={num_param}) successfully.")
        except requests.RequestException as e:
            print(f"Error sending client heartbeat: {e}")

    def report(self, start_play_position: int = 20397, start_ts_video_param: int = 57, progress_interval_s: int = 10):
        """
        开始上报学习进度.

        Args:
            start_play_position (int): 起始播放位置 (毫秒).
            start_ts_video_param (int): 起始的 .ts video 参数.
            progress_interval_s (int): 每次上报进度的间隔时间 (秒).
        """
        current_play_position = start_play_position
        current_ts_video_param = start_ts_video_param
        loop_count = 0
        client_heartbeat_num = 10 # 初始值从抓包文件获取

        print(f"Starting progress reporting for course {self.course_id}...")
        print(f"Video duration: {self.video_duration_ms / 1000}s")

        while current_play_position < self.video_duration_ms:
            loop_count += 1
            print(f"\n--- Loop {loop_count} ---")

            if loop_count > 0 and loop_count % 6 == 0:
                self._send_client_heartbeat(client_heartbeat_num)
                client_heartbeat_num += 1

            self._send_ccstate()
            time.sleep(random.uniform(0.5, 1.5))
            
            self._send_playlog(current_play_position)
            time.sleep(random.uniform(0.5, 1.5))

            self._send_ts(current_ts_video_param)

            # 更新下一次循环的参数
            increment = progress_interval_s * 1000 + random.randint(-200, 200)
            current_play_position += increment
            current_ts_video_param += 5
            
            if current_play_position < self.video_duration_ms:
                print(f"Waiting for {progress_interval_s} seconds before next report...")
                time.sleep(progress_interval_s)

        print("\nVideo finished. Reporting completed.")
