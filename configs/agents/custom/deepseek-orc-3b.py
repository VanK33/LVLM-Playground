from lmdeploy import (ChatTemplateConfig, GenerationConfig,
                      TurbomindEngineConfig)

lmm_agent = dict(
    name='DeepSeek-OCR',
    agent='lmdeploy_single',
    chat_template=None,
    model='deepseek-ai/DeepSeek-OCR',
    backend_config=TurbomindEngineConfig(session_len=8192),
    general_config=GenerationConfig(max_new_tokens=1024, top_p=0.8),
)
