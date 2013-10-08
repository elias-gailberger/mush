mush
====

a python command line music player
by Elias Gailberger - elias.gailberger@gmail.com

#### What does it do?
It plays your music. The player is intended mainly for shuffled play, and its key features are built around it, namely:
  - You can tag your music and play only tracks with certain tags, or certain tag combinations
  - You can set specific tracks to be played more or less often according to how much you like them.
  
#### This sounds boring.
Yes. I built this program for use by nobody but myself, I'm sharing it anyway. I wanted to have a player where I can veto things from random play, and conveniently play music from a subset of my library that matches what I want to hear at the time. I didn't find such a player, so I wrote it. I doesn't do much more than that, apart from basic playlist management (you can't even skip to different parts of a track). Everytime you find a feature lacking, it's because I didn't miss it enough to warrant implementing it.

How do I use it?
----------------
When you first start mush, it will assume your music is in %userprofile%/Music (That's where your music is normally stored if you are a well-behaved windows user). If it isn't, you might want to change the default folder in mush.cfg. You can also navigate the filesystem in Unix fashion with cd and ls if you want to play from different folders.

Type in `play` and hit Enter.

The player will now most likely fling random pieces of music at you, from all the tracks in all the subfolders it can find from its current folder. *Now here comes the important part:* If you are anything like me (why else would you else use this player) you now want to tag those tracks, so the player knows something about them. The more you tell it, the sweeter things you can pull off later ("Just play vegetarian progressive grindcore from the 17th century"¹ or "Play me instrumental tracks with some rhythm behind them"²). You do this by simply entering for instance `tag instrumental`. You also can easily give multiple tags (`tag beatles;lennon;acidtrip`). If you make typos with your tags, you can either say `untag rhyhtm` or `tag -rhyhtm`³ - a minus sign before a tag removes it.
Also, you might want to tell mush how much you like a certain track, so it can play it more or less often in the future. This is most easily done by simply typing `+` and `-` and hitting enter. You can also be more specific and say something like `+ 10` or `- 50` (all tracks start with a default playing probability of 100, the `+` and `-` commands by default add/subtract 20).
If some track you don't want to hear randomed comes up⁴, you can just veto it by typing `never`. This is handy if you have some music you don't want anyone else to hear, or you just hate a song on your disk for some reason (what are you doing? Just delete it).

#### I have my favourite songs tagged up, what now?
With the `playtag` command, or `pt` for short, you can play tracks from all music with a certain tag: `pt instrumental` will only play music you have tagged as instrumental. You can also forbid tags using a minus sign - `pt -nsfw` might be practical if you have music tagged that way for some reason.

#### What tags should I use for my music?
I'd recommend tagging every track with anything that comes to your mind while hearing it. This includes obvious stuff like artist and genre or some general adjectives like "slow", "fast", "sad", "long" and "awesome", but isn't at all restricted to that. You can tag a song with the first line of the chorus if like it but always forget its name, you can make a tag for music your girlfriend likes, for your next birthday party, for coding or whatever you please. There is also no known upper limit on tag sizes and you can use virtually any special characters, so go nuts.

#### Where's a full list of commands this thing accepts?
Just say `help` or `?` and you'll get one.

Troubleshooting
---------------

#### Help, it won't play a specific track!
There is a known bug where the Windows MCI will refuse to play tracks with ID3 tags larger than 256 KB. The most common cause for this is having a high-resolution album cover in the music file itself. Just remove the cover using an external tag editor and you'll probably be fine. Probably.

#### The player hates me and won't play music anymore / doesn't even read my commands!
Just keep calm and restart. The player is a buggy piece of crap and will do that sometimes.

#### Your support for non-ASCII characters is awful and you need to die.
I know.

#### This damn thing won't work, and I would like to bestow curses and hate mail upon you!
elias.gailberger@gmail.com
You might get into my spam folder, but if not, I'll read it and probably respond.


¹If this subset of your music library is non-empty, be sure to send me samples.

²This is a more realistic use case - the intersection between the "instrumental" and "rhythm" tags is exactly the kind of background music I use for work a lot.

³I typo this word all the time.

⁴Obligatory reference: http://xkcd.com/400/
