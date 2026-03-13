import requests
from bs4 import BeautifulSoup
import json
import datetime
import time
import os

FETCH_ALL_PAST = False
print("公式スケジュールの取得を開始します（詳細ページからのメンバー抽出含む）...")

# ① 過去の取得済みデータを読み込んでおく（詳細ページへの無駄なアクセスを防ぐため）
existing_schedules_cache = {}
for year in range(2019, datetime.date.today().year + 2):
    filename = f"schedule_{year}.json"
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # 既に「members」が取得できているものだけキャッシュに登録
                    if 'members' in item:
                        existing_schedules_cache[item['id']] = item
        except:
            pass

target_months = []
today = datetime.date.today()

if FETCH_ALL_PAST:
    start_year, start_month = 2019, 1
else:
    last_month_date = today.replace(day=1) - datetime.timedelta(days=1)
    start_year, start_month = last_month_date.year, last_month_date.month

end_year = today.year
end_month = today.month + 3
if end_month > 12:
    end_month -= 12
    end_year += 1

y, m = start_year, start_month
while (y < end_year) or (y == end_year and m <= end_month):
    target_months.append(f"{y}{m:02d}")
    m += 1
    if m > 12:
        m = 1
        y += 1

all_schedules = []

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
                
                # URLから取り出したID（URLがない場合は取得順の数字）
                base_id = url_path.split('/')[-1].split('?')[0] if url_path else str(len(all_schedules))
                # 「日付_番組ID」の形にして、絶対に被らない一意のIDを作る！
                item_id = f"{full_date}_{base_id}"

                members = []
                
                # ② メンバー取得ロジック（キャッシュに無ければ詳細ページへアクセス）
                if item_id in existing_schedules_cache:
                    # 既に取得済みの場合は過去の記憶を再利用する
                    members = existing_schedules_cache[item_id]['members']
                else:
                    # 初めて見る予定の場合は詳細ページへアクセス
                    if full_url:
                        try:
                            detail_resp = requests.get(full_url)
                            detail_resp.encoding = 'utf-8'
                            detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                            
                            # <div class="c-article__tag"> を探し、その中の <b> が「メンバー」なら <a> タグを取得
                            tag_divs = detail_soup.find_all('div', class_='c-article__tag')
                            for tag_div in tag_divs:
                                b_tag = tag_div.find('b')
                                if b_tag and 'メンバー' in b_tag.text:
                                    a_tags = tag_div.find_all('a')
                                    members = [a.text.strip() for a in a_tags]
                                    break
                        except Exception as e:
                            print(f"詳細ページの取得エラー ({full_url}): {e}")
                            
                        # 詳細ページにアクセスした時は必ず1秒休む
                        time.sleep(1)
                
                schedule_data = {
                    "id": item_id,
                    "date": full_date,
                    "category": category,
                    "time": time_str,
                    "title": title,
                    "url": full_url,
                    "members": members # ★メンバーの配列（リスト）を追加！
                }
                all_schedules.append(schedule_data)
                
        # 一覧ページごとの待機
        time.sleep(1)
        
    except Exception as e:
        print(f"{yyyymm} の取得中にエラーが発生しました: {e}")

schedules_by_year = {}
for item in all_schedules:
    year = item['date'][:4]
    if year not in schedules_by_year:
        schedules_by_year[year] = []
    schedules_by_year[year].append(item)

for year, items in schedules_by_year.items():
    filename = f"schedule_{year}.json"
    
    # 重複排除と並び替え
    merged_dict = {i['id']: i for i in items}
    merged_list = list(merged_dict.values())
    merged_list.sort(key=lambda x: (x['date'], x['time']))
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=4)
        
    print(f"{filename} を更新しました！（合計 {len(merged_list)} 件）")

print("\nスケジュールの年別・メンバー付き取得が完了しました！")