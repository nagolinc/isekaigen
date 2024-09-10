import json
import os

import anthropic


client = anthropic.Anthropic()

def chat(
    input_text,
    system_prompt="do your best",
    history=None,
    json_mode=False,
    max_history=8,
    verbose=False,
    model="claude-3-5-sonnet-20240620",
    #model="claude-3-haiku-20240307",
):

    if history is None:
        history = []
    else:
        #make sure we override system prompt (it is the content of the first message)
        #history[0] = {"role": "system", "content": system_prompt}
        pass #system prompt is now in the model

    if json_mode:
        #response_format = "json_object"
        prefill="{"
    else:
        #response_format = "text"
        prefill=""

    if len(history) > max_history:
        history = history[-max_history:]
    
    messages = history + [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": input_text
                }
            ]
        }
    ]
    
    
    if json_mode:
        messages+=[
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "{"
                }
            ]
        }
    ]
    
    
    if verbose:
        print("\n\nMESSAGES: >>>", messages)
    
    '''
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": response_format},
        max_tokens=4096,
    )
    '''
    message = client.messages.create(
    model=model,
    max_tokens=4000,
    temperature=0,
    system=system_prompt,
    messages=messages
    )
        
    

    #output_text = response.choices[0].message.content
    output_text = prefill+message.content[0].text

    new_history = history + [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": input_text
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": output_text
                }
            ]
        }
    ]

    return output_text, new_history
