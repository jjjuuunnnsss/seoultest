import streamlit as st
import requests
from urllib.parse import quote

# 1. 보안을 위한 Secrets 설정 확인
SEOUL_API_KEY = st.secrets.get("seoul_api_key")

def get_seoul_details(keyword):
    if not SEOUL_API_KEY:
        st.error("🔑 API 키를 찾을 수 없습니다. Secrets 설정을 확인해주세요.")
        return None

    encoded_keyword = quote(keyword)
    
    # 분석을 위한 검색 설정
    configs = [
        {"label": "자료명 검색", "url": f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/{encoded_keyword}/%20/%20/%20/%20"},
        {"label": "저자 검색", "url": f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/%20/{encoded_keyword}/%20/%20/%20"}
    ]
    
    search_results = {}
    all_unique_ebooks = {} # 최종 통합 및 중복 제거용

    for config in configs:
        label = config["label"]
        try:
            response = requests.get(config["url"], timeout=10)
            total_count = 0
            ebook_list = []
            
            if response.status_code == 200:
                data = response.json()
                if "SeoulLibraryBookSearchInfo" in data:
                    # 해당 검색의 전체 검색 결과 수
                    total_count = int(data["SeoulLibraryBookSearchInfo"].get("list_total_count", 0))
                    rows = data["SeoulLibraryBookSearchInfo"].get("row", [])
                    
                    for book in rows:
                        # 전자책 필터링
                        if book.get("BIB_TYPE_NAME") == "전자책":
                            book_info = {
                                "CTRLNO": book.get("CTRLNO"),
                                "자료명": book.get("TITLE"),
                                "저자": book.get("AUTHOR"),
                                "유형": book.get("BIB_TYPE_NAME")
                            }
                            ebook_list.append(book_info)
                            # 전체 통합 딕셔너리에 추가 (중복 제거용)
                            all_unique_ebooks[book.get("CTRLNO")] = book_info
            
            search_results[label] = {
                "total_count": total_count,
                "ebook_count": len(ebook_list),
                "ebook_list": ebook_list
            }
        except Exception as e:
            st.error(f"{label} 중 오류 발생: {e}")
            
    return search_results, all_unique_ebooks

# --- Streamlit UI ---
st.title("📚 서울도서관 검색 상세 분석기")

keyword = st.text_input("검색어를 입력하세요 (예: 히가시노)", "")

if keyword:
    with st.spinner('검색 단계별 데이터를 분석 중입니다...'):
        details, final_ebooks = get_seoul_details(keyword)
        
        if details:
            # 1. 최종 통합 결과
            st.header("🎯 최종 통합 결과 (중복 제거)")
            st.metric("최종 전자책 소장수", f"{len(final_ebooks)} 권")
            
            if final_ebooks:
                with st.expander("최종 전자책 전체 리스트 보기"):
                    st.table(list(final_ebooks.values()))

            st.divider()

            # 2. 검색 경로별 상세 내역 (자료명 vs 저자)
            st.header("🔍 검색 경로별 상세 분석")
            col1, col2 = st.columns(2)

            for i, (label, data) in enumerate(details.items()):
                with [col1, col2][i]:
                    st.subheader(f"[{label}]")
                    st.write(f"• 전체 검색 결과: **{data['total_count']}**건")
                    st.write(f"• 전자책 필터링: **{data['ebook_count']}**건")
                    
                    if data['ebook_list']:
                        with st.expander(f"{label} 전자책 리스트"):
                            st.table(data['ebook_list'])
                    else:
                        st.caption("해당 검색에서 확인된 전자책이 없습니다.")

            st.info("※ API는 한 번에 최대 100건까지만 조회하므로, 실제 도서관 보유 수와 차이가 있을 수 있습니다.")
