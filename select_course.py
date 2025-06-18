import requests # 引入requests库
from bs4 import BeautifulSoup # 引入BeautifulSoup用于HTML解析
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 预期的报告参数结构示例:
# {
#     "course_id": "课程ID",
#     "ware_id": "课件ID",
#     "playlog_userid": "播放日志用户ID",
#     "playlog_videoid": "播放日志视频ID",
#     "playlog_upid": "播放日志UPID",
#     "video_duration_ms": 1234567, # 视频总时长 (毫秒)
#     "ts_url": "TS切片基础URL",
#     "ts_key": "TS请求KEY",
#     "ts_t": "TS请求T参数",
#     "client_uuid": "客户端心跳UUID",
#     "client_cdn": "客户端心跳CDN"
# }

def get_primary_projects(cookies):
    """
    通过requests发送请求，解析HTML，获取所有一级项目列表。
    """
    logging.info("正在解析一级项目列表...")
    professional_projects = []
    public_projects = []

    url = "https://www.cmechina.net/cme/index.jsp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Referer": "https://www.cmechina.net/pub/tongzhi.jsp",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status() # 检查HTTP请求是否成功

        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找专业课程的项目名称和ID
        # 适配BeautifulSoup的CSS选择器
        professional_elements = soup.select('ul.xk_box:not([style*="z-index: 50;"]) > li.xk_list > .xk_a > a')
        for element in professional_elements:
            onclick_attr = element.get('onclick')
            if onclick_attr and onclick_attr.startswith("xkdhJumpTo("):
                parts = onclick_attr.split(",")
                project_id = parts[0].split("(")[1].strip("'")
                project_name = parts[1].strip().strip("'")
                professional_projects.append({"id": project_id, "name": project_name})
        logging.info(f"解析到 {len(professional_projects)} 个专业一级项目。")

        # 查找公共课程的项目名称和ID
        # 适配BeautifulSoup的CSS选择器
        public_elements = soup.select('ul.xk_box[style*="z-index: 50;"] > li.xk_list > .xk_a > a')
        for element in public_elements:
            onclick_attr = element.get('onclick')
            if onclick_attr and onclick_attr.startswith("xkdhJumpTo("):
                parts = onclick_attr.split(",")
                project_id = parts[0].split("(")[1].strip("'")
                project_name = parts[1].strip().strip("'")
                public_projects.append({"id": project_id, "name": project_name})
        logging.info(f"解析到 {len(public_projects)} 个公共一级项目。")

    except requests.exceptions.RequestException as e:
        logging.error(f"请求项目列表失败: {e}")
    except Exception as e:
        logging.error(f"解析项目列表失败: {e}")
    return {"professional": professional_projects, "public": public_projects}

def get_course_details_by_project_id(project_id, cookies):
    """
    通过requests发送请求，解析HTML，获取指定项目ID的所有详细课程列表。
    """
    logging.info(f"正在获取项目 {project_id} 的详细课程列表...")
    courses = []

    url = f"https://www.cmechina.net/cme/subject.jsp?subjectId={project_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.cmechina.net/pub/tongzhi.jsp",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status() # 检查HTTP请求是否成功

        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找所有课程的li元素
        course_elements = soup.select('li.pic_list')
        for element in course_elements:
            # 从a标签的onclick属性中提取信息
            a_tag = element.select_one('a.img')
            if a_tag:
                onclick_attr = a_tag.get('onclick')
                if onclick_attr and onclick_attr.startswith("xkyJumpTo("):
                    parts = onclick_attr.split(',')
                    course_id = parts[0].split("('")[1].strip("'")
                    course_name = parts[1].strip().strip("'")
                    course_score = float(parts[3].strip().strip("'")) # 将分数转换为浮点数
                    courses.append({'id': course_id, 'name': course_name, 'score': course_score})
        logging.info(f"解析到 {len(courses)} 个课程。")

    except requests.exceptions.RequestException as e:
        logging.error(f"请求课程列表失败: {e}")
    except Exception as e:
        logging.error(f"解析课程列表失败: {e}")
    return courses

def match_courses_by_score(professional_courses, public_courses, required_score):
    """
    根据需求分数匹配课程，优先选择专业课程，不足时从公共课程补充，确保总分数完全一致。
    这是一个NP完全问题（子集和问题），简单贪婪算法不一定能找到精确解。
    这里将尝试一个回溯算法来寻找精确解。
    """
    logging.info(f"正在匹配课程，需求分数: {required_score}")
    matched_courses = []
    current_score = 0.0

    all_courses = []
    # 优先添加专业课程
    for course in professional_courses:
        all_courses.append((course['score'], course, "professional"))
    # 后添加公共课程
    for course in public_courses:
        all_courses.append((course['score'], course, "public"))

    # 对课程按分数从高到低排序，这有助于剪枝，但不是解决NP问题的关键。
    # 为了优先级匹配原则，我们已经分开了专业和公共，并在all_courses中优先放置专业课。
    # 进一步，可以在各自类别内按分数排序，但这里为了保持原始顺序，暂时不进行额外排序。

    def find_exact_match(index, current_sum, current_selection):
        nonlocal matched_courses # 允许修改外部作用域的matched_courses
        if current_sum == required_score:
            matched_courses = list(current_selection)
            return True
        if current_sum > required_score or index == len(all_courses):
            return False

        score, course, course_type = all_courses[index]

        # 包含当前课程
        current_selection.append(course)
        if find_exact_match(index + 1, current_sum + score, current_selection):
            return True
        current_selection.pop() # 回溯

        # 不包含当前课程
        if find_exact_match(index + 1, current_sum, current_selection):
            return True

        return False

    if not find_exact_match(0, 0.0, []):
        logging.warning("未能找到完全匹配需求分数的课程组合。")

    return matched_courses

def get_reporting_parameters(course_id, cookies):
    # 功能: 获取指定课程ID用于上报进度的所有必需参数。
    # 注意: 此函数的实现依赖于对目标网站网络请求的分析。
    # 以下URL、参数提取逻辑均为占位符，需要根据实际分析结果进行替换。

    logging.info(f"正在为课程 {course_id} 获取上报参数...")
    reporting_params = {
        "course_id": course_id,
        "ware_id": None,
        "playlog_userid": None,
        "playlog_videoid": None,
        "playlog_upid": None,
        "video_duration_ms": None,
        "ts_url": None,
        "ts_key": None,
        "ts_t": None,
        "client_uuid": None,
        "client_cdn": None
    }

    # === 占位符逻辑开始 ===
    # 假设需要访问一个课程详情页来获取参数
    # course_video_page_url = f"https://www.cmechina.net/cme/study2.jsp?course_id={course_id}&courseware_id=SOME_WARE_ID" # WARE_ID可能也需要先获取
    # headers = { ... } # 根据需要设置请求头
    # try:
    #     response = requests.get(course_video_page_url, headers=headers, cookies=cookies)
    #     response.raise_for_status()
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #
    #     # 示例: 从HTML中提取参数 (具体选择器和逻辑需要实际分析)
    #     # reporting_params["ware_id"] = soup.select_one("#wareIdInput")["value"]
    #     # reporting_params["playlog_userid"] = # ... 从JS变量或HTML元素中提取
    #     # reporting_params["video_duration_ms"] = # ...
    #     # ... 其他参数类似
    #
    #     # 如果参数来自某个API调用:
    #     # params_api_url = "https://www.cmechina.net/api/getCourseVideoParams"
    #     # api_response = requests.post(params_api_url, data={"course_id": course_id}, cookies=cookies)
    #     # api_data = api_response.json()
    #     # reporting_params.update(api_data) # 假设API返回了所需参数
    #
    #     logging.info(f"成功获取课程 {course_id} 的部分或全部上报参数。") # 根据实际情况调整日志
    #
    # except requests.exceptions.RequestException as e:
    #     logging.error(f"请求课程 {course_id} 的视频页面或参数API失败: {e}")
    # except Exception as e:
    #     logging.error(f"解析课程 {course_id} 的上报参数失败: {e}")
    # === 占位符逻辑结束 ===

    # 临时硬编码/模拟数据 - BEGIN
    # **重要提示**: 以下是用于演示目的的模拟数据。
    # 在实际应用中，必须替换为从网站动态获取参数的真实逻辑。
    if course_id: # 确保 course_id 存在才填充模拟数据
        logging.warning(f"课程 {course_id} 的上报参数使用的是模拟数据，请替换为真实获取逻辑！")
        reporting_params.update({
            "ware_id": f"sim_ware_{course_id}",
            "playlog_userid": "sim_user_123",
            "playlog_videoid": f"sim_video_{course_id}",
            "playlog_upid": f"sim_upid_{course_id}",
            "video_duration_ms": 3600 * 1000, # 假设1小时
            "ts_url": "https://example.com/sim_ts_url",
            "ts_key": "sim_ts_key",
            "ts_t": "sim_ts_t_token",
            "client_uuid": "sim_client_uuid_abcdef",
            "client_cdn": "sim_cdn_provider"
        })
    else:
        logging.error("获取上报参数时 course_id 为空。")
    # 临时硬编码/模拟数据 - END

    # 检查是否所有参数都已获取 (可选的验证步骤)
    # all_params_found = all(value is not None for key, value in reporting_params.items() if key != "course_id") # course_id 总是存在
    # if not all_params_found:
    #    logging.warning(f"未能获取课程 {course_id} 的全部上报参数: {reporting_params}")

    return reporting_params

# 新增: 主函数封装选课和参数获取逻辑
def select_and_prepare_courses(cookies, required_score_professional, required_score_public):
    logging.info("开始执行选课和参数准备流程...")

    projects_data = get_primary_projects(cookies)
    professional_projects = projects_data.get("professional", [])
    public_projects = projects_data.get("public", [])

    all_professional_courses = []
    for project in professional_projects:
        logging.info(f"正在获取专业项目 '{project['name']}' (ID: {project['id']}) 的课程...")
        all_professional_courses.extend(get_course_details_by_project_id(project['id'], cookies))

    all_public_courses = []
    for project in public_projects:
        logging.info(f"正在获取公共项目 '{project['name']}' (ID: {project['id']}) 的课程...")
        all_public_courses.extend(get_course_details_by_project_id(project['id'], cookies))

    logging.info(f"总共获取到 {len(all_professional_courses)}门专业课程 和 {len(all_public_courses)}门公共课程。")

    # 匹配专业课程
    # 注意: match_courses_by_score 的逻辑是寻找精确匹配，如果找不到会返回空列表。
    # 实际应用中可能需要调整此逻辑，例如允许近似匹配或选择多个小课程组合。
    selected_professional_courses = []
    if required_score_professional > 0 and all_professional_courses:
        logging.info(f"开始为专业课程匹配 {required_score_professional}学分...")
        selected_professional_courses = match_courses_by_score(all_professional_courses, [], required_score_professional)
        if selected_professional_courses:
            logging.info(f"成功匹配到 {len(selected_professional_courses)} 门专业课程，总学分基本满足要求。")
        else:
            logging.warning(f"未能为专业课程精确匹配到 {required_score_professional} 学分。")

    # 匹配公共课程
    selected_public_courses = []
    if required_score_public > 0 and all_public_courses:
        logging.info(f"开始为公共课程匹配 {required_score_public}学分...")
        selected_public_courses = match_courses_by_score([], all_public_courses, required_score_public) # 注意参数顺序
        if selected_public_courses:
            logging.info(f"成功匹配到 {len(selected_public_courses)} 门公共课程，总学分基本满足要求。")
        else:
            logging.warning(f"未能为公共课程精确匹配到 {required_score_public} 学分。")

    final_selected_courses_with_params = []

    courses_to_process = selected_professional_courses + selected_public_courses

    if not courses_to_process:
        logging.warning("没有匹配到任何课程，无法进行参数获取。")
        return []

    logging.info(f"总共匹配到 {len(courses_to_process)} 门课程，将开始获取上报参数。")

    for course in courses_to_process:
        logging.info(f"准备为课程 '{course['name']}' (ID: {course['id']}) 获取上报参数。")
        # 假设 'cookies' 变量在当前作用域可用
        report_params = get_reporting_parameters(course['id'], cookies)
        if all(report_params.get(k) is not None for k in ["ware_id", "playlog_videoid"]): # 简单检查关键参数是否存在
            final_selected_courses_with_params.append({
                "course_details": course,
                "reporting_parameters": report_params
            })
            logging.info(f"已为课程 '{course['name']}' 添加上报参数。")
        else:
            logging.warning(f"未能获取课程 '{course['name']}' (ID: {course['id']}) 的完整上报参数，跳过此课程。")

    logging.info(f"完成参数准备，共计 {len(final_selected_courses_with_params)} 门课程已准备好上报。")
    return final_selected_courses_with_params

# 示例: 如何在 __main__ 中调用
if __name__ == "__main__":
    # 配置日志 (确保在文件顶部或此处配置一次)
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 模拟cookies - 实际应用中需要从登录模块获取
    mock_cookies = {"SESSION": "mock_session_id_for_testing_12345"}
    logging.info("模拟运行选课流程...")

    # 从用户或配置文件获取所需学分
    # 这里使用固定值作为示例
    target_professional_score = 10.0
    target_public_score = 5.0
    logging.info(f"目标学分: 专业课 {target_professional_score}, 公共课 {target_public_score}")

    prepared_courses = select_and_prepare_courses(mock_cookies, target_professional_score, target_public_score)

    if prepared_courses:
        logging.info("最终选定的课程及上报参数：")
        for item in prepared_courses:
            logging.info(f"  课程: {item['course_details']['name']}, 学分: {item['course_details']['score']}")
            logging.info(f"  上报参数: {item['reporting_parameters']}")
    else:
        logging.info("未能选定并准备任何课程。")
