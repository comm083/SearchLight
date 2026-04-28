import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class NLPService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[Warning] OPENAI_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key)
        print("[Service] OpenAI NLP 서비스 초기화 완료!")

    def generate_security_report(self, query: str, contexts: list):
        """
        검색된 장면들(contexts)을 바탕으로 자연어 보안 보고서를 생성합니다.
        """
        if not contexts:
            return "검색된 관련 데이터가 없어 보고서를 생성할 수 없습니다."

        # 검색된 장면들의 묘사를 텍스트로 합침
        context_text = "\n".join([f"- {c.get('description', '설명 없음')}" for c in contexts])
        
        system_prompt = "당신은 지능형 CCTV 보안 관제 시스템 '서치라이트'의 AI 요원입니다."
        user_prompt = f"""
사용자의 질문과 검색된 CCTV 장면 묘사들을 바탕으로 전문적인 '보안 상황 요약 보고서'를 작성해 주세요.

[사용자 질문]: {query}

[검색된 CCTV 장면 묘사들]:
{context_text}

[작성 지침]:
1. 전문 보안 요원처럼 격식 있고 명확한 문체를 사용하세요.
2. 검색된 사실(장면 묘사)에 기반하여 상황을 요약하세요.
3. 발견된 인물이나 차량의 특징, 행동을 구체적으로 언급하세요.
4. 상황의 위험성이나 특이사항이 있다면 강조해 주세요.
5. 보고서 형식으로 작성하고, 마지막은 "이상입니다."로 마무리하세요.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[NLP Error] 보고서 생성 실패: {e}")
            return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"

    def generate_ood_response(self, user_query: str):
        """
        보안과 관련 없는 질문(Out-of-Distribution)에 대해 친절하게 거절하는 답변을 생성합니다.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 SearchLight라는 지능형 CCTV 보안 AI야. 사용자로부터 보안과 관련 없는 일상적인 질문(인사, 날씨, 농담 등)을 받으면, 자신을 보안 전문가로 소개하며 보안 및 관제 관련 질문을 해달라고 친절하고 정중하게 요청해줘. 답변은 2문장 내외로 짧게 해."},
                    {"role": "user", "content": f"사용자 질문: {user_query}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "안녕하세요. 저는 지능형 보안 AI SearchLight입니다. 현재는 보안 및 CCTV 관제와 관련된 질문에 대해서만 도움을 드릴 수 있습니다. 궁금하신 보안 사항이 있다면 말씀해 주세요."

# 싱글톤 인스턴스 생성
nlp_service = NLPService()
