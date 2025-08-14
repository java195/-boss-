from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth  # 重点


import time
import random
import os
import json


chrome_options = Options()
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

service = Service(executable_path=r"C:\Users\42425\Desktop\自动化投递简历\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

# 注入 stealth 隐藏webdriver痕迹
stealth(
    driver,
    languages=["zh-CN", "zh", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

wait = WebDriverWait(driver, 288)

def load_cookies_and_login():
    
    print("cookie过段时间会过期把boss_cookies删除重新运行程序即可")
    print("如果想强制退出程序，把浏览器关闭即可")
    if os.path.exists("boss_cookies.json"):
        driver.get("https://www.zhipin.com/")
        with open("boss_cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            cookie.pop('domain', None)
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(5)
        print("已尝试用cookie自动登录！")
    else:
        print("未检测到 cookie，将手动登录~")
        driver.get("https://www.zhipin.com/web/user/?ka=header-login")
        input("请手动登录账号后按回车继续...")
        with open("boss_cookies.json", "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f)
        print("首次登录，已保存cookie！")

def extract_card_info(card):
    def get_by_xpath(card, xpath):
        try:
            return card.find_element(By.XPATH, xpath).text.strip()
        except Exception:
            return ""

    boss_font_map = {
        '\ue031': '0', '\ue032': '1', '\ue033': '2', '\ue034': '3',
        '\ue035': '4', '\ue036': '5', '\ue037': '6', '\ue038': '7',
        '\ue039': '8', '\ue03a': '9', '\ue03b': '.'
    }

    def restore_boss_salary(salary_str):
        return ''.join(boss_font_map.get(char, char) for char in salary_str)

    job_name = get_by_xpath(card, ".//*[contains(@class,'job-name')]")
    salary = get_by_xpath(card, ".//*[contains(@class,'job-salary')]")
    salary = restore_boss_salary(salary)
    tag_list = get_by_xpath(card, ".//*[contains(@class,'tag-list')]")
    company_location = get_by_xpath(card, ".//*[contains(@class,'company-location')]")
    company = get_by_xpath(card, ".//*[contains(@class,'boss-name')]")

    uniq = card.get_attribute("data-jobid")
    if not uniq:
        uniq = f"{job_name}@{company}|{salary}"

    return {
        "job_name": job_name,
        "salary": salary,
        "tag_list": tag_list,
        "company-location": company_location,
        "company": company
    }


try:
    # 1. 使用cookie登录第一次需要手动登录来记录cookie
    load_cookies_and_login()

    # 2. 搜索职位
    search_box = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[contains(@placeholder,'搜索职位') or contains(@id,'search')]")))
    print("岗位默认北京python实习")
    print("如需修改，可直接在job=' '内修改成需要查询的即可")
    job = "北京python实习"

    for char in job:
        search_box.send_keys(char)
        time.sleep(random.uniform(0.2, 0.5))
    search_box.send_keys(Keys.ENTER)
    print("搜索成功，等待结果...")
    time.sleep(random.uniform(60,90))

    # 3. 主投递循环
    cards_xpath = "//*[contains(@class, 'job-info')]"
    chat_btn_xpath = "//*[contains(@class, 'op-btn-chat')]"
    processed = set()
    max_greet = 10
    greet_count = 0
    max_refresh = 5
    refresh_count = 0

    while greet_count < max_greet:
        wait.until(EC.presence_of_element_located((By.XPATH, cards_xpath)))
        time.sleep(10)  # 再等一会
        job_cards = driver.find_elements(By.XPATH, cards_xpath)


        # ======= 完善自动刷新机制 =======
        if len(job_cards) == 0:
            print("卡片数为0，尝试刷新页面...（%d/%d）" % (refresh_count+1, max_refresh))
            refresh_count += 1
            if refresh_count > max_refresh:
                print("连续刷新%次仍无数据，停止脚本！" % max_refresh)
                break
            driver.refresh()
            time.sleep(random.uniform(8, 13))
            # 刷新后重新搜索
            try:
                search_box = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[contains(@placeholder,'搜索职位') or contains(@id,'search')]")))
                search_box.clear()
                for char in job:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.2, 0.4))
                search_box.send_keys(Keys.ENTER)
                print("刷新后重新输入岗位并回车...")
                time.sleep(random.uniform(8, 13))
            except Exception as ee:
                print("刷新后重新搜索遇到故障：", ee)
            continue
        else:
            refresh_count = 0  # 正常有卡片时清零刷新次数

        has_new = False
        need_refresh_stale = False   # <<<< 新增变量，检测本轮是否全部stale

        for card in job_cards:
            uniq = card.get_attribute("data-jobid")
            if uniq in processed:
                continue
            # 防止stale
            try:
                card_text_for_log = card.text
            except StaleElementReferenceException:
                print("stale元素，检测到页面已刷新，自动触发刷新机制！")
                need_refresh_stale = True
                break  # 跳出本轮 for

            if uniq in processed:
                continue
            has_new = True

            try:
                # 模拟鼠标悬停卡片
                actions = ActionChains(driver)
                actions.move_to_element(card).perform()
                print("鼠标悬停在卡片")
                time.sleep(random.uniform(2, 5))
                # 页面随机滚动
                scroll_y = random.randint(100, 900)
                driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                print(f"页面向下滚动 {scroll_y} 像素")
                time.sleep(random.uniform(4, 8))
                # 滚入视图
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                wait.until(EC.element_to_be_clickable(card))
                # 随机模拟浏览详情页
                if random.random() < 0.35:
                    try:
                        detail_btn = card.find_element(By.XPATH, ".//a[contains(@href, 'job_detail')]")
                        actions.move_to_element(detail_btn).perform()
                        time.sleep(random.uniform(4, 6))
                        detail_btn.click()
                        print("浏览详情页几秒")
                        time.sleep(random.uniform(4, 7))
                        driver.execute_script(f"window.scrollBy(0,{random.randint(200, 1200)});")
                        time.sleep(random.uniform(4, 5))
                        driver.back()
                        time.sleep(random.uniform(4, 5))
                    except Exception:
                        print("详情页进入失败，跳过")

                # 点击卡片
                card.click()
                print("已点击卡片：", uniq)
                time.sleep(random.uniform(4, 6))
                # 关键：此处再采集信息
                info = extract_card_info(card)
                print(info)

                processed.add(uniq)

                # 沟通按钮
                try:
                    chat_btn = wait.until(EC.element_to_be_clickable((By.XPATH, chat_btn_xpath)))
                    chat_btn.click()
                    greet_count += 1
                    processed.add(uniq)
                    print(f"已沟通第 {greet_count} 条")
                    # 每5次沟通，休息增大
                    if greet_count % 6 == 0:
                        print("每6次沟通休息30-60秒防反爬...")
                        time.sleep(random.uniform(30, 60))
                    time.sleep(random.uniform(3, 5))
                    if greet_count >= max_greet:
                        break  # 跳出for，剩余卡片不再沟通

                    # “留在此页”弹窗处理
                    try:
                        cancel = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//*[@class='default-btn cancel-btn']"))
                        )
                        cancel.click()
                        time.sleep(random.uniform(0.5, 1))
                    except TimeoutException:
                        print("没有留在此页弹窗，跳过")
                except Exception:
                    print("沟通按钮没找到，跳过")

            except Exception as e:
                print("卡片点击/鼠标行为异常，跳过:", e)
                continue

        # ======= check 刷新机制是否需要触发 =======
        if need_refresh_stale:
            print("检测到本轮存在 stale 或页面刷新，触发自动刷新！")
            refresh_count += 1
            if refresh_count > max_refresh:
                print("连续多次刷新仍无数据或死循环，停止！")
                break
            driver.refresh()
            time.sleep(random.uniform(8, 13))
            # 刷新后重新搜索
            try:
                search_box = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[contains(@placeholder,'搜索职位') or contains(@id,'search')]")))
                search_box.clear()
                for char in job:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.2, 0.4))
                search_box.send_keys(Keys.ENTER)
                print("刷新后重新输入岗位并回车...")
                time.sleep(random.uniform(8, 13))
            except Exception as ee:
                print("刷新后重新搜索遇到故障：", ee)
            continue

        if not has_new:
            print("没有新卡片，退出")
            break

    print("循环结束")

finally:
    input("按回车退出...")
    driver.quit()
