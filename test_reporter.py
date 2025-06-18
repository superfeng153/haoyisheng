import time
import json
import logging
from report_progress import ProgressReporter # 假设 report_progress.py 在同一目录下或在PYTHONPATH中

# 配置日志记录，确保日志为中文
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_cookies_from_file(filepath="测试用户信息.json"):
    """
    从JSON文件加载Cookies。
    确保 '测试用户信息.json' 文件存在且包含有效的Cookie信息。
    示例格式: {"cookies": {"SESSION": "xxxx", "other_cookie": "yyyy"}}
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 查找包含 "cookie" 或 "cookies" 键的字典
            if "cookies" in data:
                return data["cookies"]
            elif "cookie" in data: # 兼容单数形式
                 return data["cookie"]
            # 如果顶层就是cookies字典
            elif all(isinstance(v, str) for v in data.values()):
                 return data
            else:
                logging.error(f"无法在 {filepath} 中找到 'cookies' 键或有效的cookie格式。")
                return None
    except FileNotFoundError:
        logging.error(f"Cookie文件 {filepath} 未找到。")
        return None
    except json.JSONDecodeError:
        logging.error(f"解析Cookie文件 {filepath} 失败，请检查JSON格式。")
        return None
    except Exception as e:
        logging.error(f"加载Cookie时发生未知错误: {e}")
        return None

def main():
    logging.info("开始测试 ProgressReporter...")

    # 1. 加载用户Cookies
    # 假设 login_haoyisheng.py 已经执行并将cookies存入 '测试用户信息.json'
    # 或者可以直接在此处硬编码cookies用于测试
    user_cookies = load_cookies_from_file()

    if not user_cookies:
        logging.error("未能加载用户Cookies，测试中止。")
        # 备选：使用模拟/占位Cookie进行测试
        # user_cookies = {"SESSION": "placeholder_session_for_testing"}
        # logging.warning("使用占位Cookie进行测试。")
        return

    logging.info(f"成功加载Cookies: {user_cookies}")

    # 2. 定义 ProgressReporter 所需的测试参数
    # 这些参数通常由 select_course.py 中的 get_reporting_parameters 函数获取
    # 此处使用手动定义的模拟数据进行测试
    # **重要**: 这些值需要尽可能接近真实场景的值才能有效测试
    test_report_params = {
        "login_name": "用户的登录名或手机号", # 例如从 `测试用户信息.json` 获取或硬编码
        "course_id": "test_course_001",
        "ware_id": "test_ware_001",
        "playlog_userid": "user_test_12345",
        "playlog_videoid": "video_test_67890",
        "playlog_upid": "upid_test_abcde",
        "video_duration_ms": 1800 * 1000,  # 假设视频时长30分钟 (毫秒)
        "ts_url": "https://video.example.com/path/to/segments.ts", # 真实的 .ts URL 前缀
        "ts_key": "example_ts_key_string",  # 真实的 ts_key
        "ts_t": "example_ts_t_timestamp_or_token", # 真实的 ts_t
        "client_uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef", # 真实的 client_uuid
        "client_cdn": "cdn.example.com", # 真实的 client_cdn
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36" # 一个典型的 User-Agent
    }
    logging.info(f"使用以下测试参数初始化 ProgressReporter: {test_report_params}")

    # 从测试用户信息文件中读取 loginName (手机号)
    try:
        with open("测试用户信息.json", 'r', encoding='utf-8') as f:
            user_info = json.load(f)
            if "username" in user_info: # 假设 'username' 字段存的是手机号
                 test_report_params["login_name"] = user_info["username"]
                 logging.info(f"从测试用户信息中获取到 login_name: {user_info['username']}")
            else:
                 logging.warning("测试用户信息中未找到 'username' 作为 login_name, 将使用占位符。")
                 test_report_params["login_name"] = "13800138000" # 占位符
    except FileNotFoundError:
        logging.warning("'测试用户信息.json' 未找到, login_name 将使用占位符。")
        test_report_params["login_name"] = "13800138000" # 占位符
    except Exception as e:
        logging.error(f"读取测试用户信息时出错: {e}, login_name 将使用占位符。")
        test_report_params["login_name"] = "13800138000" # 占位符


    # 3. 实例化 ProgressReporter
    try:
        reporter = ProgressReporter(
            login_name=test_report_params["login_name"],
            course_id=test_report_params["course_id"],
            ware_id=test_report_params["ware_id"],
            playlog_userid=test_report_params["playlog_userid"],
            playlog_videoid=test_report_params["playlog_videoid"],
            playlog_upid=test_report_params["playlog_upid"],
            video_duration_ms=test_report_params["video_duration_ms"],
            ts_url=test_report_params["ts_url"],
            ts_key=test_report_params["ts_key"],
            ts_t=test_report_params["ts_t"],
            client_uuid=test_report_params["client_uuid"],
            client_cdn=test_report_params["client_cdn"],
            cookies=user_cookies,
            user_agent=test_report_params["user_agent"]
        )
        logging.info("ProgressReporter 实例化成功。")
    except Exception as e:
        logging.error(f"ProgressReporter 实例化失败: {e}")
        return

    # 4. 调用 report() 方法开始上报进度
    # 可以调整 start_play_position, start_ts_video_param, progress_interval_s 进行测试
    try:
        logging.info("开始调用 reporter.report() 方法...")
        # 为了快速测试，可以将 video_duration_ms 设置得较小，或只执行几次循环
        # 例如，这里设置一个较短的 progress_interval_s 和较小的 start_play_position
        # 并且在 report_progress.py 中可能需要临时修改循环条件或次数以避免长时间运行
        reporter.report(
            start_play_position=0,      # 从视频开始处上报
            start_ts_video_param=1,     # .ts video 参数起始值
            progress_interval_s=5      # 每5秒上报一次 (用于测试)
        )
        logging.info("reporter.report() 方法执行完毕。")
    except Exception as e:
        logging.error(f"执行 reporter.report() 方法时发生错误: {e}")

if __name__ == "__main__":
    main()
