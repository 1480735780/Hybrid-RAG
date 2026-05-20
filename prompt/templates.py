"""
Prompt Templates - LLM prompt templates for RAG.
"""

from typing import Dict, List, Optional


class PromptTemplates:
    """
    Prompt Templates for RAG system.

    Features:
    - System prompts
    - Query prompts
    - Context formatting
    - Response formatting
    """

    # System prompt for Ops Assistant
    SYSTEM_PROMPT = """You are an expert DevOps and system operations assistant. Your role is to help users diagnose and resolve technical issues related to:

- Linux system administration
- Docker container management
- MySQL database troubleshooting
- Nginx web server configuration
- Kubernetes cluster management
- CI/CD pipeline issues
- Server deployment and maintenance
- Log analysis and debugging

You should:
1. Analyze error messages and logs carefully
2. Provide clear, step-by-step solutions
3. Include relevant shell commands when appropriate
4. Explain the root cause of issues
5. Suggest preventive measures

Always base your answers on the provided context and reference sources when available."""

    # Query rewrite prompt
    QUERY_REWRITE_PROMPT = """Given the following chat history and current query, rewrite the query to be more specific and searchable.

Chat History:
{history}

Current Query: {query}

Rewritten Query:"""

    # RAG answer prompt
    RAG_ANSWER_PROMPT = """Based on the following context, answer the user's question. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {query}

Please provide a detailed answer with:
1. Root cause analysis
2. Step-by-step solution
3. Relevant commands (if applicable)
4. References to source documents

Answer:"""

    # Log analysis prompt
    LOG_ANALYSIS_PROMPT = """Analyze the following log entries and identify:
1. Error patterns
2. Root causes
3. Potential solutions
4. Severity levels

Log entries:
{log_content}

Please provide a structured analysis:"""

    # Error diagnosis prompt
    ERROR_DIAGNOSIS_PROMPT = """Diagnose the following error and provide solutions:

Error: {error_message}
Service: {service}
Context: {context}

Please provide:
1. Error explanation
2. Common causes
3. Step-by-step resolution
4. Prevention measures"""

    # Command recommendation prompt
    COMMAND_PROMPT = """Based on the following issue, recommend appropriate shell commands:

Issue: {issue}
System: {system}
Context: {context}

Please provide:
1. Diagnostic commands
2. Resolution commands
3. Verification commands

Format each command with explanation."""

    @classmethod
    def format_system_prompt(cls, additional_context: Optional[str] = None) -> str:
        """
        Format system prompt with optional additional context.

        Args:
            additional_context: Additional context to add

        Returns:
            Formatted system prompt
        """
        prompt = cls.SYSTEM_PROMPT

        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"

        return prompt

    @classmethod
    def format_rag_prompt(
        cls,
        query: str,
        context: List[Dict],
        history: Optional[List[Dict]] = None,
    ) -> str:
        """
        Format RAG prompt with context and history.

        Args:
            query: User query
            context: Retrieved context documents
            history: Chat history

        Returns:
            Formatted prompt
        """
        # Format context
        context_str = "\n\n".join([
            f"[Source {i+1}] {doc.get('content', '')}"
            for i, doc in enumerate(context)
        ])

        # Format history
        history_str = ""
        if history:
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[-5:]
            ])

        return cls.RAG_ANSWER_PROMPT.format(
            context=context_str,
            query=query,
        )

    @classmethod
    def format_query_rewrite_prompt(
        cls,
        query: str,
        history: List[Dict],
    ) -> str:
        """
        Format query rewrite prompt.

        Args:
            query: Original query
            history: Chat history

        Returns:
            Formatted prompt
        """
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history[-3:]
        ])

        return cls.QUERY_REWRITE_PROMPT.format(
            history=history_str,
            query=query,
        )

    @classmethod
    def format_log_analysis_prompt(cls, log_content: str) -> str:
        """
        Format log analysis prompt.

        Args:
            log_content: Log content to analyze

        Returns:
            Formatted prompt
        """
        return cls.LOG_ANALYSIS_PROMPT.format(log_content=log_content)

    @classmethod
    def format_error_diagnosis_prompt(
        cls,
        error_message: str,
        service: str,
        context: str,
    ) -> str:
        """
        Format error diagnosis prompt.

        Args:
            error_message: Error message
            service: Service name
            context: Additional context

        Returns:
            Formatted prompt
        """
        return cls.ERROR_DIAGNOSIS_PROMPT.format(
            error_message=error_message,
            service=service,
            context=context,
        )

    @classmethod
    def format_command_prompt(
        cls,
        issue: str,
        system: str,
        context: str,
    ) -> str:
        """
        Format command recommendation prompt.

        Args:
            issue: Issue description
            system: System information
            context: Additional context

        Returns:
            Formatted prompt
        """
        return cls.COMMAND_PROMPT.format(
            issue=issue,
            system=system,
            context=context,
        )

    @classmethod
    def format_source_citation(cls, sources: List[Dict]) -> str:
        """
        Format source citations.

        Args:
            sources: List of source documents

        Returns:
            Formatted citation string
        """
        if not sources:
            return ""

        citations = ["\n\nReferences:"]

        for i, source in enumerate(sources, 1):
            metadata = source.get("metadata", {})
            doc_name = metadata.get("filename", "Unknown Document")
            page = metadata.get("page_number", "")
            score = source.get("score", 0)

            citation = f"[{i}] {doc_name}"
            if page:
                citation += f", Page {page}"
            citation += f" (Relevance: {score:.2f})"

            citations.append(citation)

        return "\n".join(citations)
