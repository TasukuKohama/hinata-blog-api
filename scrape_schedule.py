import requests
from bs4 import BeautifulSoup
import json
import datetime
import time
import os

# ★ 超重要スイッチ：初回の一括取得用
# Trueにすると2019年からの全データを取得します。完了後は必ず False に戻してください。
FETCH_ALL_PAST = True

print("公式スケジュールの取得を開始します...")

target_months = []
today = datetime.date.today()

# ① 取得する月のリストを自動計算する
if FETCH_ALL_PAST:
    # 日向坂46改名（2019年2月）に合わせて、2019年1月から取得スタート
    start_year = 2019
    start_month = 1
else:
    # 通常の更新時は「先月」からスタート（急な過去の予定変更にも対応するため）
    last_month_date = today.replace(day=1) - datetime.timedelta(days=1)
    start_year = last_month_date.year
    start_month = last_month_date.month

# 終了は「現在から未来3ヶ月後」まで
end_year = today.year
end_month = today.month + 3
if end_month > 12:
    end_month -= 12
    end_year += 1

# 対象となる「YYYYMM」のリストを作成
y, m = start_year, start_month
while (y < end_year) or (y == end_year and m <= end_month):
    target_months.append(f"{y}{m:02d}")
    m += 1
    if m > 12:
        m = 1
        y += 1

all_schedules = []

# ② 月ごとにスクレイピングを実行
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
                
        # サーバー負荷軽減のため1秒待機
        time.sleep(1)
        
    except Exception as e:
        print(f"{yyyymm} の取得中にエラーが発生しました: {e}")

# ③ 取得した全データを「年」ごとに振り分ける
schedules_by_year = {}
for item in all_schedules:
    year = item['date'][:4] # "2026-03-12" から "2026" を取り出す
    if year not in schedules_by_year:
        schedules_by_year[year] = []
    schedules_by_year[year].append(item)

# ④ 年ごとのJSONファイルに保存する
for year, items in schedules_by_year.items():
    filename = f"schedule_{year}.json"
    existing_data = []
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                pass
                
    # 重複を排除して結合
    merged_dict = {i['id']: i for i in existing_data}
    for i in items:
        merged_dict[i['id']] = i
        
    merged_list = list(merged_dict.values())
    
    # 日付と時間で綺麗に並び替える
    merged_list.sort(key=lambda x: (x['date'], x['time']))
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=4)
        
    print(f"{filename} を更新しました！（合計 {len(merged_list)} 件）")

print("\nスケジュールの年別取得が完了しました！")