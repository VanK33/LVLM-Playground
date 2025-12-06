from lmdeploy import (ChatTemplateConfig, GenerationConfig,
                      TurbomindEngineConfig)

lmm_agent = dict(
    name='internvl3_5-8b-instruct',
    agent='lmdeploy_single',
    chat_template=ChatTemplateConfig('internvl-internlm3'),
    model='OpenGVLab/InternVL3_5-8B-Instruct',
    backend_config=TurbomindEngineConfig(session_len=8192),
    general_config=GenerationConfig(max_new_tokens=4096, top_p=0.8),
)