from bs4 import BeautifulSoup
import requests
import json

# Import headers từ file HEADERS
from HEADERS import HEADERS

# URL mẫu để kiểm tra (có thể thay đổi)
walmart_url = 'https://www.walmart.com/ip/SAMSUNG-65-Class-S90D-OLED-Smart-TV-QN65S90DAFXZA-2024/5340366859'

# Hàm lấy danh sách liên kết sản phẩm từ kết quả tìm kiếm
def get_product_link(query, page_number=1):
    search_url = f'https://www.walmart.com/search?q={query}&page={page_number}'
    try:
        # Gửi yêu cầu GET tới URL
        response = requests.get(search_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm container chứa danh sách sản phẩm
        data = soup.find('div', class_="flex flex-wrap w-100 flex-grow-0 flex-shrink-0 ph2 pr0-xl pl4-xl mt0-xl")

        if not data:
            print(f"Không tìm thấy container sản phẩm trên trang {page_number}.")
            return []

        # Tìm tất cả các thẻ <a> trong container
        links = data.find_all('a')

        # Lọc và chuẩn hóa các liên kết sản phẩm
        product_links = []
        for link in links:
            link_href = link.get('href')
            if link_href and '/ip/' in link_href:  # Chỉ lấy các liên kết sản phẩm
                if 'https' in link_href:
                    full_url = link_href
                else:
                    full_url = 'https://www.walmart.com' + link_href
                product_links.append(full_url)

        return product_links

    except Exception as e:
        print(f"Đã xảy ra lỗi khi lấy danh sách sản phẩm: {e}")
        return []

# Hàm lấy thông tin chi tiết sản phẩm từ liên kết
def extract_product_info(product_url):
    try:
        # Gửi yêu cầu GET tới URL sản phẩm
        response = requests.get(product_url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Lỗi HTTP {response.status_code} khi truy cập {product_url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm dữ liệu JSON trong thẻ <script> có id="__NEXT_DATA__"
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if not script_tag:
            print(f"Không tìm thấy dữ liệu JSON trên trang {product_url}")
            return None

        # Phân tích dữ liệu JSON
        data = json.loads(script_tag.string)
        initial_data = data['props']['pageProps']['initialData']['data']
        product_data = initial_data['product']
        reviews_data = initial_data.get('reviews', {})

        # Tạo dictionary chứa thông tin sản phẩm
        product_info = {
            'product_name': product_data['name'],
            'price': product_data['priceInfo']['currentPrice']['price'],
            'review_count': reviews_data.get('totalReviewCount', 0),
            'item_id': product_data['usItemId'],
            'avg_rating': reviews_data.get('averageOverallRating', 0),
            'brand': product_data.get('brand', ''),
            'availability': product_data['availabilityStatus'],
            'image_url': product_data['imageInfo']['thumbnailUrl'],
            'short_description': product_data.get('shortDescription', ''),
        }

        # In thông tin sản phẩm đã định dạng
        print(json.dumps(product_info, indent=4, ensure_ascii=False))
        return product_info

    except Exception as e:
        print(f"Đã xảy ra lỗi khi trích xuất thông tin sản phẩm từ {product_url}: {e}")
        return None

# Hàm chính để thực hiện tìm kiếm và lưu thông tin sản phẩm
def main():
    OUTPUT_FILE = 'product_info.jsonl'
    query = 'computers'  # Từ khóa tìm kiếm
    max_pages = 10  # Số trang tối đa để tìm kiếm

    with open(OUTPUT_FILE, 'a') as file:
        page_number = 1
        while page_number <= max_pages:
            print(f"Đang xử lý trang {page_number}...")
            links = get_product_link(query, page_number)
            if not links:
                break  # Dừng lại nếu không tìm thấy thêm liên kết sản phẩm

            for link in links:
                try:
                    product_info = extract_product_info(link)
                    if product_info:
                        file.write(json.dumps(product_info) + '\n')
                except Exception as e:
                    print(f"Lỗi khi xử lý liên kết {link}: {e}")

            page_number += 1
        print(f"Hoàn thành thu thập dữ liệu cho {query}.")

if __name__ == '__main__':
    main()
