import requests
from bs4 import BeautifulSoup
import json
import datetime
import time

print("公式スケジュールの複数月取得を開始します...")

# ① 取得したい月（過去3ヶ月〜未来3ヶ月）を自動計算してリストにする
target_months = []
today = datetime.date.today()
for i in range(-3, 4): # -3, -2, -1, 0, 1, 2, 3
    m = today.month + i
    y = today.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    target_months.append(f"{y}{m:02d}") # 例: "202603"

all_schedules = []

# ② 計算した月ごとに順番にWebサイトへアクセスする
for yyyymm in target_months:
    url = f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={yyyymm}"
    print(f"{yyyymm[:4]}年{yyyymm[4:]}月のスケジュールを取得中...")
    
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        year_tag = soup.find('div', class_='c-schedule__page_year')
        month_tag = soup.find('div', class_='c-schedule__page_month')
        current_year = year_tag.text.strip().replace('年', '') if year_tag else yyyymm[:4]
        current_month = month_tag.text.strip().replace('月', '') if month_tag else yyyymm[4:]

        day_groups = soup.find_all('div', class_='p-schedule__list-group')
        
        for group in day_groups:
            date_tag = group.find('div', class_='c-schedule__date--list')
            if not date_tag or not date_tag.find('span'):
                continue
            day = date_tag.find('span').text.strip().zfill(2)
            full_date = f"{current_year}-{current_month}-{day}"
            
            items = group.find_all('li', class_='p-schedule__item')
            for item in items:
                link_tag = item.find('a')
                url_path = link_tag['href'] if link_tag else ""
                full_url = f"https://www.hinatazaka46.com{url_path}" if url_path else ""
                
                category_tag = item.find('div', class_='c-schedule__category')
                category = category_tag.text.strip() if category_tag else "その他"
                
                time_tag = item.find('div', class_='c-schedule__time--list')
                time_str = time_tag.text.strip() if time_tag else ""
                
                title_tag = item.find('p', class_='c-schedule__text')
                title = title_tag.text.strip() if title_tag else "タイトル不明"
                
                item_id = url_path.split('/')[-1].split('?')[0] if url_path else f"{full_date}_{len(all_schedules)}"
                
                schedule_data = {
                    "id": item_id,
                    "date": full_date,
                    "category": category,
                    "time": time_str,
                    "title": title,
                    "url": full_url
                }
                all_schedules.append(schedule_data)
                
        # サーバーに負荷をかけないよう、1ページ取得したら1秒待機する
        time.sleep(1)
        
    except Exception as e:
        print(f"{yyyymm} の取得中にエラーが発生しました: {e}")

# ③ 万が一の重複を排除して、日付順（カレンダー通り）に並び替える
unique_schedules = list({ item['id']: item for item in all_schedules }.values())
sorted_schedules = sorted(unique_schedules, key=lambda x: (x['date'], x['time']))

# ④ 1つの巨大なJSONファイルとして保存
filename = "schedule.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(sorted_schedules, f, ensure_ascii=False, indent=4)
    
print(f"スケジュール合計 {len(sorted_schedules)} 件を取得し、{filename} に保存しました！")