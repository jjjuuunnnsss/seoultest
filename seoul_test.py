import streamlit as st
import pandas as pd
from urllib.parse import quote

# 페이지 설정
st.set_page_config(page_title="서초구 대용량 데이터 테스트", page_icon="🔍")

@st.cache_data(ttl=86400)  # 데이터를 24시간 동안 메모리에 보관 (앱 속도 최적화)
def load_seocho_full_data():
    # 9.4MB 전체 데이터 링크
    url = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003242287&fileDetailSn=1&dataNm=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%20%EC%84%9C%EC%B4%88%EA%B5%AC_%EC%A0%84%EC%9E%90%EB%8F%84%EC%84%9C%EA%B4%80%20%EB%8F%84%EC%84%9C%EC%A0%95%EB%B3%B4_20250909"
    
    try:
        # 1. 인코딩 시도 (공공데이터는 대부분 CP949)
        df = pd.read_csv(url, encoding='cp949')
        
        # 2. 데이터 클리닝 (공백 제거 및 문자열 강제 변환)
        df.columns = df.columns.str.strip()
        for col in ['도서명', '저자명', '형식']:
            df[col] = df[col].astype(str).str.strip()
        
        # 3. '전자책' 형식만 추출하여 메모리 최적화 (오디오북 제외)
        df_ebook = df[df['형식'].str.contains("전자책", na=False)].copy()
        return df_ebook
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return None

# UI 구성
st.title("📚 서초구 전자도서관 단독 테스트")
st.info("9.4MB 대용량 CSV 데이터를 분석합니다. 첫 실행 시 다운로드 시간이 3~5초 소요될 수 있습니다.")

with st.spinner("데이터베이스 로딩 중..."):
    df_seocho = load_seocho_full_data()

if df_seocho is not None:
    st.success(f"총 {len(df_seocho):,}권의 전자책 데이터를 로드했습니다.")
    
    # 검색창
    keyword = st.text_input("검색어를 입력하세요 (예: 노인과 바다)", placeholder="입력 후 엔터")
    
    if keyword:
        # 중복 제거 로직 (도서명, 저자명, 출판사가 같으면 1권으로 간주)
        mask = (df_seocho['도서명'].str.contains(keyword, case=False, na=False)) | \
               (df_seocho['저자명'].str.contains(keyword, case=False, na=False))
        
        # 검색 결과 추출
        search_result = df_seocho[mask].drop_duplicates(subset=['도서명', '저자명', '출판사'])
        
        # 결과 요약
        st.subheader(f"🔍 '{keyword}' 검색 결과: {len(search_result)}권")
        
        # 상세 리스트업
        if not search_result.empty:
            # 보기 좋게 표로 출력
            st.table(search_result[['도서명', '저자명', '출판사', '국제 표준 도서 번호(isbn)']].reset_index(drop=True))
            
            # 실제 서초구 전자도서관 연결 링크
            web_link = f"https://e-book.seocholib.or.kr/search?keyword={quote(keyword)}"
            st.markdown(f"🔗 [서초구 전자도서관에서 실제 확인하기]({web_link})")
        else:
            st.warning("일치하는 자료가 없습니다.")

    # 디버깅용 데이터 구조 확인
    with st.expander("데이터 구조 미리보기 (상위 5개)"):
        st.dataframe(df_seocho.head())
