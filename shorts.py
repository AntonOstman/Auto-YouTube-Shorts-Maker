# Import everything
from dotenv import load_dotenv
import random
import os
import openai
from gtts import gTTS
from moviepy.editor import *
import moviepy.video.fx.crop as crop_vid
from moviepy.video.tools.subtitles import SubtitlesClip
load_dotenv()

# Ask for video info
# title = input("\nEnter the name of the video >  ")
title = "test"
# option = input('Do you want AI to generate content? (y/n) >  ')
option = ''

if option == 'y':
    # Generate content using OpenAI API
    theme = input("\nEnter the theme of the video >  ")

    ### MAKE .env FILE AND SAVE YOUR API KEY ###
    openai.api_key = os.environ["OPENAI_API"]
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=f"Generate content on - \"{theme}\"",
        temperature=0.7,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print(response.choices[0].text)

    yes_no = input('\nIs this fine? (y/n) >  ')
    if yes_no == 'y':
        content = response.choices[0].text
    else:
        content = input('\nEnter >  ')
else:
    # Read sample file and create the sentence from each line
    file = open("sample-text/short-sample.txt")
    sentences = file.read().split('\n')
    content = ' '.join(sentence for sentence in sentences)

# Create the directory
if os.path.exists('generated') == False:
    os.mkdir('generated')

max_video_length = 58
video_duration = max_video_length

# Generate speech for the video
def create_voice(content):
    generate_voice = False
    # if (generate_voice):
    speech = gTTS(text=content, lang='en', tld='ca', slow=False)
    speech.save("generated/speech.mp3")

    audio_clip = AudioFileClip("generated/speech.mp3")
    audio_clip = audio_clip.fx( vfx.speedx, 1) 

    new_content = content
    while (audio_clip.duration > video_duration):
        print(f'\nSpeech too long!\n {str(audio_clip.duration)} seconds \n {str(audio_clip.duration)} total')
        scale_diff = video_duration / audio_clip.duration
        remove_amount = int(len(new_content) * scale_diff) - 10
        new_content = new_content[:remove_amount]

        speech = gTTS(text=new_content, lang='en', tld='ca', slow=False)
        speech.save("generated/speech.mp3")

        audio_clip = AudioFileClip("generated/speech.mp3")
        audio_clip = audio_clip.fx( vfx.speedx, 1) 

    return new_content, audio_clip

print("Trying to find voiceover with correct length")
audio_ok = False


print("Editing video")
### VIDEO EDITING ###
content, audio_clip = create_voice(content)
# Trim a random part of minecraft gameplay and slap audio on it
video = VideoFileClip(f"gameplay/minecraft_parkour.mkv")
start_point = random.randint(1, int(video.duration) - video_duration)

video_clip = video.subclip(start_point, start_point + audio_clip.duration)
video_clip = video_clip.set_audio(audio_clip)

# Resize the video to 9:16 ratio
w, h = video_clip.size
target_ratio = 1080 / 1920
current_ratio = w / h

if current_ratio > target_ratio:
    # The video is wider than the desired aspect ratio, crop the width
    new_width = int(h * target_ratio)
    x_center = w / 2
    y_center = h / 2
    final_clip = crop_vid.crop(video_clip, width=new_width, height=h, x_center=x_center, y_center=y_center)
else:
    # The video is taller than the desired aspect ratio, crop the height
    new_height = int(w / target_ratio)
    x_center = w / 2
    y_center = h / 2
    final_clip = crop_vid.crop(video_clip, width=w, height=new_height, x_center=x_center, y_center=y_center)

print("Adding subtitles to video")

generator = lambda txt: TextClip(txt, align='center', size=(1000,None), method='caption', font='Montserrat', fontsize=70, color='white')
# generator2 = lambda txt: TextClip(txt, font='Arial', fontsize=110, color='black').

shown_words = 8
wordized = content.split()
# text_speedup = video_clip.duration * 0.10 # To display the subs a bit before the voice
wps = len(content.split()) / ( video_clip.duration)

divided_words = [wordized[i:i+shown_words] for i in range(0, len(wordized), shown_words)]

subs = []
for i, words in enumerate(divided_words):
    offset = 0.8
    subs_per_second = shown_words/wps
    sub_start = max(0, i*subs_per_second - offset)
    sub_end = min(i*subs_per_second + subs_per_second - offset, video_clip.duration)
    subs.append(((sub_start, sub_end), ' '.join(map(str, words))))
    print(subs[i][0])

    
subtitles = SubtitlesClip(subs, generator)
# subtitles2 = SubtitlesClip(subs, generator2)
# video_clip = CompositeVideoClip([video_clip, subtitles2.set_pos(('center'))])
video_clip = CompositeVideoClip([video_clip, subtitles.set_pos(('center'))])

# Write the final video
video_clip.write_videofile("generated/" + title + ".mp4", codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)