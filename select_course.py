import requests # 引入requests库
from bs4 import BeautifulSoup # 引入BeautifulSoup用于HTML解析
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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