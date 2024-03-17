from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import datetime as dt


def get_broadcast_start_time(channel_id):
    options = webdriver.ChromeOptions()

    options.add_argument('headless')
    options.add_argument('disable-gpu')
    options.add_argument('lang=ko_KR')
    options.add_argument('no-sandbox')
    options.add_argument('window-size=1920x1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(f'https://play.afreecatv.com/{channel_id}')
    driver.implicitly_wait(1)

    time = driver.find_element(By.CSS_SELECTOR,
                               '#player_area > div.broadcast_information > div.text_information > ul > li:nth-child(1) > span').text

    return dt.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')


def get_balloon_count(start_time):
    url = "https://point.afreecatv.com/Balloon/AfreecaNormalExchange.asp?gifttype=1"

    options = webdriver.ChromeOptions()

    options.add_argument('lang=ko_KR')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)

    driver.implicitly_wait(5)

    input("로그인 후 엔터를 눌러주세요.")

    output = {}
    nickname_id = {}
    sum = 0

    try:
        for j in range(10000):  # 최대 10000페이지 읽기
            for i in range(10):
                print(f'{j+1}페이지 {i + 1}번째 풍선을 읽는 중...')
                col = driver.find_element(By.CSS_SELECTOR,
                                          f'body > div.sub_whole > div.sub_contents > div > div.myballoon > div:nth-child(2) > table > tbody > tr:nth-child({i + 2})')

                time_text = col.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                time = dt.datetime.strptime(time_text, '%Y-%m-%d %H:%M:%S')

                if time < start_time:
                    print('방송 시간 이내의 풍선을 모두 읽었습니다.')
                    return output, nickname_id

                id_and_nickname = col.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').text
                nickname = id_and_nickname.split('(')[0]
                uid = id_and_nickname.split('(')[1][:-1]
                balloon_count = col.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text[:-1]

                if nickname in nickname_id:
                    if nickname not in nickname_id[uid]:
                        nickname_id[uid].append(nickname)
                else:
                    nickname_id[uid] = [nickname]

                if uid in output:
                    output[uid] += int(balloon_count)
                else:
                    output[uid] = int(balloon_count)

                sum += int(balloon_count)

            driver.find_element(By.CSS_SELECTOR, f'#spnPaging > a:nth-child({j+2})').click()
            driver.implicitly_wait(3)

    except Exception as e:
        print('풍선을 모두 읽었거나 오류가 발생했습니다.')
        return output, nickname_id


if __name__ == '__main__':
    count, nickname_id = get_balloon_count(get_broadcast_start_time("vhznina"))

    sorted_count = sorted(count.items())

    f = open("{:%Y-%m-%d %H-%M-%S}.txt".format(dt.datetime.now()), 'w', encoding='utf-8')
    for uid, balloon in sorted_count:
        nickname = nickname_id[uid]
        # 닉네임1, 닉네임2: (별풍선 갯수)
        f.write(f'{", ".join(nickname)}: {balloon}개\n')

    f.close()
