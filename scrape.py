import requests
from bs4 import BeautifulSoup, NavigableString
import json
import time
import os # 追加：ファイルの存在確認などに使います

base_url = "https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&page="

# 過去のデータは各年のJSONに蓄積されるため、毎回取得するのは最新の1ページだけで十分になります！
target_pages = 380

print(f"最新の {target_pages} ページを取得し、年別のJSONに追記します...")

new_articles = []

for page in range(target_pages):
    url = base_url + str(page)
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.find_all('div', class_='p-blog-article')
        if not articles:
            break

        for article in articles:
            try:
                title = article.find('div', class_='c-blog-article__title').text.strip()
                date = article.find('div', class_='c-blog-article__date').text.strip()
                author = article.find('div', class_='c-blog-article__name').text.strip()
                text_area = article.find('div', class_='c-blog-article__text')
                
                for br in text_area.find_all("br"):
                    br.replace_with("\n")
                    
                blocks = []
                image_urls = []
                current_text = ""
                
                for element in text_area.descendants:
                    if isinstance(element, NavigableString):
                        text = str(element).strip(" \t\r")
                        if text:
                            current_text += text
                    elif element.name == 'img':
                        if current_text.strip():
                            blocks.append({"type": "text", "value": current_text.strip()})
                            current_text = ""
                        
                        if 'src' in element.attrs:
                            img_url = element['src']
                            blocks.append({"type": "image", "value": img_url})
                            image_urls.append(img_url)
                            
                if current_text.strip():
                    blocks.append({"type": "text", "value": current_text.strip()})
                    
                excerpt = "プレビューがありません"
                for b in blocks:
                    if b["type"] == "text":
                        excerpt = b["value"][:40].replace('\n', ' ') + "..."
                        break

                detail_link = article.find('a', class_='c-button-blog-detail')
                article_id = detail_link['href'].split('detail/')[1].split('?')[0] if detail_link else "unknown"

                # 【重要】日付（例: 2026.3.10）から「年」だけを抽出する
                year = date.split('.')[0]

                blog_data = {
                    "id": article_id,
                    "author": author,
                    "title": title,
                    "date": date,
                    "excerpt": excerpt,
                    "blocks": blocks,
                    "imageUrls": image_urls,
                    "year": year # 年の情報をデータに追加
                }
                
                new_articles.append(blog_data)
                
            except Exception as e:
                continue
                
        time.sleep(1)

    except Exception as e:
        break

# 年ごとにデータを振り分ける
articles_by_year = {}
for article in new_articles:
    year = article['year']
    if year not in articles_by_year:
        articles_by_year[year] = []
    articles_by_year[year].append(article)

# 各年のJSONファイルを読み込み、新しい記事を合体させて保存する
for year, articles in articles_by_year.items():
    filename = f"blogs_{year}.json" # 年別のファイル名（例: blogs_2026.json）
    existing_data = []
    
    # すでにその年のJSONファイルがMacやGitHub内にあれば読み込む
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
                
    # 既存のデータと新しいデータを結合（重複排除）
    # 記事のIDをキーにすることで、全く同じ記事が2回保存されるのを防ぎます
    merged_dict = {item['id']: item for item in existing_data}
    for item in articles:
        merged_dict[item['id']] = item
        
    merged_list = list(merged_dict.values())
    
    # IDの数字が大きい（新しい）順に並び替える
    try:
        merged_list.sort(key=lambda x: int(x['id']) if x['id'].isdigit() else 0, reverse=True)
    except:
        pass

    # JSONファイルとして上書き保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=4)
        
    print(f"{filename} を更新しました！（合計 {len(merged_list)} 件）")

print("\n差分更新と年別JSONへの分割が完了しました！")