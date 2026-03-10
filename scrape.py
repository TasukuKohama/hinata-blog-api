import requests
from bs4 import BeautifulSoup, NavigableString
import json
import time # 追加：サーバーへの負荷を軽減するための待機用

# 全メンバーのブログ一覧のベースURL（ページ番号を後で付け足します）
base_url = "https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&page="

blog_list = []

# 取得するページ数を指定（ここでは例として、最新の3ページ分を取得します）
target_pages = 500

print(f"全メンバーのブログを {target_pages} ページ分取得します...")

for page in range(target_pages):
    print(f"--- {page + 1}ページ目を取得中 ---")
    
    # URLにページ番号（0, 1, 2...）をくっつける
    url = base_url + str(page)
    
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 記事のまとまりを全て取得
        articles = soup.find_all('div', class_='p-blog-article')
        
        if not articles:
            print("この記事ページにはデータがありませんでした。")
            break

        for article in articles:
            try:
                title = article.find('div', class_='c-blog-article__title').text.strip()
                date = article.find('div', class_='c-blog-article__date').text.strip()
                author = article.find('div', class_='c-blog-article__name').text.strip()
                text_area = article.find('div', class_='c-blog-article__text')
                
                # <br>タグを実際の改行（\n）に変換
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

                blog_data = {
                    "id": article_id,
                    "author": author,
                    "title": title,
                    "date": date,
                    "excerpt": excerpt,
                    "blocks": blocks,
                    "imageUrls": image_urls
                }
                
                blog_list.append(blog_data)
                
            except Exception as e:
                print(f"個別の記事解析中にエラー: {e}")
                continue
                
        # 【重要】スクレイピングのマナー
        # 次のページにアクセスする前に1秒間待機し、サーバーに負荷をかけないようにします
        time.sleep(1)

    except Exception as e:
        print(f"ページ取得中にエラーが発生しました: {e}")
        break

# JSONファイルとして保存
with open('blogs.json', 'w', encoding='utf-8') as f:
    json.dump(blog_list, f, ensure_ascii=False, indent=4)

print(f"\n完了！合計 {len(blog_list)} 件のブログを 'blogs.json' に保存しました。")