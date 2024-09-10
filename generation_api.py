import fal_client
import base64
from io import BytesIO
from PIL import Image

import requests

def generate_image(prompt, dest="static/samples", **kwargs):

    handler = fal_client.submit(
        #"fal-ai/fast-turbo-diffusion",
        #"fal-ai/hyper-sdxl",
        "fal-ai/flux/schnell",
        arguments={
            "prompt": prompt,
            "image_size":"landscape_16_9",
            #"num_inference_steps": 8,
            "enable_safety_checker": False,
        },
    )

    log_index = 0
    for event in handler.iter_events():
        #print('about to die',event)
        if isinstance(event, fal_client.InProgress):
            if event.logs is None:
                continue
            new_logs = event.logs[log_index:]
            for log in new_logs:
                if log is not None:
                    print("log",log["message"])
                    
                        
            log_index = len(event.logs)

    result = handler.get()
    
    
    
    
    print("result",result)
    
    # Extracting the image URL
    image_url = result['images'][0]['url']

    # Downloading the image
    response = requests.get(image_url)
    image_data = response.content

    # Creating a PIL image from the downloaded image data
    image = Image.open(BytesIO(image_data))
    
    #save the image to the samples directory (with a unique name)
    filename="img_"+generate_random_string()+".png"
    fullPath = dest + "/" + filename
    image.save(fullPath)
    
    #if fullPath doesn't start with "/", add it
    if not fullPath.startswith("/"):
        fullPath="/"+fullPath
    
    return fullPath
    
    #return image

import secrets
import string

def generate_random_string(length=16):
    # Generate a random string of a-z, A-Z, 0-9
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def upscale_image(image,imageDescription,width,height,**kwargs):
    # Upscale the image
    image = image.resize((width, height), Image.LANCZOS)
    return image


import re
import datetime
import requests


#read ELEVEN_KEY from os.environ
import os
ELEVEN_KEY = os.environ.get('ELEVEN_KEY')

def generate_tts0(
    text, speaker="static/voices/femalevoice3.wav", savePath="static/samples/"
):
    
    print("doing tts",text)

    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.0,
            "similarity_boost": 0.0,
            "style": 0.0,
            "use_speaker_boost": False
        },
        "seed": 123,
    }
    headers = {"Content-Type": "application/json",
               "xi-api-key": ELEVEN_KEY}

    response = requests.request("POST", url, json=payload, headers=headers)
    
    print("response",response.status_code)
    
    if response.status_code != 200:
        print("error",response.text)
        return None



    #print(response.text)
    
    ftext = re.sub(r"[^a-z0-9]", "_", text.lower())[:50]
    filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{ftext}.wav"

    fullPath = savePath + filename

    with open(fullPath, "wb") as f:
        f.write(response.content)

    print("done")
    return fullPath


from google.cloud import texttospeech

# Create a client
client = texttospeech.TextToSpeechClient()

def generate_tts(text, savePath='static/samples/', gender="female", voice_id=0, **kwargs):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    if gender=="male":
        voices = [
                "en-US-Casual-K",
                "en-US-Journey-D",
                "en-US-Neural2-A",
                "en-US-Neural2-D",
                "en-US-Neural2-I",
                "en-US-Neural2-J",
                "en-US-News-N",
                "en-US-Polyglot-1"
            ]
    else:
        voices = [
                "en-US-Journey-O",#want this one first (narrator voice)
                "en-US-Journey-F",                
                "en-US-Neural2-C",
                "en-US-Neural2-E",
                "en-US-Neural2-F",
                "en-US-Neural2-G",
                "en-US-Neural2-H",
                #"en-US-News-K",#don't like this one
                #"en-US-News-L"
            ]
        
    name = voices[voice_id%len(voices)]

    # Build the voice request, specifying the language code and the name of the voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=name,
    )

    # Select the type of audio encoding
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # Build the request
    request = texttospeech.SynthesizeSpeechRequest(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    #filename
    ftext = re.sub(r"[^a-z0-9]", "_", text.lower())[:50]
    filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{ftext}.wav"
    
    fullPath = savePath + filename
    
    # Perform the text-to-speech request on the text input with the selected voice parameters and audio encoding.
    response = client.synthesize_speech(request=request)

    # Write the response to the output file.
    with open(fullPath, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file ',fullPath)
        
    return fullPath



def setup(**kwargs):
    pass