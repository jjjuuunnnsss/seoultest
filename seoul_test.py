import streamlit as st
import requests
from urllib.parse import quote

# 발급받으신 인증키를 여기에 입력하세요
SEOUL_API_KEY = "my_key"

def search_seoul_library(book_name):
    unique_books = set()  # 중복 제거용 집합
    book_details = []     # 최종 리스트
    
    encoded_query = quote(book_name.encode("utf-8"))
    
    # 1. 제목(TITLE) 검색 조건: BIB_TYPE="ze"
    # URL 구조 예시: /1/100/(제목)/(저자)/(자료코드)/(ISBN)/(자료유형)
    # 저자, 자료코드, ISBN 자리는 공백(%20) 처리
    title_search_url = f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/{encoded_query}/%20/%20/%20/ze"
    
    # 2. 저자(AUTHOR) 검색 조건: BIB_TYPE="ze"
    # 제목 자리는 공백(%20) 처리
    author_search_url = f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/%20/{encoded_query}/%20/%20/ze"
    
    urls = [("제목", title_search_url), ("저자", author_search_url)]
    
    for label, url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "SeoulLibraryBookSearchInfo" in data:
                    rows = data["SeoulLibraryBookSearchInfo"]["row"]
                    for book in rows:
                        # 중복 제거를 위한 고유 ID (BOOK_MAST_NO)
                        book_id = book.get("BOOK_MAST_NO")
                        if book_id not in unique_books:
                            unique_books.add(book_id)
                            book_details.append({
                                "제목": book.get("TITLE"),
                                "저자": book.get("AUTHOR"),
                                "출판사": book.get("PUBLISHER"),
                                "발행년": book.get("PUBLISH_YEAR"),
                                "자료유형": book.get("BIB_TYPE_NAME"), # 확인용
                                "검색출처": label
                            })
        except Exception as e:
            st.error(f"{label} 검색 중 오류 발생: {e}")
            
    return book_details

# --- Streamlit UI ---
st.set_page_config(page_title="서울도서관 API v2 테스트", layout="wide")
st.title("📚 서울도서관 전자책(ze) 통합검색 테스트")
st.caption("메뉴얼상의 BIB_TYPE: 'ze' 인자를 사용하여 제목과 저자를 각각 검색합니다.")

keyword = st.text_input("검색어를 입력하세요", "")

if keyword:
    with st.spinner("요청하신 조건으로 검색 중..."):
        results = search_seoul_library(keyword)
        
        if results:
            st.success(f"중복 제거 후 총 **{len(results)}**권의 전자책이 검색되었습니다.")
            st.dataframe(results, use_container_width=True)
            
            web_link = f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={quote(keyword.encode('utf-8'))}"
            st.markdown(f"🔗 [서울도서관 전자도서관 웹사이트에서 확인]({web_link})")
        else:
            st.warning("해당 조건으로 검색된 전자책 결과가 없습니다.")
