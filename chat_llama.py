from llama_cpp.llama import Llama, LlamaGrammar

#llama_model=r"D:\lmstudio\TheBloke\Chronomaid-Storytelling-13B-GGUF\chronomaid-storytelling-13b.Q4_K_M.gguf"

llama_model=r"d:\lmstudio\Caerbannog\Qwen2.5-LumenReplete-14B-Q4_K_M-GGUF\qwen2.5-lumenreplete-14b-q4_k_m.gguf"

#llama_model=r"D:\lmstudio\RichardErkhov\AiCloser_-_Qwen2.5-32B-AGI-gguf\Qwen2.5-32B-AGI.IQ3_M.gguf"

#llama_model=r"D:\lmstudio\mradermacher\Code-Llama-Bagel-8B-i1-GGUF\Code-Llama-Bagel-8B.i1-Q6_K.gguf"

n_gpu_layers=99

llm = Llama(llama_model, n_ctx=8162, n_gpu_layers=n_gpu_layers)



cfg = {
                "genTextAmount_min": 30,
                "genTextAmount_max": 100,
                "no_repeat_ngram_size": 16,
                "repetition_penalty": 1.0,
                "MIN_ABC": 4,
                "num_beams": 1,
                "temperature": 1.0,
                "MAX_DEPTH": 5,
            }

def chat(
    input_text,
    system_prompt="do your best",
    history=None,
    json_mode=False,
    max_history=8,
    verbose=False,
    min_new_tokens=32,
    max_new_tokens=1024,
):
    
    
    if history is None:
        history=[]
        
        
    if json_mode:
        response_format={
            "type": "json_object",
        }
    else:
        response_format={
            "type": "text",
        }
        
    #check if role for history[0] is system
    if len(history)>0:
        if history[0]['role'] == 'system':
            history[0]['content'] = system_prompt
        else:
            history.insert(0, {"role": "system", "content": system_prompt})
    else:
        history.insert(0, {"role": "system", "content": system_prompt})
        
    #add user input to history
    history+=[{"role":"user", "content":input_text}]
    
    response=llm.create_chat_completion(
        messages = history,
        response_format=response_format
    )
    
    
    result_text = response["choices"][0]['message']['content']
    
    #add the result to history
    history+=[{"role":"assistant", "content":result_text}]
    
    return result_text, history