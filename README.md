# Neodium

Neodium is a discord music bot with many advanced features. This bot has been made to fill the place of groovy and make it open-source so that anyone can use it. With a First come First serve and task clearing queueing system that is when a queued audio is played it gets removed from the queue so the next audio in the queue can be played.

## Key Features

1. No disturb feature: If anyone is serving someone then the bot can't be made to leave the VC.
2. Advanced No disturb: You can lock the player by using -lock command and anyone will not be able to clear the queue and pause, resume, skip or stop the player except who initiated the lock. In future planning to add a voting system.
3. Live Feature: The bot can play live youtube videos using -live or -l <youtube live url> 

**NOTE: These are the only the exclusive features that other bots generally don't have. For full usage check usage section**

## Usage/Commands

**-add-playlist** [playlist url] [starting index] [ending index]: To add a playlist to queue  
**-clear-queue** or **-clear** : Can only be done if there is no lock initiated. Clears the queue.  
**-help** : Shows help message.  
**-join** : Makes the bot join a VC.         
**-leave** : Makes the bot leave the VC.  
**-live** or **-l** [video url] : Plays the live youtube video.   
**-lock** : Locks the player and the queue.  
**-lyrics** : Displays lyrics of the current song.  
**-pause** : Pauses player.  
**-play** or **-p** [keyword] : Searches the keyword on youtube and plays the first result.   
**-queue** [delimeter] : Displays the songs currently in queue.  
**-remove** [index no] : Removes a mentioned song from queue.       
**-resume** : Resumes the player.  
**-search** or **-s** [keyword] : Searches the keyword and displays first 5 results. Choosing one of them will queue the song.    
**-skip** : Skips the current song.  
**-stop** : Stops the player from playing anything else.  
**-download** or **-d** [video url] [codec option]: Downloads the YT video, Instagram video or reel in the url. For codec option 0(default) is v:h264, a:aac.  

## Installation/Setup

First make sure you have ffmpeg installed install it by

for debian:
```bash
apt install ffmpeg
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip install -r requirements.txt
```

This bot fetches lyrics from [genius.com](https://genius.com) searched using google search api. All this things are done by the lyrics_extractor module which requires SEARCH ENGINE CODE and GOOGLE SEARCH API TOKEN. How to setup lyrics_extractor is given [here](https://www.geeksforgeeks.org/create-a-gui-to-extract-lyrics-from-song-using-python/) you just need the two values and put it in credentials.json.

Now time for credentials if you are using the code from master branch or raw_dev then create a credentials.jsob file.

### credentials.json
```json
{
    "token": "BOT TOKEN",
    "search_engine": "SEARCH ENGINE CODE",
    "search_token": "GOOGLE SEARCH API TOKEN"
}
```
But if you using the code from deploy then there is no credentials.json file it takes them from the environment. Now setting them up.

```bash
export TOKEN=<BOT TOKEN>
export SEARCH_ENGINE=<SEARCH ENGINE CODE>
export SEARCH_TOKEN=<GOOGLE SEARCH API TOKEN>
```

The deploy branch requires an extra file named cookies.txt its just to remove age restriction. So to make it log into your not age restricted google account in your browser and then export cookies.txt file of that account using the cookies.txt extension. See more about it in setup of youtube-dl.

Now running it is pretty easy as you can make a service, a background task etc. but the very general way is 

```bash
python bot.py
```

## Cautions

1. Never try to make money from this project, not because I will sue you but Youtube can sue you and thats why this project is open-sourced.
2. Don't get confused between the branches and their code. master is the general stable code base, raw_dev is for me to write code and deploy is for servers or particularly for platform as a service. Also don't use any code outside these branches as they can be outdated. Deploy branch is always recomended.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPL v3.0](https://github.com/pritam20ps05/neodium/blob/proj-info/LICENSE)
