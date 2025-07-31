import openai 
from pydantic import BaseModel
import json

class NextPlayerActions(BaseModel):
    options: list[str]
    
class Scene(BaseModel):
    scene_description: str

client = openai.OpenAI()

scenes = []

def get_next_actions(scene, character_name):
        
    messages = [
        {"role": "system", "content": f"You are the dungeon master for a role-playing game. You'll be given the last scene, and you need to present the player, {character_name}, with several options for what to do next. Respond with JSON, given the following format: {{'options': ['option1', 'option2', 'option3']}}"},
        {"role": "user", "content": scene}
    ]

    response = client.responses.parse(
        model="gpt-4o",
        input=messages,
        text_format=NextPlayerActions,
    )

    return response.output_parsed.options


def generate_random_scene(character_name):
    messages = [
        {"role": "system", "content": f"You are the dungeon master for a role-playing game. You'll be given the character's name, and you need to generate a random scene for the character to start off the story. Respond with a single scene description."},
        {"role": "user", "content": character_name}
    ]
    
    response = client.responses.parse(
        model="gpt-4o",
        input=messages,
        text_format=Scene,
    )
    
    return response.output_parsed.scene_description


def get_player_choice(next_actions, scene, character_name):
    actions_as_numbered_list = "\n".join([f"{i+1}. {action}" for i, action in enumerate(next_actions)])
    prompt_player_for_action = f"{scene}\n\n{character_name}, you have the following options for what to do next:\n\n{actions_as_numbered_list}\n"
    reprompt = True
    while True:
        if reprompt:
            try:
                player_choice = int(input(prompt_player_for_action))
                return player_choice
            except ValueError:
                print("Please enter a valid number.")
                reprompt = True
        else:
            player_choice = int(input(prompt_player_for_action))
            reprompt = False
            
def get_next_scene(player_choice, next_actions, current_scene, character_name, summarized_story):
    messages = [
        {"role": "system", "content": f"You are the dungeon master for a role-playing game. The character's name is {character_name}, and the last scene was {current_scene}. The player chose {next_actions[player_choice - 1]}, and you need to respond with what happened, followed by the next scene. The story so far is: {summarized_story.story_summary}. A scene by scene summary of the story so far is: {summarized_story.scene_summaries}, and the characters introduced are: {summarized_story.characters_introduced}, the locations introduced are: {summarized_story.locations_introduced}, the objects introduced are: {summarized_story.objects_introduced}, the events introduced are: {summarized_story.events_introduced}, the relationships introduced are: {summarized_story.relationships_introduced}, the conflicts introduced are: {summarized_story.conflicts_introduced}, and the open threads are: {summarized_story.open_threads}. Prioritize suprise and challenging traditional story tropes. Keep scenes short, and give the player a lot of agency by keeping the story open ended and scenes small. The scene should be a single scene, not a series of scenes."},
        {"role": "user", "content": next_actions[player_choice - 1]}
    ]

    response = client.responses.parse(
        model="gpt-4o",
        input=messages,
        text_format=Scene,
    )

    return response.output_parsed.scene_description


def save_scenes(scenes):
    with open("scenes.json", "a") as f:
        json.dump(scenes, f)
        
class SummarizedStory(BaseModel):
    story_summary: str
    scene_summaries: list[str]
    characters_introduced: list[str]
    locations_introduced: list[str]
    objects_introduced: list[str]
    events_introduced: list[str]
    relationships_introduced: list[str]
    conflicts_introduced: list[str]
    open_threads: list[str]
        
def summarize_scenes(scenes, summarized_story):
    ## prompt the language model to summarize the scenes up to this point
    messages = [
        {"role": "system", "content": "You are a storyteller. You'll be given a list of scenes, and you need to summarize the story up to this point. The consumer of the story is writing each scene as they go, so it should help them to stay oriented in the story. Respond with JSON, given the following format: {{'story_summary': 'summary of the story', 'scene_summaries': ['summary of each scene'], 'characters_introduced': ['list of characters introduced'], 'locations_introduced': ['list of locations introduced'], 'objects_introduced': ['list of objects introduced'], 'events_introduced': ['list of events introduced'], 'relationships_introduced': ['list of relationships introduced'], 'conflicts_introduced': ['list of conflicts introduced'], 'open_threads': ['list of open threads']}}"},
        {"role": "user", "content": "\n".join(scenes) + "\n\nThe story so far is: " + summarized_story.story_summary + "\n\nThe scene by scene summary of the story so far is: " + "\n".join(summarized_story.scene_summaries) + "\n\nThe characters introduced are: " + "\n".join(summarized_story.characters_introduced) + "\n\nThe locations introduced are: " + "\n".join(summarized_story.locations_introduced) + "\n\nThe objects introduced are: " + "\n".join(summarized_story.objects_introduced) + "\n\nThe events introduced are: " + "\n".join(summarized_story.events_introduced) + "\n\nThe relationships introduced are: " + "\n".join(summarized_story.relationships_introduced) + "\n\nThe conflicts introduced are: " + "\n".join(summarized_story.conflicts_introduced) + "\n\nThe open threads are: " + "\n".join(summarized_story.open_threads)}
    ]

    response = client.responses.parse(
        model="gpt-4o",
        input=messages,
        text_format=SummarizedStory,
    )
    print("Summarized story: ", response.output_parsed)

    return response.output_parsed


character_name = input("What is the character's name? ")
scene = input("What is the first scene? ")
if scene == "":
    ## generate a random scene
    scene = generate_random_scene(character_name)

scenes.append(scene)
summarized_story = SummarizedStory(story_summary="", scene_summaries=[], characters_introduced=[], locations_introduced=[], objects_introduced=[], events_introduced=[], relationships_introduced=[], conflicts_introduced=[], open_threads=[])
summarized_story = summarize_scenes(scenes, summarized_story)
while True:
    next_actions = get_next_actions(scene, character_name)
    player_choice = get_player_choice(next_actions, scene, character_name)
    scene = get_next_scene(player_choice, next_actions, scene, character_name, summarized_story)
    print(scene)
    scenes.append(scene)
    if len(scenes) > 5:
        summarized_story = summarize_scenes(scenes, summarized_story)
        save_scenes(scenes)
        scenes = []