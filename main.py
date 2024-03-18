import random

import typer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import json
import datetime as dt
from rich.prompt import Prompt


def get_broadcast_start_time(channel_id):
    options = webdriver.ChromeOptions()

    options.add_argument("headless")
    options.add_argument("disable-gpu")
    options.add_argument("lang=ko_KR")
    options.add_argument("no-sandbox")
    options.add_argument("window-size=1920x1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    driver.get(f"https://play.afreecatv.com/{channel_id}")
    driver.implicitly_wait(1)

    start_time_text = driver.find_element(
        By.CSS_SELECTOR,
        "#player_area > div.broadcast_information > div.text_information > ul > li:nth-child(1) > span",
    ).text

    driver.quit()

    try:
        start_time = dt.datetime.strptime(start_time_text, "%Y-%m-%d %H:%M:%S")
        return start_time
    except Exception as e:
        print("방송 시작 시간을 가져오는데 실패했습니다.")
        return ask_time()


def get_balloon_count(start_time):
    options = webdriver.ChromeOptions()

    options.add_argument("lang=ko_KR")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    driver.get(
        "https://point.afreecatv.com/Balloon/AfreecaNormalExchange.asp?gifttype=1"
    )

    input("로그인이 완전히 끝난 후 엔터를 눌러주세요.")

    output = {}
    nickname_id = {}
    sum_total = 0

    try:
        for j in range(500):  # 최대 500페이지 읽기
            driver.implicitly_wait(random.uniform(3, 5))

            for i in range(10):
                print(f"{j+1}페이지 {i + 1}번째 풍선을 읽는 중...")
                col = driver.find_element(
                    By.CSS_SELECTOR,
                    f"body > div.sub_whole > div.sub_contents > div > div.myballoon > "
                    f"div:nth-child(2) > table > tbody > tr:nth-child({i + 2})",
                )

                time_text = col.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                balloon_time = dt.datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S")

                if balloon_time < start_time:
                    print("방송 시간 이내의 풍선을 모두 읽었습니다.")
                    driver.quit()
                    return output, nickname_id, sum_total

                id_and_nickname = col.find_element(
                    By.CSS_SELECTOR, "td:nth-child(2) > span"
                ).text
                nickname = id_and_nickname.split("(")[0]
                uid = id_and_nickname.split("(")[1][:-1]
                balloon_count = col.find_element(
                    By.CSS_SELECTOR, "td:nth-child(3)"
                ).text[:-1]

                # 추가 후 중복 제거
                nickname_id[uid] = list(set(nickname_id.get(uid, []) + [nickname]))

                output[uid] = int(balloon_count) + output.get(uid, 0)

                sum_total += int(balloon_count)

            driver.execute_script(f"javascript:goBJPage('{j+2}')")

    except:
        print("풍선을 모두 읽었거나 오류가 발생했습니다.")
        driver.quit()
        return output, nickname_id, sum_total


def save_file(sorted_count, nickname_id, total_sum):
    f = open(
        "{:%Y-%m-%d %H-%M-%S}.txt".format(dt.datetime.now()), "w", encoding="utf-8"
    )
    for uid, balloon in sorted_count:
        nickname = nickname_id[uid]
        # 닉네임1, 닉네임2: (별풍선 갯수)
        f.write(f'{", ".join(nickname)}: {balloon}개\n')

    f.write(f"총 풍선 갯수: {total_sum}개")

    f.close()


def ask_time():
    while True:
        time_text = Prompt.ask("언제 데이터까지 가져올지 입력해주세요. (예: 2023-01-01 00:00:00)")

        try:
            start_time = dt.datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S")
            return start_time
        except:
            print("시간 형식이 잘못되었습니다. 다시 입력해주세요.")


def initial_launch():
    broadcaster_id = typer.prompt("(ex) https://bj.afreecatv.com/vhznina -> vhznina) 방송자 아이디를 입력해주세요.")

    save_data = {"broadcaster_id": broadcaster_id,}

    f = open("ninacalc_settings.json", "w", encoding="utf-8")
    f.write(json.dumps(save_data, ensure_ascii=False, indent=4))
    f.close()

    return broadcaster_id


def get_settings():
    try:
        f = open("ninacalc_settings.json", "r", encoding="utf-8")
        data = json.loads(f.read())
        f.close()
        return data["broadcaster_id"]
    except:
        return initial_launch()


if __name__ == "__main__":
    use_auto_broadcast_time = typer.confirm("방송 시작 시간을 자동으로 가져오시겠습니까?")

    if use_auto_broadcast_time:
        broadcaster_id = get_settings()

        start_time = get_broadcast_start_time(broadcaster_id)
    else:
        start_time = ask_time()

    count, nick, sum_total = get_balloon_count(start_time)

    sort = sorted(count.items())

    save_file(sort, nick, sum_total)
