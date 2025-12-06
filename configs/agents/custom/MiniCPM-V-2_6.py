from lmdeploy import (ChatTemplateConfig, GenerationConfig,
                      TurbomindEngineConfig)

lmm_agent = dict(
    name='MiniCPM-V-2_6',
    agent='lmdeploy_single',
    chat_template=None,
    model='openbmb/MiniCPM-V-2_6',
    backend_config=TurbomindEngineConfig(session_len=8192),
    general_config=GenerationConfig(max_new_tokens=4096, top_p=0.8),
)
