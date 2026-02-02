"""RAG engine with FAISS vector store and conversation memory."""

from typing import List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


SYSTEM_PROMPT = """あなたは提供された文脈のみに基づいて回答するアシスタントです。

以下のルールに従ってください：
1. 文脈に含まれる情報のみを使用して回答してください
2. 答えがわからない場合は「この文書には該当する情報がありません」と答えてください
3. 推測や外部知識は使用しないでください

文脈:
{context}

チャット履歴:
{chat_history}

質問: {question}
回答:"""


class RAGEngine:
    """RAG engine with FAISS and conversation memory."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.vectorstore: Optional[FAISS] = None
        self.chat_history: List[Tuple[str, str]] = []
        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vectorstore.add_documents(documents)

    def search(self, query: str, k: int = 4) -> List[Document]:
        """Search for relevant documents."""
        if self.vectorstore is None:
            return []
        return self.vectorstore.similarity_search(query, k=k)

    def _format_chat_history(self) -> str:
        """Format chat history for the prompt."""
        if not self.chat_history:
            return "なし"

        formatted = []
        for human, ai in self.chat_history:
            formatted.append(f"ユーザー: {human}")
            formatted.append(f"アシスタント: {ai}")
        return "\n".join(formatted)

    def _format_context(self, documents: List[Document]) -> str:
        """Format documents into context string."""
        contexts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "不明")
            page = doc.metadata.get("page", "")
            source_info = f"[出典{i}: {source}"
            if page:
                source_info += f", ページ{page + 1}"
            source_info += "]"
            contexts.append(f"{source_info}\n{doc.page_content}")
        return "\n\n".join(contexts)

    def query(self, question: str, k: int = 4) -> Tuple[str, List[Document]]:
        """Query the RAG system and return answer with sources."""
        if self.vectorstore is None:
            return "ドキュメントがまだ登録されていません。まずファイルをアップロードするか、URLを追加してください。", []

        relevant_docs = self.search(question, k=k)

        if not relevant_docs:
            return "関連する情報が見つかりませんでした。", []

        context = self._format_context(relevant_docs)
        chat_history = self._format_chat_history()

        messages = self.prompt.format_messages(
            context=context,
            chat_history=chat_history,
            question=question
        )

        response = self.llm.invoke(messages)
        answer = response.content

        self.chat_history.append((question, answer))

        return answer, relevant_docs

    def clear_history(self) -> None:
        """Clear the chat history."""
        self.chat_history = []

    def clear_all(self) -> None:
        """Clear vector store and chat history."""
        self.vectorstore = None
        self.chat_history = []

    @property
    def document_count(self) -> int:
        """Return the number of documents in the vector store."""
        if self.vectorstore is None:
            return 0
        return len(self.vectorstore.docstore._dict)
