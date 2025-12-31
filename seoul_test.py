import streamlit as st
import requests
from urllib.parse import quote

# 1. Secrets 키 확인 (에러 발생 방지를 위해 get 메서드 사용)
# Streamlit Cloud 설정(Secrets)에 seoul_api_key = "..." 가 반드시 있어야 합니다.
SEOUL_API_KEY = st.secrets.get("seoul_api_key")

def get_seoul_library_ebook_count(keyword):
    """
    서울도서관 API 통합 검색 및 '전자책' 필터링 로직
    """
    # API 키가 없을 경우 사용자에게 알림
    if not SEOUL_API_KEY:
        st.error("🔑 API 키를 찾을 수 없습니다. Streamlit Cloud의 Secrets 설정을 확인해주세요.")
        return 0

    unique_books = {}
    encoded_keyword = quote(keyword) # 이미 문자열이면 바로 quote 가능
    
    # 분석된 최적의 검색 URL (자료명, 저자 순서 고정)
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
                        # 3. <BIB_TYPE_NAME>이 "전자책"인 자료만 필터링
                        if book.get("BIB_TYPE_NAME") == "전자책":
                            # 2. 중복 제거: <CTRLNO> 기준
                            ctrl_no = book.get("CTRLNO")
                            if ctrl_no:
                                unique_books[ctrl_no] = book
                else:
                    # 데이터가 없을 때 API가 보내는 메시지 확인용 (필요시 주석 해제)
                    # st.write(f"{item['type']} 결과 없음: {data.get('RESULT', {}).get('MESSAGE')}")
                    pass
        except Exception as e:
            st.warning(f"{item['type']} 검색 중 통신 에러가 발생했습니다.")
            continue
            
    return len(unique_books)

# --- 실행부 ---
st.title("서울도서관 전자책 검색기")
keyword = st.text_input("검색어를 입력하고 엔터를 치세요", "")

if keyword:
    with st.spinner('서울도서관 데이터를 분석 중입니다...'):
        count = get_seoul_library_ebook_count(keyword)
        
        # 결과 출력
        st.metric(label="중복 제거 후 전자책 소장수", value=f"{count} 권")
        
        if count == 0:
            st.info("검색된 전자책이 없습니다. 검색어를 바꿔보거나 'ze' 유형이 있는지 확인해보세요.")
