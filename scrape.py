import requests
from bs4 import BeautifulSoup, NavigableString
import json
import time
import os

base_url = "https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&page="
target_pages = 380  # 過去の漏れた記事も回収するため、50ページ分取得します

print(f"最新の {target_pages} ページを取得し、年別のJSONに追記します...")

new_articles = []

for page in range(target_pages):
    url = base_url + str(page)
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.find_all('div', class_='p-blog-article')
        if not articles:
            break

        for article in articles:
            # 万が一特定の項目でエラーが起きても、記事自体は捨てないように安全に取得します
            try:
                # 1. 各項目の安全な取得（見つからなかった場合の予備テキストを用意）
                title_tag = article.find('div', class_='c-blog-article__title')
                title = title_tag.text.strip() if title_tag else "タイトルなし"

                date_tag = article.find('div', class_='c-blog-article__date')
                date = date_tag.text.strip() if date_tag else "1970.1.1 00:00"
                year = date.split('.')[0] if '.' in date else "2099"

                name_tag = article.find('div', class_='c-blog-article__name')
                author = name_tag.text.strip() if name_tag else "不明なメンバー"

                # 2. 記事IDの安全な取得
                article_id = "unknown"
                detail_link = article.find('a', class_='c-button-blog-detail')
                if detail_link and detail_link.has_attr('href'):
                    href = detail_link['href']
                    if 'detail/' in href:
                        article_id = href.split('detail/')[1].split('?')[0]
                    else:
                        article_id = href.split('/')[-1].split('?')[0] # 予備の抽出方法

                # 3. 本文と画像の抽出（アップデート版）
                text_area = article.find('div', class_='c-blog-article__text')
                blocks = []
                image_urls = []
                
                if text_area:
                    # 見えない裏側のタグを削除
                    for hidden_tag in text_area(["script", "style"]):
                        hidden_tag.decompose()

                    for br in text_area.find_all("br"):
                        br.replace_with("\n")
                        
                    current_text = ""
                    for element in text_area.descendants:
                        if isinstance(element, NavigableString):
                            text = str(element).strip(" \t\r")
                            if text:
                                current_text += text
                        elif element.name == 'img':
                            img_url = element.get('data-src') or element.get('src') or ""
                            if img_url:
                                if 'emoji' in img_url or 'decopic' in img_url or 'icon' in img_url:
                                    continue
                                
                                if current_text.strip():
                                    blocks.append({"type": "text", "value": current_text.strip()})
                                    current_text = ""
                                
                                blocks.append({"type": "image", "value": img_url})
                                image_urls.append(img_url)
                                
                    if current_text.strip():
                        blocks.append({"type": "text", "value": current_text.strip()})
                        
                # 4. プレビュー文の作成
                excerpt = "プレビューがありません"
                for b in blocks:
                    if b["type"] == "text":
                        clean_text = b["value"].replace('\n', ' ').replace('\r', '')
                        excerpt = clean_text[:40] + "..."
                        break

                blog_data = {
                    "id": article_id,
                    "author": author,
                    "title": title,
                    "date": date,
                    "excerpt": excerpt,
                    "blocks": blocks,
                    "imageUrls": image_urls,
                    "year": year
                }
                
                new_articles.append(blog_data)
                
            except Exception as e:
                # エラーが出た場合はスキップせず、ターミナル（GitHub）の画面に犯人を表示します
                print(f"警告: 記事（ID: {article_id}）の解析中にエラーが起きました - {e}")
                continue
                
        time.sleep(1)

    except Exception as e:
        print(f"ページの通信中にエラーが発生しました: {e}")
        break

# 年ごとにデータを振り分ける
articles_by_year = {}
for article in new_articles:
    year = article['year']
    if year not in articles_by_year:
        articles_by_year[year] = []
    articles_by_year[year].append(article)

for year, articles in articles_by_year.items():
    filename = f"blogs_{year}.json"
    existing_data = []
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
                
    merged_dict = {item['id']: item for item in existing_data}
    for item in articles:
        merged_dict[item['id']] = item
        
    merged_list = list(merged_dict.values())
    
    try:
        merged_list.sort(key=lambda x: int(x['id']) if x['id'].isdigit() else 0, reverse=True)
    except:
        pass

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=4)
        
    print(f"{filename} を更新しました！（合計 {len(merged_list)} 件）")

print("\n差分更新と年別JSONへの分割が完了しました！")