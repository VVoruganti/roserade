import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import time
import logging
from ..models.config import OllamaConfig


class OllamaEmbedder:
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.base_url = config.host.rstrip('/')
        self.model = config.embedding_model
        self.timeout = config.timeout
        self.logger = logging.getLogger(__name__)

    async def check_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['name'] for model in data.get('models', [])]
                    return []
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return []

    async def check_model_available(self) -> bool:
        """Check if the configured model is available."""
        available_models = await self.get_available_models()
        return any(self.model in model_name for model_name in available_models)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        payload = {
            "model": self.model,
            "prompt": text,
            "options": {
                "temperature": 0.0,
                "seed": 42
            }
        }

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('embedding', [])
                    else:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to connect to Ollama: {e}")

    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        if not texts:
            return []

        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await self._process_batch(batch)
            results.extend(batch_results)
            
            # Small delay to avoid overwhelming the server
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return results

    async def _process_batch(self, texts: List[str]) -> List[List[float]]:
        """Process a single batch of texts."""
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def generate_embeddings_with_retry(
        self, 
        texts: List[str], 
        max_retries: int = 3, 
        retry_delay: float = 1.0
    ) -> List[List[float]]:
        """Generate embeddings with retry logic."""
        for attempt in range(max_retries):
            try:
                return await self.generate_embeddings_batch(texts)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    def sync_generate_embedding(self, text: str) -> List[float]:
        """Synchronous wrapper for single embedding generation."""
        return asyncio.run(self.generate_embedding(text))

    def sync_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Synchronous wrapper for batch embedding generation."""
        return asyncio.run(self.generate_embeddings_batch(texts))

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Model {self.model} not found"}
        except Exception as e:
            return {"error": str(e)}

    async def pull_model(self) -> Dict[str, Any]:
        """Pull the configured model if not available."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"status": "success", "message": f"Model {self.model} pulled successfully"}
                    else:
                        error_text = await response.text()
                        return {"status": "error", "message": error_text}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class EmbeddingStats:
    def __init__(self):
        self.total_texts = 0
        self.successful_embeddings = 0
        self.failed_embeddings = 0
        self.total_time = 0.0
        self.errors = []

    def add_success(self, processing_time: float):
        self.successful_embeddings += 1
        self.total_time += processing_time

    def add_failure(self, error: str):
        self.failed_embeddings += 1
        self.errors.append(error)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_texts": self.total_texts,
            "successful_embeddings": self.successful_embeddings,
            "failed_embeddings": self.failed_embeddings,
            "success_rate": self.successful_embeddings / max(self.total_texts, 1),
            "average_time_per_text": self.total_time / max(self.successful_embeddings, 1),
            "errors": self.errors
        }