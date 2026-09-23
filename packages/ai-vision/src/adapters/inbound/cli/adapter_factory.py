"""Shared LIVE/MOCK adapter selection, used by both the CLI and the web inbound adapters."""
from __future__ import annotations

import os
from dataclasses import dataclass

from src.application.ports.outbound.image_generator_port import ImageGeneratorPort
from src.application.ports.outbound.image_processor_port import ImageProcessorPort
from src.application.ports.outbound.llm_provider_port import LlmProviderPort
from src.application.ports.outbound.video_animator_port import VideoAnimatorPort
from src.adapters.outbound.mock_adapters import (
    MockImageGeneratorAdapter,
    MockImageProcessorAdapter,
    MockLlmAdapter,
    MockVideoAnimatorAdapter,
)


@dataclass
class AdapterBundle:
    llm_provider: LlmProviderPort
    image_processor: ImageProcessorPort
    image_gen: ImageGeneratorPort
    video_anim: VideoAnimatorPort
    is_live: bool


def build_adapters(force_mock: bool = False) -> AdapterBundle:
    """Selects LIVE (Gemini) or MOCK outbound adapters.

    LIVE requires GEMINI_API_KEY to be set and force_mock to be False. If the Gemini
    adapters fail to initialize, silently falls back to MOCK — same behavior as the
    original inline selection in the CLI pipeline, kept identical here so the CLI and
    the web adapter never diverge.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    is_live = bool(gemini_key and not force_mock)

    if is_live:
        try:
            from src.adapters.outbound.gemini_llm_adapter import GeminiLlmAdapter
            from src.adapters.outbound.gemini_image_generator import GeminiImageGeneratorAdapter

            print("🔑 Chave GEMINI_API_KEY carregada com sucesso!")
            print("🎨 Adaptador Gemini Visual (gemini-2.5-flash-image) ativado para geração de cenas!")
            return AdapterBundle(
                llm_provider=GeminiLlmAdapter(),
                image_processor=MockImageProcessorAdapter(),
                image_gen=GeminiImageGeneratorAdapter(),
                video_anim=MockVideoAnimatorAdapter(),
                is_live=True,
            )
        except Exception as e:
            print(f"⚠️ Erro ao inicializar adaptadores Gemini ({e}). Alternando para mock.")
            return AdapterBundle(
                llm_provider=MockLlmAdapter(),
                image_processor=MockImageProcessorAdapter(),
                image_gen=MockImageGeneratorAdapter(),
                video_anim=MockVideoAnimatorAdapter(),
                is_live=False,
            )

    if not gemini_key:
        print("💡 Dica: Configure sua chave no arquivo .env para executar em modo LIVE.")

    return AdapterBundle(
        llm_provider=MockLlmAdapter(),
        image_processor=MockImageProcessorAdapter(),
        image_gen=MockImageGeneratorAdapter(),
        video_anim=MockVideoAnimatorAdapter(),
        is_live=False,
    )
