import requests
from bs4 import BeautifulSoup
import json
import time

print("メンバープロフィールの取得を開始します...")

# メンバー一覧ページのURL
list_url = "https://www.hinatazaka46.com/s/official/search/artist?ima=0000"

# サイリウムカラーの手動定義リスト（※必要に応じて色名やカラーコードを編集してください）
penlight_colors = {
    "小坂 菜緒": ["ホワイト", "ライトブルー"],
    "金村 美玖": ["イエロー", "ライトブルー"],
    "正源司 陽子": ["オレンジ", "レッド"],
    "藤嶌 果歩": ["サクラピンク", "ブルー"],
    "丹生 明里": ["オレンジ", "オレンジ"],
    "河田 陽菜": ["サクラピンク", "イエロー"],
    "石塚 瑶季": ["サクラピンク", "オレンジ"]
    # ...他のメンバーも追加できます！
}

try:
    response = requests.get(list_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # メンバー詳細ページへのリンクを探す
    member_links = []
    # （※サイトの構造に合わせて、アーティスト一覧のリンクを取得します）
    for a_tag in soup.select('.p-member__item a, .c-member__item a'):
        href = a_tag.get('href')
        if href and 'artist/' in href:
            full_url = f"https://www.hinatazaka46.com{href}"
            if full_url not in member_links:
                member_links.append(full_url)
                
    # もし一覧からうまく取れなかった時の予備（1番から順にアクセス）
    if not member_links:
        for i in range(1, 40): # メンバーIDの範囲
            member_links.append(f"https://www.hinatazaka46.com/s/official/artist/{i}?ima=0000")

    members_data = []

    for url in member_links:
        try:
            res = requests.get(url)
            res.encoding = 'utf-8'
            detail_soup = BeautifulSoup(res.text, 'html.parser')
            
            # ご提示いただいたHTML構造に合わせてデータを抽出
            box = detail_soup.find('div', class_='p-member__box')
            if not box:
                continue
                
            # 名前と画像
            name_info = box.find('div', class_='c-member__name--info')
            if not name_info:
                continue
            
            # 英語名（span）を取り除いて日本語名だけにする
            en_span = name_info.find('span', class_='name_en')
            if en_span:
                en_name = en_span.text.strip()
                en_span.decompose()
            name = name_info.text.strip().replace(' ', ' ') # 空白を整える
            
            kana_tag = box.find('div', class_='c-member__kana')
            kana = kana_tag.text.strip() if kana_tag else ""
            
            img_tag = box.find('div', class_='c-member__thumb').find('img')
            img_url = img_tag['src'] if img_tag else ""
            
            # テーブル情報（生年月日、身長など）
            profile = {
                "name": name,
                "kana": kana,
                "imageUrl": img_url,
                "birthdate": "不明",
                "zodiac": "不明",
                "height": "不明",
                "birthplace": "不明",
                "bloodType": "不明",
                "snsUrl": "",
                "penlights": penlight_colors.get(name, ["不明", "不明"]) # リストから色を取得
            }
            
            table = box.find('table', class_='p-member__info-table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    key_td = row.find('td', class_='c-member__info-td__name')
                    val_td = row.find('td', class_='c-member__info-td__text')
                    if key_td and val_td:
                        key = key_td.text.strip()
                        val = val_td.text.strip()
                        
                        if key == "生年月日": profile["birthdate"] = val
                        elif key == "星座": profile["zodiac"] = val
                        elif key == "身長": profile["height"] = val
                        elif key == "出身地": profile["birthplace"] = val
                        elif key == "血液型": profile["bloodType"] = val
                        elif key == "SNS":
                            a_tag = val_td.find('a')
                            if a_tag: profile["snsUrl"] = a_tag['href']
                            
            members_data.append(profile)
            print(f"{name} のデータを取得しました。")
            time.sleep(1)
            
        except Exception as e:
            pass

    # 名前で重複を削除し、五十音順（kana）で並び替え
    unique_members = { m['name']: m for m in members_data }.values()
    sorted_members = sorted(unique_members, key=lambda x: x['kana'])

    with open("members.json", 'w', encoding='utf-8') as f:
        json.dump(sorted_members, f, ensure_ascii=False, indent=4)
        
    print(f"\nメンバー {len(sorted_members)} 名のプロフィールを取得し、members.json に保存しました！")

except Exception as e:
    print(f"エラーが発生しました: {e}")