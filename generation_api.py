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

male_voices_hosted=open("d:/img/voices/male_voices_uploaded.txt").readlines()
male_voices_hosted=[line.strip() for line in male_voices_hosted if len(line.strip())]
female_voices_hosted=open("d:/img/voices/female_voices_uploaded.txt").readlines()
female_voices_hosted=[line.strip() for line in female_voices_hosted if len(line.strip())]

male_transcripts=open("d:/img/voices/male_transcripts.txt").readlines()
female_transcripts=open("d:/img/voices/female_transcripts.txt").readlines()


import fal_client
import os
import requests


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])


def generate_tts_fal(input_text,voice_id=0,gender="female",save_path = "./static/samples"):
    if gender=="male":
        index=voice_id%len(male_voices_hosted)
        voice_file=male_voices_hosted[index]
        transcript=male_transcripts[index]
    else:
        index=voice_id%len(female_voices_hosted)
        voice_file=female_voices_hosted[index]
        transcript=female_transcripts[index]
        
        
    print("using voice",voice_file)


    result = fal_client.subscribe(
        "fal-ai/f5-tts",
        arguments={
            "gen_text": input_text,
            "ref_audio_url": voice_file,
            "ref_text": transcript,
            "model_type": "F5-TTS",
            "remove_silence": True
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    print(result)
    
    url=result['audio_url']['url']
    
    filename=url.split("/")[-1]
    print('saving file',filename,'in',save_path)
    

    # Create the directory if it doesn't exist
    os.makedirs(save_path, exist_ok=True)

    # Full path for the saved file
    file_path = os.path.join(save_path, filename)

    # Download the file and save it
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"File downloaded and saved at {file_path}")
    else:
        print("Failed to download file:", response.status_code)
    
    return file_path



from fish_audio_sdk import Session, TTSRequest, ReferenceAudio

import os
fish_api_key=os.environ["FISH_TTS_API_KEY"]

session = Session(fish_api_key)

# Option 1: Using a reference_id
with open("output1.mp3", "wb") as f:
    for chunk in session.tts(TTSRequest(
        reference_id="e58b0d7efca34eb38d5c4985e378abcb",
        text="four score and seven years ago"
    )):
        f.write(chunk)

# Option 2: Using reference audio


import datetime
import random


import glob
male_voices=glob.glob("d:/img/voices/male/normal/*.wav")
female_voices=glob.glob("d:/img/voices/female/normal/*.wav")

def generate_filename(extension="mp3"):
    # Get the current datetime
    now = datetime.datetime.now()
    # Format the datetime as a string
    datetime_str = now.strftime("%Y%m%d%H%M%S")
    # Generate a random number
    random_number = random.randint(1000, 9999)
    # Combine the parts to create the filename
    filename = f"{datetime_str}-img-{random_number}.{extension}"
    return filename


from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os

def remove_silence(audio_path, silence_thresh=-40, min_silence_len=500, padding=200):
    # Load audio file
    audio = AudioSegment.from_file(audio_path)
    
    # Detect non-silent chunks
    nonsilent_chunks = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    
    # Combine non-silent chunks
    output_audio = AudioSegment.empty()
    for start, end in nonsilent_chunks:
        # Add a bit of padding if needed
        output_audio += audio[start - padding:end + padding]
    
    return output_audio



from pydub.silence import detect_silence

def trim_silence_end(audio_path, silence_threshold=-50.0, silence_duration=1000):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)
    
    # Detect silence (returns a list of [start, end] in ms)
    silence_regions = detect_silence(audio, min_silence_len=silence_duration, silence_thresh=silence_threshold)

    # If there's silence at the end, remove it
    if silence_regions and silence_regions[-1][1] == len(audio):
        end_of_audio = silence_regions[-1][0]
        trimmed_audio = audio[:end_of_audio]
    else:
        trimmed_audio = audio  # No silence detected at the end

    # Save the trimmed audio
    #trimmed_audio.export("trimmed_output.wav", format="wav")
    print("Silence trimmed and saved as 'trimmed_output.wav'.")
    return trimmed_audio




def tts_fish(input_text,voice_id=0,gender='female',save_path="static/samples/"):
    if gender=='male':
        voice=male_voices[voice_id%len(male_voices)]
    else:
        voice=female_voices[voice_id%len(female_voices)]
    txt_file=voice.replace(".wav","_transcript.txt")
    
    
    output_file=generate_filename()
    
    full_path=os.path.join(save_path,output_file)

    with open(voice, "rb") as audio_file:
        with open(full_path, "wb") as f:
            for chunk in session.tts(TTSRequest(
                text=input_text,
                references=[
                    ReferenceAudio(
                        audio=audio_file.read(),
                        text=open(txt_file).read(),
                    )
                ]
            )):
                f.write(chunk)
                
    #return full_path
    
    #now we need to remove silence
    #output_audio = remove_silence(full_path)
    output_audio=trim_silence_end(full_path)
    new_filename=full_path.replace(".mp3","_trimmed.mp3")
    output_audio.export(new_filename, format="mp3")
    
    return new_filename









def generate_filename(extension="mp3"):
    # Get the current datetime
    now = datetime.datetime.now()
    # Format the datetime as a string
    datetime_str = now.strftime("%Y%m%d%H%M%S")
    # Generate a random number
    random_number = random.randint(1000, 9999)
    # Combine the parts to create the filename
    filename = f"{datetime_str}-img-{random_number}.{extension}"
    return filename


import os
import requests
import datetime
import random

import torch
from scipy.io.wavfile import write

def save_audio(output, filename):
    # Move tensor to CPU if necessary and detach it from any computational graph
    audio_tensor = output.audio.cpu().detach().numpy()
    
    # The audio tensor may have a batch dimension, so squeeze if necessary
    audio_data = audio_tensor.squeeze()  # Shape will be (n_samples,)
    
    # Save the audio data to a file using scipy
    write(filename, output.sr, audio_data)


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])


def generate_tts_outer(input_text,voice_id=0,gender="female",save_path = "./static/samples"):
    from outetts.v0_1.interface import InterfaceHF, InterfaceGGUF    
    
    # Initialize the interface with the Hugging Face model
    interface_oute_tts = InterfaceHF("OuteAI/OuteTTS-0.1-350M")
    
    if gender=='male':
        voice=male_voices[voice_id%len(male_voices)]
    else:
        voice=female_voices[voice_id%len(female_voices)]
    txt_file=voice.replace(".wav","_transcript.txt")
        
    
    # Create a custom speaker from an audio file
    speaker = interface_oute_tts.create_speaker(
        voice,
        open(txt_file).read()
    )

    # Generate TTS with the custom voice
    output = interface_oute_tts.generate(
        text=input_text,
        speaker=speaker,
        temperature=0.1,
        repetition_penalty=1.1,
        max_lenght=4096
    )
    
    filename=generate_filename()
    
    full_path=os.path.join(save_path,filename)
    
    #return output
    save_audio(output,full_path)
    
    return full_path




def setup(**kwargs):
    pass