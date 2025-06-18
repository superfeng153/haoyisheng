# 自动学课需求 (Crawl4AI 终版)

## 引言

本文档基于 `Crawl4AI` 框架，为自动化学习脚本提供最终的设计与开发蓝图。通过全面利用 `Crawl4AI` 的高级功能，本方案将开发重心从复杂的底层交互模拟，聚焦到核心业务逻辑的实现上，旨在最大化开发效率与项目健壮性。

## 一、核心功能需求

*   **用户输入:** 支持账号、密码、人员类别和目标学分的自动提取登录。
*   **课程匹配:** 根据抓取到的课程信息（名称、学分、ID等），通过匹配算法（优先专业课，公共课补齐）精确组合出满足目标学分的课程列表。

## 二、技术实现：Crawl4AI 一站式解决方案

放弃原有多库协作的复杂模式，全面采用 `Crawl4AI` 作为统一的浏览器自动化与数据提取引擎。

### 2.1 统一的采集与交互引擎

*   **登录与会话持久化:**
    *   **首次登录:** 通过 `Crawl4AI` 访问登录页面后，利用 `js_code` 参数执行JavaScript，精确地向账号、密码输入框填充值。对于验证码，可以通过 `Crawl4AI` 捕获验证码图片（例如，通过 `screenshot` 参数针对特定元素截图，或通过 `js_code` 获取图片 `base64`），然后结合 `dddocr` 库进行识别。将识别结果同样通过 `js_code` 填入验证码输入框，并模拟点击登录按钮。整个过程应配合 `wait_for` 参数，确保页面元素（如验证码图片、登录按钮）加载完成和登录成功后的跳转信号。
    *   **会话保存:** 在 `CrawlerRunConfig` 中指定 `storage_state="my_session.json"`，`Crawl4AI` 会自动保存登录后的所有会话信息（Cookies, Local Storage 等）。
    *   **自动续期:** 后续运行脚本时，`Crawl4AI` 会自动加载 `my_session.json` 文件，实现长期有效的免密登录。

*   **动态内容处理 (翻页/懒加载):**
    *   使用 `js_code` 参数执行点击"下一页"或页面滚动的 JavaScript。
    *   配合 `wait_for` 参数，等待新课程列表加载完成的明确信号（如特定DOM元素出现或某个JS变量状态改变），确保数据完整性。
    *   利用 `session_id` 在连续的翻页操作中复用同一个浏览器标签页，提高效率。

*   **内容预过滤 (重要优化):**
    *   在抓取课程列表页时，在 `CrawlerRunConfig` 中配置 `css_selector`，直接指定课程列表所在的容器ID或类。例如：`css_selector="#courseListPanel"`。这使得 `Crawl4AI` 在提取前就过滤掉所有无关内容（如导航栏、页脚），极大地提升了后续提取的准确性和效率。

*   **课程学习模拟:**
    *   直接使用 `Crawl4AI` 访问课程学习页面。通过执行页面自身的 JavaScript 函数（如 `startStudy()`, `reportProgress()`）或模拟点击相关按钮，来完成学习过程。这从根本上规避了所有关于请求签名、参数加密的反爬措施。
    *   **并发学习优化:** 对于已选定的多门课程，可利用 `crawler.arun_many` 配合 `SemaphoreDispatcher` 实现并发学习，显著缩短挂课总时长。

*   **自适应学习策略 (核心):**
    *   **动机:** 考虑到学习系统可能存在未知的并发或请求频率限制，采用一种动态的、自我优化的策略来寻找最快的稳定学习模式。
    *   **可配置的学习参数:** 在 `config.py` 中定义学习并发数（`CONCURRENCY_LEVEL`）、基础进度上报间隔（`BASE_REPORT_INTERVAL`）等核心参数，避免硬编码。
    *   **智能探索与反馈循环:**
        *   **启动:** 从一个保守的配置开始（例如：`CONCURRENCY_LEVEL = 1`，上报间隔较长）。
        *   **试探性加速:** 在连续多次学习/上报操作成功后（通过检查 `CrawlResult.success` 和页面反馈确认），脚本可以尝试逐步提高效率，例如：轻微缩短上报间隔或在 `SemaphoreDispatcher` 中增加并发数。
        *   **熔断与回退:** 一旦检测到失败（例如 `CrawlResult.success` 为 `False`，或服务器返回错误信息），脚本应立即"熔断"，自动回退到上一个已知的稳定配置，并将导致失败的激进配置（如过高的并发数、过短的间隔）记录下来，在本次运行中不再尝试。
    *   **最终目标:** 通过这种"试探-反馈-调整"的闭环机制，脚本能够在每次运行时，根据服务器的实时状况，自动"调优"至当前环境所能允许的最优学习效率。

### 2.2 智能化的数据提取

*   **方案A (首选): `JsonCssExtractionStrategy`**
    *   为课程列表页定义一个JSON配置，清晰描述课程列表的容器选择器 (`baseSelector`) 及各字段（名称、学分、ID）的相对选择器和提取类型（文本或属性）。这是最高效、最稳定的提取方式。

*   **方案B (备选): `LLMExtractionStrategy`**
    *   当页面结构极其不规则时，可使用此方案。通过自然语言指令和Pydantic模型定义，让大模型自动提取所需数据。结合 `JsonCssExtractionStrategy.generate_schema()`，甚至可以自动化生成用于结构化提取的CSS选择器Schema，进一步降低开发成本。

### 2.3 关键：提取隐藏参数的策略

**此过程分为"AI工具自动发现"和"自动执行"两个阶段。**

1.  **AI工具自动发现 (一次性工作):**
    *   **目标:** 利用 `Crawl4AI` 的高级调试能力（如 `js_code` 执行后通过 `CrawlResult` 获取 `metadata` 或 `extracted_content`），或结合 `LLMExtractionStrategy`，自动定位并识别存储着关键参数（如 `session_token`, `play_id`）的页面JavaScript变量、局部存储或网络请求响应体中的数据。
    *   **方法:** 通过编写适配器或利用 `Crawl4AI` 的 `js_code` 参数，在页面加载完成后自动执行JS代码，探测 `window` 对象、`localStorage` 或通过拦截网络请求获取响应数据，智能分析并提取目标参数。此阶段着重于通过LLM的语义理解能力，从非结构化或半结构化页面数据中自动推断出所需参数及其提取方式，例如使用 `LLMExtractionStrategy` 结合自然语言指令直接提取关键信息。

2.  **自动执行 (`Crawl4AI`):**
    *   **核心思想:** 让浏览器自己把数据"拿出来"。
    *   **实现:** 在 `Crawl4AI` 访问页面后，通过 `js_code` 执行一段JS，读取侦察阶段找到的变量，并将其值写入一个临时的DOM元素属性中 (如: `document.body.setAttribute('data-play-id', window.player.playId);`)。或直接通过 `LLMExtractionStrategy` 或 `JsonCssExtractionStrategy` 定义的Schema进行提取。
    *   最后，在 `JsonCssExtractionStrategy` 中增加一个字段，用于从这个临时属性中提取所需参数，或者直接通过 `LLMExtractionStrategy` 返回结构化数据。

## 三、精简的模块化代码结构

*   `main.py`: 主流程控制器，负责调用其他模块。在调用 `crawler_service` 后，必须检查返回的 `CrawlResult` 对象的 `success` 属性，并根据 `error_message` 属性进行日志记录或执行重试逻辑。
*   `config.py`: 集中管理所有配置信息。**应包含预设的 `BrowserConfig` 和 `CrawlerRunConfig` 实例**（如 `DEV_BROWSER_CONFIG`, `PROD_RUN_CONFIG`），而不仅仅是URL和Schema。
*   `crawler_service.py`: **`Crawl4AI` 的唯一接口层。** 封装如 `login_and_save_session`, `fetch_all_courses`, `study_selected_courses` 等原子操作。所有函数在调用 `crawler.arun()` 或 `arun_many()` 后，**应直接返回完整的 `CrawlResult` 对象或 `List[CrawlResult]`**，将成功与否的判断交由上层处理。
*   `course_matcher.py`: **纯算法模块。** 输入为 `crawler_service.py` 提供的结构化课程数据（`List[Dict]`），输出为匹配好的课程列表。不包含任何爬虫代码，便于独立测试。
*   `utils.py`: 提供日志配置等通用辅助功能。

## 四、技术栈与部署

*   **核心库:** `Python`, `Crawl4AI`, `dddocr` (用于验证码识别)。
*   **部署:** 开发时 `headless=False`，部署时 `headless=True`。整个流程由 `