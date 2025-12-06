from lmdeploy import (ChatTemplateConfig, GenerationConfig,
                      TurbomindEngineConfig)

lmm_agent = dict(
    name='gemma-3-4b-it',
    agent='lmdeploy_single',
    chat_template=None,
    model='google/gemma-3-4b-it',
    backend_config=TurbomindEngineConfig(session_len=8192),
    general_config=GenerationConfig(max_new_tokens=4096, top_p=0.8),
)
