"""
Streamlit Frontend for Enterprise Ops Assistant.
"""

import streamlit as st
import requests
import json
from typing import List, Dict

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "use_hybrid" not in st.session_state:
        st.session_state.use_hybrid = True
    if "metadata_filter" not in st.session_state:
        st.session_state.metadata_filter = {}


def send_message(message: str) -> Dict:
    """Send message to API and get response."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/",
            json={
                "query": message,
                "session_id": st.session_state.session_id,
                "history": st.session_state.messages[-10:],
                "metadata_filter": st.session_state.metadata_filter,
                "use_hybrid": st.session_state.use_hybrid,
                "top_k": 5,
            },
            timeout=120,
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Please make sure the backend is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def upload_document(file, metadata: Dict) -> Dict:
    """Upload document to API."""
    try:
        files = {"file": (file.name, file.getvalue())}
        data = {"metadata": json.dumps(metadata)}

        response = requests.post(
            f"{API_BASE_URL}/documents/upload",
            files=files,
            data=data,
            timeout=300,
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Upload Error: {str(e)}")
        return None


def get_stats() -> Dict:
    """Get knowledge base statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/knowledge-base/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def search_knowledge_base(query: str, top_k: int = 10) -> Dict:
    """Search knowledge base."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/knowledge-base/search",
            json={
                "query": query,
                "top_k": top_k,
                "use_hybrid": st.session_state.use_hybrid,
            },
            timeout=60,
        )

        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def render_sidebar():
    """Render sidebar with settings."""
    with st.sidebar:
        st.title("Settings")

        # Hybrid search toggle
        st.session_state.use_hybrid = st.checkbox(
            "Use Hybrid Search",
            value=st.session_state.use_hybrid,
            help="Combine BM25 keyword search with vector semantic search",
        )

        # Metadata filters
        st.subheader("Metadata Filters")

        department = st.selectbox(
            "Department",
            ["", "ops", "dev", "security", "network"],
            index=0,
        )

        service = st.selectbox(
            "Service",
            ["", "mysql", "docker", "nginx", "kubernetes", "redis", "jenkins"],
            index=0,
        )

        level = st.selectbox(
            "Priority Level",
            ["", "P1", "P2", "P3"],
            index=0,
        )

        # Update metadata filter
        st.session_state.metadata_filter = {}
        if department:
            st.session_state.metadata_filter["department"] = department
        if service:
            st.session_state.metadata_filter["service"] = service
        if level:
            st.session_state.metadata_filter["level"] = level

        st.divider()

        # Clear chat button
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

        st.divider()

        # Knowledge base stats
        st.subheader("Knowledge Base")
        stats = get_stats()
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats.get("total_documents", 0))
            with col2:
                st.metric("Chunks", stats.get("total_chunks", 0))
        else:
            st.info("Cannot connect to API")


def render_chat():
    """Render chat interface."""
    st.title("Enterprise Ops Assistant")
    st.caption("Intelligent Operations Knowledge Base powered by Hybrid RAG")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Display sources if available
            if "sources" in message and message["sources"]:
                with st.expander("Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        content = source.get("content", "")[:200]
                        metadata = source.get("metadata", {})
                        filename = metadata.get("filename", "Unknown")
                        score = source.get("score", 0)

                        st.markdown(f"**[{i}] {filename}** (Score: {score:.4f})")
                        st.caption(content + "...")
                        st.divider()

    # Chat input
    if prompt := st.chat_input("Enter your question or error log..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = send_message(prompt)

                if response:
                    answer = response.get("answer", "No response")
                    sources = response.get("sources", [])
                    session_id = response.get("session_id")

                    # Update session ID
                    if session_id:
                        st.session_state.session_id = session_id

                    # Display answer
                    st.markdown(answer)

                    # Display sources
                    if sources:
                        with st.expander("Sources"):
                            for i, source in enumerate(sources, 1):
                                content = source.get("content", "")[:200]
                                metadata = source.get("metadata", {})
                                filename = metadata.get("filename", "Unknown")
                                score = source.get("score", 0)

                                st.markdown(f"**[{i}] {filename}** (Score: {score:.4f})")
                                st.caption(content + "...")
                                st.divider()

                    # Add assistant message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                else:
                    st.error("Failed to get response from API")


def render_document_upload():
    """Render document upload interface."""
    st.title("Document Upload")
    st.caption("Upload documents to the knowledge base")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "txt", "md", "log"],
        help="Supported formats: PDF, DOCX, TXT, Markdown, Log files",
    )

    if uploaded_file:
        # Metadata inputs
        st.subheader("Document Metadata")

        col1, col2 = st.columns(2)

        with col1:
            department = st.selectbox(
                "Department",
                ["ops", "dev", "security", "network"],
            )

            service = st.selectbox(
                "Service",
                ["mysql", "docker", "nginx", "kubernetes", "redis", "jenkins", "other"],
            )

        with col2:
            level = st.selectbox(
                "Priority Level",
                ["P1", "P2", "P3"],
            )

            tags = st.text_input(
                "Tags (comma-separated)",
                placeholder="e.g., troubleshooting, performance",
            )

        source = st.text_input(
            "Source",
            placeholder="e.g., MySQL Troubleshooting Guide",
        )

        # Upload button
        if st.button("Upload Document", use_container_width=True):
            with st.spinner("Uploading and processing..."):
                # Prepare metadata
                metadata = {
                    "department": department,
                    "service": service,
                    "level": level,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "source": source,
                }

                # Upload
                result = upload_document(uploaded_file, metadata)

                if result:
                    st.success("Document uploaded successfully!")

                    # Display result
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Document ID", result.get("document_id", "")[:8] + "...")
                    with col2:
                        st.metric("Chunks", result.get("chunks_count", 0))
                    with col3:
                        st.metric("Status", result.get("status", "unknown"))

                    st.json(result)


def render_knowledge_base():
    """Render knowledge base management interface."""
    st.title("Knowledge Base")
    st.caption("Manage your documents and knowledge base")

    # Tabs
    tab1, tab2 = st.tabs(["Documents", "Search"])

    with tab1:
        # List documents
        try:
            response = requests.get(f"{API_BASE_URL}/documents/")
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                total = data.get("total", 0)

                st.metric("Total Documents", total)

                if documents:
                    for doc in documents:
                        with st.expander(f"{doc.get('filename', 'Unknown')} - {doc.get('status', 'unknown')}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**ID:** {doc.get('document_id', '')[:8]}...")
                            with col2:
                                st.write(f"**Chunks:** {doc.get('chunks_count', 0)}")
                            with col3:
                                st.write(f"**Size:** {doc.get('file_size', 0)} bytes")

                            st.json(doc.get("metadata", {}))
                else:
                    st.info("No documents uploaded yet")
            else:
                st.error("Failed to load documents")
        except Exception as e:
            st.info(f"Cannot connect to API: {e}")

    with tab2:
        # Search interface
        search_query = st.text_input("Search query", placeholder="Enter your search query...")
        search_top_k = st.slider("Number of results", 1, 20, 10)

        if st.button("Search", use_container_width=True) and search_query:
            with st.spinner("Searching..."):
                results = search_knowledge_base(search_query, search_top_k)

                if results:
                    st.write(f"Found {results.get('total', 0)} results")

                    for i, result in enumerate(results.get("results", []), 1):
                        content = result.get("content", "")
                        metadata = result.get("metadata", {})
                        score = result.get("score", 0)
                        filename = metadata.get("filename", "Unknown")

                        with st.expander(f"[{i}] {filename} (Score: {score:.4f})"):
                            st.markdown(content)
                            st.json(metadata)
                else:
                    st.info("No results found")


def main():
    """Main application."""
    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Main content area
    tab1, tab2, tab3 = st.tabs(["Chat", "Upload", "Knowledge Base"])

    with tab1:
        render_chat()

    with tab2:
        render_document_upload()

    with tab3:
        render_knowledge_base()


if __name__ == "__main__":
    main()
