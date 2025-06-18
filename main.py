import logging
import json # For loading cookies if login module doesn't return them directly
import time # For potential retries with delay

# Import functions/classes from other project files
# Assuming they are in the same directory or Python path
from login_haoyisheng import login # Assuming login_haoyisheng.py has a 'login' function that returns cookies
from select_course import select_and_prepare_courses
from report_progress import ProgressReporter
from test_reporter import load_cookies_from_file # Re-using cookie loading for now

# Configure logging in Chinese
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main_orchestrator():
    logging.info("开始执行自动学课主流程...")

    # 1. 用户登录并获取Cookies
    user_cookies = None
    user_info = None # To store username for login_name parameter

    try:
        # Option A: If login_haoyisheng.login() handles everything and returns cookies & user info
        # logging.info("尝试通过 login_haoyisheng.py 登录...")
        # success, message, cookies_data, user_data = login() # Modify 'login' to return these
        # if success:
        #     user_cookies = cookies_data
        #     user_info = user_data # e.g., {"username": "13800138000"}
        #     logging.info(f"登录成功。用户: {user_info.get('username', 'N/A')}, 获取到Cookies。")
        # else:
        #     logging.error(f"登录失败: {message}")
        #     return

        # Option B: For now, reuse load_cookies_from_file from test_reporter.py
        # This assumes '测试用户信息.json' is populated by running login_haoyisheng.py separately.
        logging.info("尝试从 '测试用户信息.json' 加载 Cookies 和用户信息...")
        user_cookies = load_cookies_from_file("测试用户信息.json") # Path to user info file
        if user_cookies:
            logging.info("成功从文件加载 Cookies。")
            try:
                with open("测试用户信息.json", 'r', encoding='utf-8') as f:
                    user_data_from_file = json.load(f)
                    user_info = {"username": user_data_from_file.get("username")} # Adapt based on actual key in JSON
                    logging.info(f"成功从文件加载用户信息: {user_info}")
            except Exception as e:
                logging.warning(f"无法从 '测试用户信息.json' 加载详细用户信息 (如手机号): {e}")
                user_info = {"username": "13800138000"} # Fallback
                logging.warning(f"将使用备用手机号: {user_info['username']}")
        else:
            logging.error("未能加载用户Cookies，主流程中止。")
            return

    except ImportError:
        logging.error("错误: 无法导入 'login_haoyisheng.py'。请确保该文件存在且包含 'login' 函数。")
        logging.info("将尝试从 '测试用户信息.json' 加载 Cookies 作为备选方案。")
        user_cookies = load_cookies_from_file("测试用户信息.json")
        if not user_cookies:
            logging.error("备选方案加载Cookies失败，主流程中止。")
            return
        logging.info("备选方案：成功从文件加载 Cookies。")
        user_info = {"username": "13800138000"} # Fallback
        logging.warning(f"将使用备用手机号: {user_info['username']}")


    # 2. 选课并获取上报参数
    # 定义所需学分 (这些可以来自配置文件或用户输入)
    required_professional_score = 1.0 # 示例：需要1学分专业课
    required_public_score = 0.5       # 示例：需要0.5学分公共课
    logging.info(f"课程需求: 专业课 {required_professional_score} 学分, 公共课 {required_public_score} 学分。")

    prepared_courses = []
    try:
        prepared_courses = select_and_prepare_courses(user_cookies, required_professional_score, required_public_score)
    except Exception as e:
        logging.error(f"执行选课和参数准备时发生严重错误: {e}", exc_info=True)
        return

    if not prepared_courses:
        logging.warning("未能选择或准备任何课程进行学习。流程结束。")
        return

    logging.info(f"成功选择并准备了 {len(prepared_courses)} 门课程。")

    # 3. 遍历选定的课程并上报进度
    for course_item in prepared_courses:
        course_details = course_item.get("course_details", {})
        report_params = course_item.get("reporting_parameters", {})

        if not course_details or not report_params:
            logging.warning("发现一个课程条目缺少课程详情或上报参数，已跳过。")
            continue

        logging.info(f"开始处理课程: '{course_details.get('name', '未知课程')}' (ID: {course_details.get('id', '未知ID')})")

        # 从 report_params 或 user_info 中获取 ProgressReporter 所需参数
        # 注意: select_course.py 中的 get_reporting_parameters 已经填充了大部分参数 (目前是模拟数据)
        # login_name 和 user_agent 可能需要特别处理

        login_name = user_info.get("username") if user_info else None
        if not login_name:
            login_name = "13800138000" # Fallback
            logging.warning(f"无法从用户信息获取 login_name 或用户信息不存在，将使用备用手机号: {login_name}")

        if report_params.get("login_name"): # 如果get_reporting_parameters能提供
            login_name = report_params["login_name"]

        user_agent = report_params.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        if not report_params.get("user_agent"): # 如果 select_course 未提供
            logging.warning(f"课程 '{course_details.get('name')}' 的上报参数中缺少 user_agent, 将使用默认值。")


        try:
            reporter = ProgressReporter(
                login_name=login_name,
                course_id=report_params["course_id"], # Should be same as course_details.get('id')
                ware_id=report_params["ware_id"],
                playlog_userid=report_params["playlog_userid"],
                playlog_videoid=report_params["playlog_videoid"],
                playlog_upid=report_params["playlog_upid"],
                video_duration_ms=report_params["video_duration_ms"],
                ts_url=report_params["ts_url"],
                ts_key=report_params["ts_key"],
                ts_t=report_params["ts_t"],
                client_uuid=report_params["client_uuid"],
                client_cdn=report_params["client_cdn"],
                cookies=user_cookies,
                user_agent=user_agent
            )
            logging.info(f"课程 '{course_details.get('name')}' 的 ProgressReporter 实例化成功。")

            # 调用 report() 方法开始上报
            # 实际运行时可能不需要修改这里的参数，除非有特殊测试需求
            reporter.report(
                start_play_position=report_params.get("start_play_position", 0), # 允许从参数中指定起始点
                start_ts_video_param=report_params.get("start_ts_video_param", 1),
                progress_interval_s=report_params.get("progress_interval_s", 10) # 上报间隔
            )
            logging.info(f"课程 '{course_details.get('name')}' 的进度上报完成。")

        except KeyError as e:
            logging.error(f"为课程 '{course_details.get('name')}' 实例化 ProgressReporter 失败: 缺少参数 {e}。上报参数详情: {report_params}", exc_info=True)
        except Exception as e:
            logging.error(f"处理课程 '{course_details.get('name')}' 时发生错误: {e}", exc_info=True)

        logging.info(f"完成课程 '{course_details.get('name')}' 的处理。")

    logging.info("所有选定课程处理完毕。自动学课主流程结束。")

if __name__ == "__main__":
    # 这是一个示例，如何处理 login_haoyisheng.py 可能引发的验证码问题
    # max_login_attempts = 3
    # for attempt in range(max_login_attempts):
    #     try:
    #         main_orchestrator()
    #         break # 成功则退出循环
    #     except Exception as e: #  假设login() 或其他部分可能抛出特定异常如 CaptchaError
    #         # 这里的异常检查非常基础，实际应用中可能需要更精确的异常类型
    #         if "CaptchaError" in str(type(e)) or "CaptchaRequired" in str(e):
    #             logging.error(f"登录尝试 {attempt + 1} 失败: 验证码错误或需要手动干预。错误: {e}")
    #             if attempt < max_login_attempts - 1:
    #                 logging.info("等待一段时间后重试...")
    #                 time.sleep(60) # 等待1分钟
    #             else:
    #                 logging.error("已达到最大登录尝试次数，程序终止。")
    #         else:
    #             logging.error(f"发生未处理的错误: {e}", exc_info=True)
    #             break # 其他错误则不重试
    main_orchestrator()
