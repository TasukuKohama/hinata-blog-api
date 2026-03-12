import requests
from bs4 import BeautifulSoup
import json
import datetime
import os

# 公式スケジュールのURL（今月のページ）
url = "https://www.hinatazaka46.com/s/official/media/list"

print("公式スケジュールの取得を開始します...")

try:
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    schedules = []
    
    # 1. 現在表示されている「年」と「月」を取得
    year_tag = soup.find('div', class_='c-schedule__page_year')
    month_tag = soup.find('div', class_='c-schedule__page_month')
    current_year = year_tag.text.strip().replace('年', '') if year_tag else str(datetime.datetime.now().year)
    current_month = month_tag.text.strip().replace('月', '') if month_tag else str(datetime.datetime.now().month).zfill(2)

    # 2. 日付ごとのグループ（<div class="p-schedule__list-group">）を探す
    day_groups = soup.find_all('div', class_='p-schedule__list-group')
    
    for group in day_groups:
        # 3. 「日」を取得
        date_tag = group.find('div', class_='c-schedule__date--list')
        if not date_tag or not date_tag.find('span'):
            continue
        day = date_tag.find('span').text.strip().zfill(2)
        full_date = f"{current_year}-{current_month}-{day}" # 例: "2026-03-01"
        
        # 4. その日の予定リスト（<li>）を順番に取得
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
            
            # 予定ごとのユニークID（URLの数字部分などから作成）
            item_id = url_path.split('/')[-1].split('?')[0] if url_path else f"{full_date}_{len(schedules)}"
            
            schedule_data = {
                "id": item_id,
                "date": full_date,
                "category": category,
                "time": time_str,
                "title": title,
                "url": full_url
            }
            schedules.append(schedule_data)

    # 5. JSONとして保存
    filename = "schedule.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False, indent=4)
        
    print(f"スケジュール {len(schedules)} 件を取得し、{filename} に保存しました！")

except Exception as e:
    print(f"スケジュールの取得中にエラーが発生しました: {e}")