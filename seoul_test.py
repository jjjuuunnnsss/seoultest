import streamlit as st
import requests
from urllib.parse import quote

# 1. 보안을 위한 Secrets 설정 확인
SEOUL_API_KEY = st.secrets.get("seoul_api_key")

def get_seoul_library_ebook_details(keyword):
    """
    서울도서관 API 통합 검색 후 
    중복 제거된 '전자책'의 상세 리스트와 권수를 반환합니다.
    """
    if not SEOUL_API_KEY:
        st.error("🔑 API 키를 찾을 수 없습니다. Streamlit Cloud의 Secrets 설정을 확인해주세요.")
        return [], 0

    unique_books = {}  # CTRLNO를 키로 사용하여 중복 제거 및 데이터 저장
    encoded_keyword = quote(keyword)
    
    # 자료명 검색 URL과 저자 검색 URL
    search_urls = [
        {"type": "자료명", "url": f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/{encoded_keyword}/%20/%20/%20/%20"},
        {"type": "저자", "url": f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/%20/{encoded_keyword}/%20/%20/%20"}
    ]
    
    for item in search_urls:
        try:
            response = requests.get(item["url"], timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "SeoulLibraryBookSearchInfo" in data:
                    rows = data["SeoulLibraryBookSearchInfo"].get("row", [])
                    for book in rows:
                        # BIB_TYPE_NAME이 "전자책"인 경우만 추출
                        if book.get("BIB_TYPE_NAME") == "전자책":
                            ctrl_no = book.get("CTRLNO")
                            if ctrl_no and ctrl_no not in unique_books:
                                unique_books[ctrl_no] = {
                                    "CTRLNO": ctrl_no,
                                    "자료명": book.get("TITLE"),
                                    "저자": book.get("AUTHOR"),
                                    "출처": item["type"]
                                }
        except Exception:
            continue
            
    # 리스트 형식으로 변환하여 반환
    result_list = list(unique_books.values())
    return result_list, len(result_list)

# --- Streamlit UI ---
st.title("📚 서울도서관 전자책 통합 검색")

keyword = st.text_input("검색어를 입력하세요 (예: 옌롄커)", "")

if keyword:
    with st.spinner('데이터를 통합 분석 중입니다...'):
        ebook_list, total_count = get_seoul_library_ebook_details(keyword)
        
        # 1. 결과 요약 출력
        st.subheader("검색 결과 요약")
        st.metric(label="중복 제거 후 전자책 소장수", value=f"{total_count} 권")
        
        # 2. 상세 리스트업 출력
        if total_count > 0:
            st.subheader("확인된 자료 상세 리스트")
            # 표(Table) 형태로 출력하여 가독성을 높임
            st.table(ebook_list)
            
            # 참고용 웹 링크
            web_link = f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={quote(keyword)}"
            st.markdown(f"🔗 [서울도서관 전자도서관에서 실제 도서 확인하기]({web_link})")
        else:
            st.info(f"'{keyword}'(으)로 검색된 전자책 결과가 없습니다.")
