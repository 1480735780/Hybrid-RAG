"""
LLM Client - Multi-provider LLM integration.
Supports OpenAI, DashScope (Qwen/DeepSeek), and local models.
"""

from typing import AsyncGenerator, Dict, List, Optional

from loguru import logger


class LLMClient:
    """
    LLM Client supporting multiple providers.

    Supported providers:
    - OpenAI (GPT-4, etc.)
    - DashScope (Qwen, DeepSeek)
    - Local models (Qwen, etc.)
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider (openai, dashscope, local)
            api_key: API key for the provider
            base_url: Base URL for API
            model: Model name
        """
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None

    def _get_client(self):
        """Get or create LLM client based on provider."""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        elif self.provider == "dashscope":
            # DashScope uses OpenAI-compatible API
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

        elif self.provider == "local":
            # Local model using transformers
            self._client = "local"
            logger.info("Using local LLM model")

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if client == "local":
            return await self._generate_local(messages, temperature, max_tokens)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream text generation.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Text chunks
        """
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if client == "local":
            async for chunk in self._generate_local_stream(messages, temperature, max_tokens):
                yield chunk
            return

        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise

    async def _generate_local(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using local model."""
        # TODO: Implement local model generation
        # This would use transformers pipeline
        return "Local model generation not implemented yet"

    async def _generate_local_stream(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Stream generation using local model."""
        # TODO: Implement local model streaming
        yield "Local model streaming not implemented yet"

    async def generate_with_context(
        self,
        query: str,
        context: List[Dict],
        history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate answer with RAG context.

        Args:
            query: User query
            context: Retrieved context documents
            history: Chat history
            system_prompt: System prompt

        Returns:
            Generated answer
        """
        # Build context string
        context_str = "\n\n".join([
            f"[Source {i+1}] {doc.get('content', '')}"
            for i, doc in enumerate(context)
        ])

        # Build history string
        history_str = ""
        if history:
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[-5:]  # Last 5 messages
            ])

        # Build prompt
        prompt = f"""Based on the following context and chat history, answer the user's query.

Context:
{context_str}

Chat History:
{history_str}

User Query: {query}

Please provide a detailed and accurate answer based on the context. If the context doesn't contain enough information, say so."""

        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
