import streamlit as st
import requests
from urllib.parse import quote

# 1. 보안을 위해 Streamlit Secrets에서 API 키를 가져옵니다.
# Streamlit Cloud 설정의 Secrets 부분에 seoul_api_key = "실제키값" 을 입력해두어야 합니다.
try:
    SEOUL_API_KEY = st.secrets["seoul_api_key"]
except KeyError:
    st.error("Streamlit Secrets에 'seoul_api_key'가 설정되지 않았습니다.")
    SEOUL_API_KEY = None

def get_seoul_library_ebook_count(keyword):
    """
    서울도서관 API를 사용하여 자료명/저자 통합 검색 후 
    중복 제거된 '전자책' 권수만 반환합니다.
    """
    if not SEOUL_API_KEY:
        return "인증키 오류"

    unique_books = {}  # CTRLNO를 키로 사용하여 중복 제거
    encoded_keyword = quote(keyword.encode("utf-8"))
    
    # 자료명 검색 URL과 저자 검색 URL (분석하신 위치값 반영)
    search_urls = [
        f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/{encoded_keyword}/%20/%20/%20/%20",
        f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/%20/{encoded_keyword}/%20/%20/%20"
    ]
    
    for url in search_urls:
        try:
            response = requests.get(url, timeout=7)
            if response.status_code == 200:
                data = response.json()
                
                if "SeoulLibraryBookSearchInfo" in data:
                    rows = data["SeoulLibraryBookSearchInfo"]["row"]
                    
                    for book in rows:
                        # 사용자가 요청한 필터링: <BIB_TYPE_NAME>이 "전자책"인 자료만 포함
                        # 파일 분석 결과 전자책은 이 필드에 '전자책'이라고 명시됨
                        if book.get("BIB_TYPE_NAME") == "전자책":
                            # 중복 제거: 고유번호인 <CTRLNO>를 기준으로 저장
                            ctrl_no = book.get("CTRLNO")
                            if ctrl_no:
                                unique_books[ctrl_no] = book
                                
        except Exception:
            # 개별 호출 오류 시 해당 루프는 건너뜀
            continue
            
    # 최종 필터링 및 중복 제거된 결과 개수 반환
    return len(unique_books)

# --- Streamlit UI 호출 예시 ---
# count = get_seoul_library_ebook_count("옌롄커")
# st.write(f"서울도서관 소장 현황: {count}권")
