# Neodium

Neodium is a discord music bot with many advanced features. This bot has been made to fill the place of groovy and make it open-source so that anyone can use it. With a First come First serve and task clearing queueing system that is when a queued audio is played it gets removed from the queue so the next audio in the queue can be played. Supports playing audio from youtube and spotify.

## Key Features

1. No disturb feature: If anyone is serving someone then the bot can't be made to leave the VC.
2. Advanced No disturb: You can lock the player by using -lock command and anyone will not be able to clear the queue and pause, resume, skip or stop the player except who initiated the lock. In future planning to add a voting system.
3. Live Feature: The bot can play live youtube videos using -live or -l <youtube live url>.  
4. Download Feature: Download any public YT or instagram audio video file. Additional support has also been given for instagram private only.

**NOTE: These are the only the exclusive features that other bots generally don't have. For full usage check usage section**
    
## Deploy to Heroku

Click the deploy to heroku button for deploying it now only. Before doing that you would need 5 variable values mentioned in installation/setup section.
    
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/pritam20ps05/neodium/tree/deploy)

# Usage/Commands
## Basic
This category of commands contains the basic functionalities of the bot such as joining a VC.  
### commands
    -join                                Makes the bot join the channel 
                                         of the user, if the bot has already
                                         joined and is in a different channel
                                         it will move to the channel the user 
                                         is in. Only if you are not trying to 
                                         disturb someone.
    
    -leave                               Makes the bot leave the voice channel.
                                         Only if you are not trying to disturb 
                                         someone.
## Player
This category of commands contains the playable functionalities of the bot. All of them can make bot join vc, play audio and queue audio.
### commands
    -search, -s [query]                  Searches the query on YT and gives 5 
                                         results to choose from. Choosen one
                                         will be queued or played.
    
    -play, -p [query]                    Searches the query on YT and plays or 
                                         queues the most relevant result.
    
    -live, -l [url]                      Plays a YT live from the URL provided 
                                         as input.
    
    -add-playlist [playlist_url]         Adds a whole YT or Spotify playlist to queue 
     [starting_index] [ending_index]     and starts playing it. Input is taken as 
                                         the URL to the public or unlisted playlist.
                                         You can also mention a starting point or an 
                                         ending point of the playlist or both.
## Visualizer
This category of commands contains the visualizers which enables you to monitor some states of the bot or get some kind of info about something
### commands
    -queue [limit=10]                    Displays the current queue. Limit is the 
                                         number of entries shown per page, default 
                                         is 10.
    
    -lyrics                              Displays the lyrics of the current song if 
                                         available.
    
    -current, -c                         Displays information about the current song 
                                         in the player.
## Queue
This category of commands contains the commands related to queues. Also there is a concept of queue lock which will dissable any user from using these commands except the user initiating the lock with some more exceptions. Queue lock effective commands will be marked with "Q".
### commands
    -remove                   Q          Removes an mentioned entry from the queue.
    
    -pause                    Q          Pauses the current player.
    
    -resume                   Q          Resumes the paused player.
    
    -skip                     Q          Skips current audio.
    
    -stop                     Q          Just like skip but also clears the queue.
    
    -clear-queue, -clear      Q          Clears the queue.
    
    -shuffle                  Q          Randomly shuffles the whole queue.
    
    -lock                                Locks the queue and prevents anyone from 
                                         damaging anyone\'s experience.
## Download
This category of commands contains recently added download feature which can download YT and instagram audio video files with private support for instagram only.
### commands
    -download, -d [url]                  Downloads YT or instagram audio video files  
    [codec_option=0]                     from the url. If the bot is already playing  
                                         something then passing no input will result in 
                                         selecting that video. Codec_option is for 
                                         choosing vcodec, default is 0 for h264 but can 
                                         be set to 1 for codec provided by vendor.
    
    -login [username]                    Supports the instagram private feature. 
    [password]                           This command Logs in to your instagram 
                                         account and uses it to access files through 
                                         your account. Once logged in use the download 
                                         command normally. This command can only be 
                                         used in DMs in order to protect your privacy.
    
    -logout                              Logout of your account only if you are already 
                                         logged in.
## Special
This category of commands contains the special commands which can only be accessed by the owner of the bot. These commands enables the owner to remotely invoke methods for temporary fixes or other debugging stuff.
### commands
    -refetch [insta_cookie_fileid]       Refetches the default cookie files from the 
    [yt_cookie_fileid]                   google dive file ids' of the cookie files. 
                                         If not passed it gets the file ids' from 
                                         environmental variables.

    -add-cog [cog_name]                  Adds a predefined cog to the bot.
    
    -remove-cog [cog_name]               Removes a already existing cog. Generally 
                                         used to disable a functionality of the bot.

## Installation/Setup

First make sure you have ffmpeg installed, install it by

for debian:
```bash
sudo apt install ffmpeg
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip install -r requirements.txt
```

This bot fetches lyrics from [genius.com](https://genius.com) searched using google search api. All this things are done by the lyrics_extractor module which requires SEARCH ENGINE CODE and GOOGLE SEARCH API TOKEN. How to setup lyrics_extractor is given [here](https://www.geeksforgeeks.org/create-a-gui-to-extract-lyrics-from-song-using-python/) you just need the two values.

Now get the [bot token](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token), after that create 2 cookie files one for youtube and the other for instagram using [cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en) chrome extension. Once done upload them to google drive, make it public and copy their file ids'.

You will also need spotify client id and client secret which you can get them after creating an app from [here](https://developer.spotify.com/dashboard/applications).
    
The following are all the environmental variables required for starting the bot.

```bash
TOKEN <BOT TOKEN>
SEARCH_ENGINE <SEARCH ENGINE CODE>
SEARCH_TOKEN <GOOGLE SEARCH API TOKEN>
INSTA_COOKIEFILE_ID <COOKIEFILE GDRIVE FILE ID FOR INSTAGRAM>
YT_COOKIEFILE_ID <COOKIEFILE GDRIVE FILE ID FOR YT>
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
```

This bot requires the following buildpacks and the above mentioned variables. If you are using the deploy to heroku button to deploy, then you don't need to care about the buidpacks but you will still need the variables.
### Buildpacks
    heroku/python
    https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
    https://github.com/xrisk/heroku-opus.git
    
## Branch Info
    master                               The general and the most recent stable 
                                         version of the bot.
    
    raw_dev                              The most updated version of the bot
                                         and the one with raw development.
    
    deploy                               The code that is ready to be deployed
                                         to a heroku server.
    
    proj-info                            A accessory branch which gets the most
                                         updates regarding documentation and
                                         license.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPL v3.0](https://github.com/pritam20ps05/neodium/blob/proj-info/LICENSE)
