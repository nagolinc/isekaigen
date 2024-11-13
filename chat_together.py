import os
from together import Together
import json

client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))



def chat(
    input_text,
    system_prompt="do your best",
    history=None,
    json_mode=False,
    max_history=8,
    verbose=False,
):

    if history is None:
        history = [{"role": "system", "content": system_prompt}]
    else:
        #make sure we override system prompt (it is the content of the first message)
        history[0] = {"role": "system", "content": system_prompt}

    if json_mode:
        response_format = "json_object"
    else:
        response_format = "text"

    if len(history) > max_history:
        history = history[:1] + history[-max_history:]
    messages = history + [{"role": "user", "content": input_text}]
    
    
    if verbose:
        print("\n\nMESSAGES: >>>", messages)
    
    response = client.chat.completions.create(
        model="NousResearch/Hermes-3-Llama-3.1-405B-Turbo",
        messages=messages,
        #response_format={"type": response_format},
        max_tokens=4096,
    )

    output_text = response.choices[0].message.content

    new_history = messages + [
        #{"role": "user", "content": input_text},
        {"role": "assistant", "content": output_text},
    ]

    return output_text, new_history
