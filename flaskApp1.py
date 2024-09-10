from chat_openai import chat as chatJ
from chat_openai import chat
#from chat_openai4 import chat
#from chat_anthropic import chat
#from chat_deepseek import chat
#from chat_openrouter import chat#doesn't seem to work (nous returns noting, llama3 ignores json mode)
#from chat_fireworks import chat#meh (405b is better, but $$$)
#from chat_gemini import chat#something wrong with json mode

from comfy import generate_comfy
from generation_api import generate_tts, generate_image
import json
import concurrent.futures
import threading
import queue
import time
import datetime

import dataset

db=dataset.connect("sqlite:///story.db")

system_prompt_generate_allies=open("system_prompt_generate_allies.txt", "r").read()


def do_generate_image(text_to_image_caption):
    if args.use_comfy:
        image_filename=generate_comfy(text_to_image_caption,width=args.image_size[0],height=args.image_size[1],yaml_file=args.comfy_yaml)
    else:
        image_filename=generate_image(text_to_image_caption)
    return image_filename


def make_story(story_intro, num_episodes=None,history=None):
    
    #generate unique id {datetime}-{story_intro}
    #remove anything not a-zA-Z0-9
    story_intro_abc=re.sub(r'[^a-zA-Z0-9]', '_', story_intro)[:50]
    formatted_datetime=datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    story_id=f"{formatted_datetime}-{story_intro_abc}"
    
    story_counter=0
    
    
    
    if num_episodes is None:
        num_episodes=args.num_episodes
        
        
    #generate title,author
    instructions='''
    generate a title and author for the given story.
    return your response as JSON formatted like so
    {
        "title":"The story of the magic sword",
        "author":"John Doe"
    }
    
    '''
    _title,_=chatJ(story_intro,system_prompt=instructions,json_mode=True)
    print(_)
    title=json.loads(_title)
    prompt=f'generate a movie title screen for a movie with title "{title["title"]}" and author "{title["author"]}"'
    image=do_generate_image(prompt)
    
    
    result = {
            "text": title["title"]+" by "+title["author"],
            "prompt": prompt,
            "image": image,
            "audio": "/static/silence.wav",
            "music": "/static/loading.mp3",
            "story_id": story_id,
            "story_counter": story_counter,
        }
    story_counter+=1
    
    #save to db
    db["stories"].insert(result)
    
    yield result
        
        
    if args.generate_items:
    

        magicItems_instruction=f"""
        
        You are making an isekai based on the idea {story_intro}.

        Generate a list of {args.num_items} weapons/magic items/abilities/treausres that could be found.

        The items should gradually increase in power from common items (something similar to a rusty sword or a wooden stick) to legendary (something like the death note or a nuclear bomb).

        """

        print("generating magic items")

        items,history = chat(magicItems_instruction,system_prompt=system_prompt_isekai,history=history)

        print("generated magic items",items)

        enemies_instruction=f"""
        
        You are making an isekai based on the idea {story_intro}.

        Generate a list of {args.num_items} enemies that could be encountered.

        The enemies should gradually increase in power from common enemies (something similar in danger to a rat or a spider) to legendary (something like a god or a demon).
        """
        
        print("generating enemies")

        enemies,history = chat(enemies_instruction,system_prompt=system_prompt_isekai,history=history)

        print("generated enemies",enemies)
        
        allies_instruction=system_prompt_generate_allies.format(story_intro=story_intro,num_items=args.num_items)
        
        print("generating allies")

        allies,history = chat(allies_instruction,system_prompt=system_prompt_isekai,history=history)

        print("generated allies",allies)

        #locations
        locations_instruction=f"""
        
        You are making an isekai based on the idea {story_intro}.
        
        Generate a list of {args.num_items} locations that the main character could visit.

        The locations should gradually increase in spectacle from common locations (somewhere ordinary like a forest or village) to legendary (something like a pocket dimension or the divine plane).
        """
        
        print("generating locations")

        locations,history = chat(locations_instruction,system_prompt=system_prompt_isekai,history=history)
        
        print("generated locations",locations,"history len",len(history))


    #episodes
    
    episodes_instruction =f"you are making a story based on the idea {story_intro}."

    episodes_instruction+=f"Now generate a list of episodes for the story.  Try to aim for about {num_episodes} episodes."
    
    system_prompt_generateEpisodes=open(args.system_prompt_generateEpisodes, "r").read()
    
    episodes_instruction+="\n"+system_prompt_generateEpisodes
    
    def nlen(l):
        if l is None:
            return 0
        return len(l)
    
    print("generating episodes","history len",nlen(history))

    episodes_text,history = chat(episodes_instruction,system_prompt=system_prompt_generateEpisodes,history=history)
    print(episodes_text)

    system_prompt_jsonEpisodes=open("system_prompt_jsonEpisodes.txt", "r").read()
    
    print("converting episodes to JSON")

    jsonEpisodes,_ = chatJ(episodes_text,system_prompt=system_prompt_jsonEpisodes,json_mode=True)#discard the history for this one, doesn't matter
    print("jsonEpisodes",jsonEpisodes,"history len",len(history))
    

    episodesData=json.loads(jsonEpisodes)
    
    episodes=episodesData["episodes"]
    
    characters={}
    character_info=""
    
    #extra_info="This is the first episode, so be sure to introduce the main character and explain how they got isekai'd.  Also, introduce the main plot and the main antagonist."
    extra_info="This is the first episode, so be sure to introduce the main character and explain the main plot."

    # Setup an initial history
    # Initial script and history setup
    script_data, history, json_history = generateScript(episodes[0], story_intro+extra_info,character_info, history)
    
    #add script_data["characters"] to characters
    if "characters" in script_data:
        for character in script_data["characters"]:
            if  "name" in character and  character["name"] not in characters:
                print("ADDING CHARACTER",character["name"])
                characters[character["name"]]=character
                character_info+=f"\n{character['name']}: {character['description']}"
    

    # Queue for communication between threads
    script_queue = queue.Queue()
    shot_queue = queue.Queue()

    # Start processing shots for the first script in a new thread
    shot_thread = threading.Thread(target=process_shots, args=(script_data, shot_queue))
    shot_thread.start()

    # Process remaining episodes
    for i in range(1, len(episodes)):
        
        extra_info="""
IMPORTANT: include a line at the beginning of the screenplay in which the character describes how they transitioned from the previous scene.
For example, if in scene 1, the characters were in the dragon's cave and in scene 2 they are at the castle, the main character might say
"I can't believe we made it out of the dragon's cave and into the castle.  I hope we can find the princess before it's too late."
This FIRST LINE of DIALOGUE must BOTH explicity describe what happened in the last scene, and HOW it relates to the current action.
"""
        
        if i == len(episodes) - 1:
            extra_info += "This is the final episode, so be sure to wrap things up.  Keep in mind, the story need not have a happy ending."
        else:
            extra_info += "Make sure to maintain continuity with the previous episodes and advance the main plot."
    
        # Handle script generation in a separate thread
        #if i<len(episodes):
        script_thread = threading.Thread(target=generateScript_thread, args=(episodes[i], story_intro + extra_info, character_info, history, json_history, script_queue))
        script_thread.start()
    
        # Yield shots while waiting for the next script
        while True:
            try:
                shot = shot_queue.get(timeout=0.1)
                #add story_id,story_counter
                shot["story_id"]=story_id
                shot["story_counter"]=story_counter
                story_counter+=1
                db["stories"].insert(shot)
                
                yield shot
            except queue.Empty:
                if not shot_thread.is_alive():
                    break
    
        #if i<len(episodes):
        # Wait for the next script to be ready
        script_thread.join()
        script_data, history, json_history = script_queue.get()  # Ensure you unpack the queue item correctly
    
        # Add script_data["characters"] to characters
        if "characters" in script_data:
            for character in script_data["characters"]:
                if "name" in character and character["name"] not in characters:
                    print("ADDING CHARACTER", character["name"])
                    characters[character["name"]] = character
                    character_info += f"\n{character['name']}: {character['description']}"
    
        # Start processing shots for the new script
        if shot_thread.is_alive():
            shot_thread.join()  # Ensure previous shot processing is complete
        shot_thread = threading.Thread(target=process_shots, args=(script_data, shot_queue))
        shot_thread.start()

    # Ensure the last shot processing thread has completed
    #shot_thread.join()
    while True:
        try:
            shot = shot_queue.get(timeout=0.1)
            #add story_id,story_counter
            shot["story_id"]=story_id
            shot["story_counter"]=story_counter
            story_counter+=1
            db["stories"].insert(shot)           
            
            yield shot
        except queue.Empty:
            if not shot_thread.is_alive():
                break
        
    # Start processing shots for the new script
    if shot_thread.is_alive():
        shot_thread.join()

    #yield the end
    end= {
        "text": "The end",
        "prompt": "the end",
        "image": the_end_img,
        "audio": the_end_audio,
        "duration": the_end_duration,
        'ended': True,
        "story_id": story_id,
        "story_counter": story_counter,
    }
    db["stories"].insert(end)
    yield end
    
    
#get saved stories
def get_stories():
    story_ids=db["stories"].distinct("story_id")
    #fetch first shot for each story
    stories=[]
    for _story_id in story_ids:
        story_id=_story_id['story_id']
        story=db["stories"].find_one(story_id=story_id)
        if story is not None:
            stories.append(story  )
    return stories    
    
    

def generateScript_thread(episode, story_intro, character_info, history, json_history, output_queue):
    script_data, new_history, new_json_history = generateScript(episode, story_intro,character_info, history, json_history)
    output_queue.put((script_data, new_history,new_json_history))  # Put script data and updated history into the queue

def process_shots(script_data, shot_queue):
    for shot in generateShots(script_data):
        shot_queue.put(shot)  # Process each shot and put it into the queue
        
        
system_prompt_write_script=open("system_prompt_write_script.txt", "r").read()        
                
def generateScript(episode,story_intro,character_info,history,json_history=None):
    instructions=f"""
    
    You are writing episodes for an story based on the idea {story_intro}.
    
    As a reminder, the story thus far has included:
    {character_info}
    
    Write a script for episode {episode["title"]} of the story.

    With description {episode["description"]}.
    
    Reminder: Avoid cliches like 'we worked together' 'we don't need to be enemies'
    INSTEAD: Characters should be driven by powerful internal motivations such as shame, greed and resentment that are often violent, chaotic, and self-destructive.
    Reminder: None of the chracters should be 'good guys', even when they do good things, it should be for selfish reasons.
    Reminder: write the screenplay in natural language with a mix of dialogue and action.
    Reminder: When the characters encounter a new location, character, or item, one of them should describe it's physical appearance.
    Reminder: Make sure to use the characters' unique abilities and items, especially the main characcter's unique trais.
    Reminder: The script should begin with a list of characters including their names and physical descriptions.
        
    """
    
    print("generating script for",episode["title"],"with character info",character_info,"history len",len(history))
            
    script,history = chat(instructions,system_prompt=system_prompt_write_script,history=history)
    
    print("generated script>>>\n",script)
    
    reminder="""
    Reminder: Follow the input SCRIPT AS CLOSELY AS POSSIBLE.  That means *each* line in the script should have a corresponding script in your JSON
    Reminder: Make sure to include ALL characters at the beginning of the json in the "characters" field.  Each script has AT LEAST 3 characters.
    Reminder: Avoid references to technical aspects of the script like "scene" "camera" or "episode"
    """
    
    if args.extra_episode_to_json_reminders:
        reminder+=open(args.extra_episode_to_json_reminders).read()
        print('json reminder',reminder)
    
    
    
    #convert script to JSON
    print("converting script to JSON")
    jsonScript,jsonHistory = chatJ(character_info+script+reminder,
                                  system_prompt=system_prompt_episodeToJson,
                                  history=json_history,
                                  json_mode=True)
    print("jsonScript",jsonScript)
    
    scriptData=json.loads(jsonScript)                
    
    return scriptData,history, jsonHistory



import concurrent.futures

def generateShots(scriptData):
    for shot in scriptData["shots"]:
        print("generating shot", shot)
        
        text_to_image_caption = args.promptPrefix+shot["caption"] + args.promptSuffix
        
        char_dict = {}
        if "characters" in scriptData:
            # Convert from a [{name:, description:}] to a dictionary
            for character in scriptData["characters"]:
                if "name" in character:
                    char_dict[character["name"]] = character["description"]
        
        # Add character info to shot if it exists
        if "characters" in shot:
            for character in shot["characters"]:
                if isinstance(character, str) and character in char_dict:
                    text_to_image_caption += "\n" + char_dict[character]
        
        # Add setting
        if "setting" in shot:
            text_to_image_caption += "\n" + shot["setting"]
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the image generation task
            if args.use_comfy:
                image_future = executor.submit(generate_comfy, text_to_image_caption, width=args.image_size[0], height=args.image_size[1], yaml_file=args.comfy_yaml)
            else:
                image_future = executor.submit(generate_image, text_to_image_caption)
                
                
            speaker_name=""
            speaker_line=""
            speaker_gender=""
            
            # Determine the TTS task
            if "dialogue" in shot and "text" in shot["dialogue"] and "gender" in shot["dialogue"] and "speaker" in shot["dialogue"]:
                tts_line = shot["dialogue"]["text"]
                
                #convert all caps to capital case
                tts_line=convert_all_caps_to_capital_case(tts_line)
                
                if "cue" in shot["dialogue"]:
                    cue="("+shot["dialogue"]["cue"]+")"
                else:
                    cue=""
                
                line = shot["dialogue"]["speaker"] + cue+": " + shot["dialogue"]["text"]
                
                speaker_name=shot["dialogue"]["speaker"]
                speaker_line=shot["dialogue"]["text"]
                speaker_gender=shot["dialogue"]["gender"]
                
                # Convert speaker to a pseudorandom voice_id
                voice_id = hash(shot["dialogue"]["speaker"].lower())% 1000 + args.voice_offset
                
                if len(tts_line.strip())==0:
                    continue
                
                audio_future = executor.submit(generate_tts, tts_line, gender=shot["dialogue"]["gender"], voice_id=voice_id)
            elif "narration" in shot:
                line = shot["narration"]
                
                speaker_name="Narrator"
                speaker_line=shot["narration"]
                speaker_gender="female"
                
                audio_future = executor.submit(generate_tts, line)
            else:
                line = shot["caption"]
                audio_future = executor.submit(generate_tts, line)
            
            # Wait for both tasks to complete
            image_filename = image_future.result()
            audio = audio_future.result()
        
        yield {
            "text": line,
            "prompt": shot["caption"],
            "image": image_filename,
            "audio": audio,
            "speaker_name": speaker_name,
            "speaker_line": speaker_line,
            "speaker_gender":speaker_gender
        }



def convert_all_caps_to_capital_case(text):
    def capitalize_if_all_caps(word):
        if word.isupper():
            return word.capitalize()
        return word

    words = text.split()
    converted_words = [capitalize_if_all_caps(word) for word in words]
    return ' '.join(converted_words)

        
import argparse
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

import threading

# Create a lock object
chat_lock = threading.Lock()

story_gen=None

#add an endpoint to set story_gen given a story_intro
@app.route("/set_story", methods=["POST"])
def set_story():
    global story_gen, story_history, characters_history, image_history
    print('setting story', request.json["story_intro"])
    num_episodes = request.json.get("num_episodes", None)
    print("num_episodes",num_episodes)
    story_history = None
    characters_history = None
    image_history = None
    story_gen = make_story(request.json["story_intro"], num_episodes)
    #story_gen = make_story()
    return jsonify({"status": "success"})

the_end_img="/static/the_end.png"
the_end_audio="/static/the_end.wav"
the_end_duration=2.0


@app.route("/next_result", methods=["GET"])
def next_result():
    try:
        result = next(story_gen)
    except StopIteration:
        
        result = {
            "text": "The end",
            "prompt": "the end",
            "image": the_end_img,
            "audio": the_end_audio,
            "duration": the_end_duration,
            'ended': True
        }
    return jsonify(result)


@app.route("/")
def index():
    return render_template("storyApp.html")

#/list (renders template list_stories.html)
@app.route("/list", methods=["GET"])
def list_stories():
    return render_template("list_stories.html")

import random

import re
def remove_all_caps(text):
    def capitalize_word(match):
        word = match.group(0)
        if word.isupper():
            return word.capitalize()
        return word

    # Use regex to find all words and apply the capitalize_word function
    return re.sub(r'\b[A-Z]+\b', capitalize_word, text)


def random_plot(samples=None):
    keywords=[]
    for filename in args.wordlists:
        if filename.endswith(".txt"):
            lines=[line.strip() for line in open(filename).readlines()]
        else:
            lines=[filename]
        keywords+=[random.choice(lines)]
        
    keyword_string=" ".join(keywords)
    
    
    if samples is None:
        samples = open(args.samplePlots).read()
    random_plot_system_prompt = open("random_plot_system_prompt.txt").read()
    
    result,history= chat(keyword_string, system_prompt=random_plot_system_prompt+samples,json_mode=True)
    
    print(history)
    
    print(result)
    return json.loads(result)["plot"]




#/random_plot
@app.route("/random_plot", methods=["GET"])
def show_random_plot():
    return jsonify({"tagline": random_plot()})


#/get_stories
@app.route("/get_stories", methods=["GET"])
def show_stories():
    stories=get_stories()
    return jsonify(stories)


#need an endpoint that allows us to fetch the shot with story_id and story_counter
@app.route("/get_shot", methods=["POST"])
def get_shot():
    story_id=request.json["story_id"]
    story_counter=request.json["story_counter"]
    shot=db["stories"].find_one(story_id=story_id,story_counter=story_counter)
    print('about to die',shot)
    return jsonify(shot)

#/play_story needs to render templates/play_saved_story.html
@app.route("/play_story", methods=["GET"])
def play_story():
    return render_template("play_saved_story.html")        
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    #--image_size, default [512,512], nargs=2, type=int (width,height)
    parser.add_argument("--image_size", default=[512,512], nargs=2, type=int, help="Image size")
    
    #--voice_offset, default 0, type=int
    parser.add_argument("--voice_offset", default=0, type=int, help="Voice offset")
    
    
    #--num_episodes (default 12)
    parser.add_argument("--num_episodes", default=12, type=int, help="Number of episodes")
    
    #--num_items (default 20)
    parser.add_argument("--num_items", default=20, type=int, help="Number of items")
    
    #--promptSuffix default ", live action film still, 4k, cinematic, detailed, high resolution"
    parser.add_argument("--promptSuffix", default=", cosplay, high resolution photograph, dramatic lighting, 4k, detailed", type=str, help="Prompt suffix")
    
    #--promptPrefix, default "live action film still "
    parser.add_argument("--promptPrefix", default="live action film still, ", type=str, help="Prompt prefix")
    
    #--wordlists (1 or more filenames, default "..\words\diverseWords.txt")
    parser.add_argument("--wordlists", nargs="+", default=["..\words\diverseWords.txt"], help="Wordlists")
    
    #--use_comfy (store_true)
    parser.add_argument("--use_comfy", action="store_true", help="Use comfy")
    
    #--comfy_yaml
    parser.add_argument("--comfy_yaml", type=str, default="comfy.yaml", help="Comfy yaml")
    
    
    #--generate_items (store_true)
    parser.add_argument("--generate_items", action="store_true", help="Generate items")
    
    #--samplePlots "sample_anime_plots.txt"
    parser.add_argument("--samplePlots", default="sample_anime_plots.txt", help="Sample plots")
    
    #system_prompt_isekai=open("system_prompt_iskeai.txt", "r").read()
    parser.add_argument("--system_prompt_isekai", type=str, default="system_prompt_iskeai.txt", help="Isekai prompt")
    
    #--system_prompt_generateEpisodes "system_prompt_generateEpisodes.txt"
    parser.add_argument("--system_prompt_generateEpisodes", default="system_prompt_generateEpisodes.txt", help="Generate episodes prompt")

    #"system_prompt_episodeToJson.txt"
    parser.add_argument("--system_prompt_episodeToJson", default="system_prompt_episodeToJson.txt", help="Instructions for turning a screenplay into to JSON format")
    
    #--extra_episode_to_json_reminders (default none)
    parser.add_argument("--extra_episode_to_json_reminders", default=None, type=str, help="Extra episode to JSON reminders")
    
    
    
    args = parser.parse_args()
    
    system_prompt_episodeToJson=open(args.system_prompt_episodeToJson, "r").read()

    
    system_prompt_generateEpisodes=open(args.system_prompt_generateEpisodes, "r").read()
    
    system_prompt_isekai=open(args.system_prompt_isekai, "r").read()
    
    
    #generate test image
    if args.use_comfy:
        generate_comfy("A knight fights a dragon"+args.promptSuffix ,width=args.image_size[0],height=args.image_size[1], yaml_file=args.comfy_yaml)
    
    app.run(debug=True, port=5000, use_reloader=False)

