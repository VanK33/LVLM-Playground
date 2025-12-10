from lmdeploy import (ChatTemplateConfig, GenerationConfig,
                      TurbomindEngineConfig)

lmm_agent = dict(
    name='Fara-7B',
    agent='lmdeploy_single',
    chat_template=None,
    model='microsoft/Fara-7B',
    backend_config=TurbomindEngineConfig(session_len=8192),
    general_config=GenerationConfig(max_new_tokens=1024, top_p=0.8),
)
