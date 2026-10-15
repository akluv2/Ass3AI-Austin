from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def test_gemini_connection():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0
    )

    response = llm.invoke("Say hello in one short sentence.")

    assert response.content
    print(response.content)