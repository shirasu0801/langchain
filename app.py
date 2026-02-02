"""Streamlit UI for RAG Q&A Bot."""

import os

import streamlit as st
from dotenv import load_dotenv

from document_loader import process_uploaded_file, process_url
from rag_engine import RAGEngine

load_dotenv()

st.set_page_config(
    page_title="RAG Q&A Bot",
    page_icon="📚",
    layout="wide"
)

st.title("📚 RAG Q&A Bot")
st.caption("ドキュメントをアップロードして質問してください")


def init_session_state():
    """Initialize session state variables."""
    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = RAGEngine()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sources" not in st.session_state:
        st.session_state.sources = []


init_session_state()

with st.sidebar:
    st.header("📁 ドキュメント管理")

    st.subheader("ファイルアップロード")
    uploaded_files = st.file_uploader(
        "PDF/テキストファイルを選択",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("ファイルを追加", type="primary"):
            with st.spinner("ドキュメントを処理中..."):
                for uploaded_file in uploaded_files:
                    try:
                        docs = process_uploaded_file(uploaded_file)
                        st.session_state.rag_engine.add_documents(docs)
                        st.success(f"✅ {uploaded_file.name} を追加しました")
                    except Exception as e:
                        st.error(f"❌ {uploaded_file.name}: {str(e)}")

    st.divider()

    st.subheader("URL追加")
    url_input = st.text_input("URLを入力", placeholder="https://example.com")

    if url_input:
        if st.button("URLを追加"):
            with st.spinner("URLを読み込み中..."):
                try:
                    docs = process_url(url_input)
                    st.session_state.rag_engine.add_documents(docs)
                    st.success(f"✅ URLを追加しました")
                except Exception as e:
                    st.error(f"❌ エラー: {str(e)}")

    st.divider()

    st.subheader("📊 インデックス状態")
    doc_count = st.session_state.rag_engine.document_count
    st.metric("登録チャンク数", doc_count)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("履歴クリア"):
            st.session_state.rag_engine.clear_history()
            st.session_state.messages = []
            st.session_state.sources = []
            st.rerun()
    with col2:
        if st.button("全てリセット"):
            st.session_state.rag_engine.clear_all()
            st.session_state.messages = []
            st.session_state.sources = []
            st.rerun()

main_col, source_col = st.columns([2, 1])

with main_col:
    st.subheader("💬 チャット")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("質問を入力してください"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("考え中..."):
                answer, sources = st.session_state.rag_engine.query(prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.sources = sources

with source_col:
    st.subheader("📑 引用元")

    if st.session_state.sources:
        for i, doc in enumerate(st.session_state.sources, 1):
            source = doc.metadata.get("source", "不明")
            page = doc.metadata.get("page", "")

            with st.expander(f"出典 {i}: {os.path.basename(source)}" + (f" (p.{page + 1})" if page != "" else "")):
                st.markdown(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
    else:
        st.info("質問すると、回答の引用元がここに表示されます")
