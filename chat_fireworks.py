import os

api_key = os.environ["FIREWORKS_AI_KEY"]

import openai

client = openai.OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=api_key,
)


def chat(input_text, system_prompt="do your best", history=None, json_mode=False,
         #model="accounts/fireworks/models/llama-v3-8b-instruct",
         #model ="accounts/fireworks/models/llama-v3p1-70b-instruct",
         model="accounts/fireworks/models/llama-v3p1-405b-instruct",
         #model="accounts/fireworks/models/mixtral-8x22b-instruct",#not good
         max_history=8):

    if history is None:
        history = [{"role": "system", "content": system_prompt}]
    else:
        # make sure we override system prompt (it is the content of the first message)
        history[0] = {"role": "system", "content": system_prompt}
        
        
    if len(history)>max_history:
        history=history[0:1]+history[-max_history:]
        
    messages = history + [{"role": "user", "content": input_text}]

    if json_mode:
        response_format = "json_object"
    else:
        response_format = "text"


    
    chat_completion = client.chat.completions.create(
        model=model,
        max_tokens=16384,
        response_format={"type": response_format},
        messages=messages,
    )
    output_text = chat_completion.choices[0].message.content

    new_history = messages + [{"role": "assistant", "content": output_text}]

    return output_text, new_history
