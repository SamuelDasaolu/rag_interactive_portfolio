import streamlit as st
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# --- Page Config ---
st.set_page_config(page_title="Interactive Biography RAG", page_icon="👤")

st.title("👤 Samuel's Interactive Biography")
st.markdown("Upload a biography (text file) and ask questions to chat with it.")

# --- Sidebar: Configuration ---
with st.sidebar:
    st.header("1. Setup")
    api_key = st.text_input("Google API Key", type="password")
    st.markdown("[Get a Google API Key](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    
    st.header("2. Knowledge Base")
    uploaded_file = st.file_uploader("Upload Biography (.txt)", type="txt")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- Helper Functions ---

def get_text_content(uploaded_file):
    """
    Robust function to read text from uploaded file or local file.
    """
    try:
        if uploaded_file:
            # Use getvalue() to read bytes without moving the cursor, 
            # ensuring it works across reruns.
            return uploaded_file.getvalue().decode("utf-8")
        elif os.path.exists("biography.txt"):
            # Read local file
            with open("biography.txt", "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None
    return None

@st.cache_resource(show_spinner=False)
def build_vector_store(text_content, _api_key):
    """
    Builds the FAISS vector store from raw text content.
    """
    if not text_content:
        return None

    try:
        # 1. Create a Document object directly (bypassing file loaders)
        docs = [Document(page_content=text_content, metadata={"source": "biography"})]

        # 2. Split text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # 3. Create Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", 
            google_api_key=_api_key
        )

        # 4. Build Index
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
        return vectorstore

    except Exception as e:
        st.error(f"Error creating vector store: {e}")
        return None

def get_rag_chain(vectorstore, _api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=_api_key,
            convert_system_message_to_human=True # Helps with some specific error types
        )

        system_prompt = (
            "You are an AI assistant representing the person described in the context. "
            "Answer questions as if you are that person. "
            "Use the following pieces of retrieved context to answer the question. "
            "If the answer is not in the context, say you don't know based on the biography. "
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        retriever = vectorstore.as_retriever()
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        return rag_chain
    except Exception as e:
        st.error(f"Error creating chain: {e}")
        return None

# --- Main Logic ---

def main():
    if not api_key:
        st.warning("Please enter your Google API Key in the sidebar to start.")
        return

    # 1. Get Text Content
    text_content = get_text_content(uploaded_file)

    if not text_content:
        st.info("Please upload a .txt file or create a 'biography.txt' file in the app directory.")
        return

    # 2. Build Vector Store
    with st.spinner("Processing biography..."):
        vectorstore = build_vector_store(text_content, api_key)

    # 3. Chat Interface
    if vectorstore:
        rag_chain = get_rag_chain(vectorstore, api_key)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask me anything about my life..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = rag_chain.invoke({"input": prompt})
                        answer = response['answer']
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"An error occurred during generation: {e}")

if __name__ == "__main__":
    main()