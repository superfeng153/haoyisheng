import asyncio
from playwright.async_api import Playwright, async_playwright, expect
import json
import ddddocr
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def login_haoyisheng(page, username, password):
    max_retries = 3
    retry_delay_seconds = 2

    for attempt in range(max_retries):
        logging.info(f"尝试登录 (Attempt {attempt + 1}/{max_retries})...")
        try:
            await page.goto("https://www.cmechina.net/cme/study2.jsp?course_id=202501012211&courseware_id=01")

            # 注册弹窗处理事件 (虽然弹窗可能在登录后出现，但为了健壮性在此注册)
            page.on('dialog', lambda dialog: asyncio.ensure_future(dialog.accept()))

            # --- ddddocr 验证码处理 ---
            # 获取验证码图片元素
            captcha_image_element = page.locator("img[id='imgVerify']")
            # 等待验证码图片元素可见
            await captcha_image_element.wait_for(state="visible", timeout=10000)

            captcha_image_buffer = await captcha_image_element.screenshot()
            # 保存验证码图片到本地，方便调试
            with open("captcha.png", "wb") as f:
                f.write(captcha_image_buffer)
            logging.info("验证码图片已保存到 captcha.png")

            ocr = ddddocr.DdddOcr()
            captcha_text = ocr.classification(captcha_image_buffer)
            logging.info(f"识别到验证码: {captcha_text}")
            # 填写验证码
            await page.locator("#verify_input").fill(captcha_text)
            # ----------------------------------

            # 输入用户名和密码
            await page.locator("#login_name").fill(username)
            await page.locator("#login_pass").fill(password)

            # 点击登录按钮
            await page.locator("#login_but").click()

            # 等待页面发生跳转
            async with page.expect_navigation(timeout=20000):
                pass # 等待任何导航发生
            logging.info("登录成功，页面已发生跳转。") # 立即打印登录成功

            # 登录成功后获取cookies
            cookies = await page.context.cookies()
            return True, cookies

        except Exception as e:
            logging.error(f"登录尝试失败: {e}")
            if attempt < max_retries - 1:
                logging.info(f"等待 {retry_delay_seconds} 秒后重试...")
                await asyncio.sleep(retry_delay_seconds)
            else:
                logging.error("达到最大重试次数，登录失败。")
                return False, None
    return False, None
