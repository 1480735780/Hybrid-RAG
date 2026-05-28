"""
Streamlit Demo - 纯前端版本，可直接部署到 Streamlit Cloud
不需要后端 API，所有逻辑在前端完成
"""

import streamlit as st
import os

# Page config
st.set_page_config(
    page_title="Enterprise Ops Assistant",
    page_icon="🔧",
    layout="wide",
)

# Title
st.title("🔧 Enterprise Ops Assistant")
st.caption("基于 Hybrid RAG 的企业智能运维知识库平台")


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents" not in st.session_state:
    st.session_state.documents = []
if "chunks" not in st.session_state:
    st.session_state.chunks = []


# Sidebar
with st.sidebar:
    st.title("Settings")

    use_hybrid = st.checkbox("Use Hybrid Search", value=True)
    top_k = st.slider("Top K Results", 1, 10, 5)

    st.divider()

    st.subheader("Metadata Filter")
    department = st.selectbox("Department", ["", "ops", "dev", "security"])
    service = st.selectbox("Service", ["", "mysql", "docker", "nginx", "kubernetes"])

    st.divider()

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.subheader("Knowledge Base")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", len(st.session_state.documents))
    with col2:
        st.metric("Chunks", len(st.session_state.chunks))


def split_text(text, chunk_size=512, overlap=50):
    """Simple text splitter."""
    chunks = []
    paragraphs = text.split('\n\n')
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > chunk_size:
            if current:
                chunks.append(current.strip())
            current = current[-overlap:] + "\n\n" + para if current else para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def simple_search(query, chunks, top_k=5):
    """Simple keyword search (BM25-like)."""
    import re

    # Tokenize query
    query_tokens = set(re.findall(r'[\w一-鿿]+', query.lower()))

    results = []
    for chunk in chunks:
        content = chunk["content"].lower()
        # Count matching tokens
        score = sum(1 for token in query_tokens if token in content)
        if score > 0:
            results.append({
                "content": chunk["content"],
                "metadata": chunk.get("metadata", {}),
                "score": score / len(query_tokens) if query_tokens else 0,
            })

    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def generate_answer(query, context_docs):
    """Generate answer based on context (without LLM)."""
    if not context_docs:
        return f"抱歉，没有找到与 **{query}** 相关的知识库内容。\n\n请先上传运维文档到知识库。"

    answer = f"根据知识库检索，找到以下与 **{query}** 相关的信息：\n\n"

    for i, doc in enumerate(context_docs[:3], 1):
        content = doc["content"][:500]
        metadata = doc.get("metadata", {})
        source = metadata.get("source", "Unknown")
        score = doc.get("score", 0)

        answer += f"### [{i}] 来源: {source}\n"
        answer += f"{content}\n\n"
        answer += f"*相关度: {score:.2f}*\n\n"
        answer += "---\n\n"

    answer += "> 💡 **提示**: 配置 LLM API Key 后可获得更智能的 AI 回答"

    return answer


# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Upload", "🔍 Knowledge Base"])

# Chat tab
with tab1:
    st.subheader("智能问答")

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if "sources" in msg and msg["sources"]:
                with st.expander("📚 Sources"):
                    for i, src in enumerate(msg["sources"], 1):
                        st.markdown(f"**[{i}]** {src.get('content', '')[:200]}...")

    # Chat input
    if prompt := st.chat_input("输入运维问题或错误日志..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                # Search
                results = simple_search(prompt, st.session_state.chunks, top_k)

                # Generate answer
                answer = generate_answer(prompt, results)

                st.markdown(answer)

                if results:
                    with st.expander("📚 Sources"):
                        for i, src in enumerate(results[:3], 1):
                            st.markdown(f"**[{i}]** {src.get('content', '')[:200]}...")

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": results,
                })

# Upload tab
with tab2:
    st.subheader("上传文档")

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["txt", "md", "log"],
        help="支持 TXT、Markdown、日志文件",
    )

    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input("文档来源", value=uploaded_file.name)
        with col2:
            doc_type = st.selectbox("文档类型", ["运维手册", "故障排查", "部署文档", "日志分析"])

        if st.button("上传并处理", use_container_width=True):
            with st.spinner("Processing..."):
                # Read file
                content = uploaded_file.read().decode("utf-8")

                # Split into chunks
                chunks = split_text(content)

                # Add to documents
                doc_info = {
                    "filename": uploaded_file.name,
                    "source": source,
                    "type": doc_type,
                    "chunks_count": len(chunks),
                }
                st.session_state.documents.append(doc_info)

                # Add chunks
                for i, chunk_text in enumerate(chunks):
                    st.session_state.chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "source": source,
                            "type": doc_type,
                            "chunk_index": i,
                        },
                    })

                st.success(f"文档上传成功！生成 {len(chunks)} 个文本块。")

                # Preview
                with st.expander("预览文本块"):
                    for i, chunk in enumerate(chunks[:5], 1):
                        st.markdown(f"**Chunk {i}:**")
                        st.text(chunk[:200] + "...")
                        st.divider()

# Knowledge Base tab
with tab3:
    st.subheader("知识库管理")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文档数", len(st.session_state.documents))
    with col2:
        st.metric("文本块数", len(st.session_state.chunks))
    with col3:
        total_chars = sum(len(c["content"]) for c in st.session_state.chunks)
        st.metric("总字符数", f"{total_chars:,}")

    st.divider()

    # Search
    st.subheader("搜索知识库")
    search_query = st.text_input("搜索查询")

    if search_query:
        results = simple_search(search_query, st.session_state.chunks, top_k=10)

        if results:
            st.write(f"找到 {len(results)} 个结果")
            for i, r in enumerate(results, 1):
                with st.expander(f"[{i}] Score: {r['score']:.2f} - {r['metadata'].get('source', 'Unknown')}"):
                    st.markdown(r["content"])
                    st.json(r["metadata"])
        else:
            st.info("没有找到相关结果")

    st.divider()

    # Document list
    st.subheader("已上传文档")
    if st.session_state.documents:
        for doc in st.session_state.documents:
            with st.expander(f"{doc['filename']} - {doc['type']}"):
                st.write(f"**来源:** {doc['source']}")
                st.write(f"**文本块:** {doc['chunks_count']}")
    else:
        st.info("暂无文档，请先上传")

    if st.button("清空知识库", type="secondary"):
        st.session_state.documents = []
        st.session_state.chunks = []
        st.rerun()
