import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import tempfile
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from markdown import markdown

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic 모델 정의
class Post(BaseModel):
    source: str
    title: str
    content: str
    strategic_point: str
    key_point: str

class ContentResponse(BaseModel):
    posts: List[Post]

# Mock 데이터
MOCK_DATA = ContentResponse(
    posts=[
        Post(
            source="MBC 전참시, 황석희 번역가",
            title="신입 채용의 미래",
            content="저 같이 코딩 전혀 모르는 문돌이 시니어도 너무나 쉽게 활용할 수 있도록 만들어주신 수많은 AI 기획/개발자 분들께 참 감사합니다. 주로 2030 저연차 분들이 많으시겠죠? 아이러니하게도 이 때문에 회사 저연차 분들에게 지시할 업무가 점점 줄고 있어요. AI를 잘 쓴다는건 '얼마나 좋은 질문을 던질 것인가' & '더 좋은 결과를 위해 뭘 추가 학습 시킬 것인가' 이 두가지가 관건일텐데, 더 빠른 게 강점인 1~3년차보다 더 많이 알면서 느리진 않은 8~10년차 분들의 결과물이 압도적으로 좋습니다. 안타깝고 조심스럽지만, 향후 신입 채용이 얼마나 더 빠르게 줄어들 것인지를 전망케 해주는 사례일 거예요.",
            strategic_point="A 얘기에 B가 빵 터져서 웃었는데, 아무리 생각해도 안웃긴 거예요. 그래서 AI에게 학습시켜서 물어봤어요. 'B가 여기서 왜 웃었다고 생각해?' 그러면 AI가 '둘의 이 대화는 1950년대 어떤 만화의 한 대목으로 ...' 이런 맥락을 물어보고 답변을 얻기 너무 좋은 툴이에요. 남들이 AI 때문에 걱정되지 않냐는 얘기 많이 하는데, 저는 AI가 없는 세상으로 돌아가고 싶지 않아요",
            key_point="빠른 실행과 효율성이 강점인 사람은 AI가 대체재인 셈 깊은 궁리와 신중함이 강점인 사람은 AI가 보완재인 셈"
        )
    ]
)

# 페이지 설정
st.set_page_config(
    page_title="원포인트 전략 컨텐츠 생성기",
    page_icon="🎯",
    layout="wide"
)

def create_image(text, title, strategic_point, key_point, image_number):
    """이미지 생성 (4:6 비율)"""
    width = 1080
    height = 1620
    background_color = "white"
    text_color = "#182551"
    
    img = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("AppleGothic.ttf", 60)
        point_font = ImageFont.truetype("AppleGothic.ttf", 50)
    except:
        st.warning("기본 폰트를 사용합니다. 더 나은 디자인을 위해 'AppleGothic.ttf' 폰트를 설치해주세요.")
        title_font = ImageFont.load_default()
        point_font = ImageFont.load_default()
    
    def wrap_text(text, font, max_width):
        """텍스트를 max_width에 맞게 줄바꿈"""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = draw.textlength(word + " ", font=font)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    # 여백 설정
    padding = 50
    max_width = width - (padding * 2)
    
    # 제목 그리기
    title_lines = wrap_text(title, title_font, max_width)
    y_position = 100
    for line in title_lines:
        draw.text((padding, y_position), line, font=title_font, fill=text_color)
        y_position += 70  # 제목 줄 간격
    
    # 전략적 포인트 그리기
    y_position += 20  # 제목과 포인트 사이 간격
    point_lines = wrap_text(f"🎯 {strategic_point}", point_font, max_width)
    for line in point_lines:
        draw.text((padding, y_position), line, font=point_font, fill=text_color)
        y_position += 60  # 포인트 줄 간격
    
    # 키포인트 그리기
    y_position += 20  # 포인트들 사이 간격
    key_lines = wrap_text(f"💡 {key_point}", point_font, max_width)
    for line in key_lines:
        draw.text((padding, y_position), line, font=point_font, fill=text_color)
        y_position += 60  # 키포인트 줄 간격
    
    # 페이지 번호
    draw.text((width - 100, height - 80), f"{image_number}/5", font=point_font, fill=text_color)
    
    return img

def generate_content(topic, strategy, content_type, reference_text):
    """ChatGPT를 사용하여 컨텐츠 생성"""
    system_prompt = """당신은 전문적인 SNS 컨텐츠 작성자입니다. 
    다음 형식에 맞춰 응답해주세요:
    - title: 제목
    - content: 본문 내용 (200자 이내)
    - strategic_point: 전략적 포인트"""
    
    user_prompt = f"""
    다음 조건에 맞는 5개의 SNS 포스트를 생성해주세요:
    
    주제: {topic}
    전략: {strategy}
    컨텐츠 타입: {content_type}
    참고 텍스트: {reference_text}
    
    - 각 포스트는 제목, 본문, 전략적 포인트로 구성
    - 본문은 200자 이내
    - 전략적 포인트는 핵심 메시지를 한 문장으로 표현
    - 참고 텍스트의 스타일과 톤을 반영
    """
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=ContentResponse
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        st.error(f"컨텐츠 생성 중 오류가 발생했습니다: {str(e)}")
        return None

def main():
    st.title("원포인트 전략 컨텐츠 생성기 🎯")
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("""
            <style>
            .sidebar-textarea textarea {
                height: 100px !important;
                resize: none !important;
            }
            .sidebar-textarea textarea[data-testid="stTextArea"] {
                height: 200px !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.header("컨텐츠 설정")
        
        topic = st.text_input(
            "주제",
            placeholder="예: 성공적인 비즈니스 전략"
        )
        
        strategy = st.text_area(
            "전략",
            placeholder="예: 명확하고 실용적인 비즈니스 인사이트 제공",
            key="strategy_textarea"
        )
        
        content_type = st.selectbox(
            "컨텐츠 타입",
            ["웹툰", "드라마", "영화"]
        )
        
        reference_text = st.text_area(
            "참고 텍스트",
            placeholder="웹툰, 드라마, 영화의 대사나 내용을 입력하세요.",
            key="reference_textarea"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("컨텐츠 생성", type="primary"):
                if topic and strategy and reference_text:
                    with st.spinner("AI가 컨텐츠를 생성하고 있습니다..."):
                        content = generate_content(topic, strategy, content_type, reference_text)
                        if content:
                            st.session_state['content'] = content.posts
                            st.session_state['generated'] = True
                else:
                    st.warning("모든 필드를 입력해주세요!")
        
        with col2:
            if st.button("샘플 테스트", type="secondary"):
                st.session_state['content'] = MOCK_DATA.posts
                st.session_state['generated'] = True

    # 메인 영역: 생성된 컨텐츠 표시
    if 'generated' in st.session_state and st.session_state['generated']:
        # 인스타그램 미리보기 섹션
        st.header("인스타그램 미리보기")
        preview_col1, preview_col2 = st.columns([1, 1])
        
        with preview_col1:
            st.markdown("### 인스타그램 미리보기")
            strategic_point = markdown(st.session_state['content'][0].strategic_point)
            st.markdown(f"""
            {st.session_state['content'][0].title}

            {strategic_point}

            #원포인트전략 #인사이트 #전략적사고
            """, unsafe_allow_html=True)
        
        with preview_col2:
            st.markdown("### 캡션 미리보기")
            content = markdown(st.session_state['content'][0].content)
            st.markdown(f"""
            {st.session_state['content'][0].title}

            {content}

            #원포인트전략 #인사이트 #전략적사고
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # 컨텐츠 편집 섹션
        st.header("컨텐츠 편집")
        edited_content = []
        
        for i, post in enumerate(st.session_state['content'], 1):
            with st.container():
                st.subheader(f"포스트 {i}")
                
                edited_title = st.text_input(
                    "제목",
                    value=post.title,
                    key=f"title_{i}"
                )
                
                edited_strategic_point = st.text_input(
                    "전략적 포인트",
                    value=post.strategic_point,
                    key=f"point_{i}"
                )
                
                edited_key_point = st.text_input(
                    "키포인트",
                    value=post.key_point,
                    key=f"key_point_{i}"
                )
                
                edited_content.append({
                    'title': edited_title,
                    'strategic_point': edited_strategic_point,
                    'key_point': edited_key_point,
                    'content': edited_title
                })
                
                st.divider()
        
        # 이미지 다운로드 섹션
        st.header("이미지 다운로드")
        
        if st.button("모든 이미지 다운로드", type="primary"):
            with tempfile.TemporaryDirectory() as temp_dir:
                for i, post in enumerate(edited_content, 1):
                    img = create_image(post['content'], post['title'], post['strategic_point'], post['key_point'], i)
                    image_path = os.path.join(temp_dir, f"post_{i}.jpg")
                    img.save(image_path)
                    
                    with open(image_path, "rb") as file:
                        st.download_button(
                            label=f"포스트 {i} 다운로드",
                            data=file,
                            file_name=f"post_{i}.jpg",
                            mime="image/jpeg"
                        )

if __name__ == "__main__":
    main() 