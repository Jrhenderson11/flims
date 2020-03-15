# Flims

This is a tool for querying and formatting a list of films that I keep in Simplenote.


# How it works

 - Retrieve notes from Simplenote
 - Find first note with 'FILM' in title
 - Filter out things that aren't film titles (web links + markdown titles)
 - Check against a local cached copy of films to find any films that haven't been retrieved yet
 - Use imdbpy to get more film details (not always very accurate)
 - Nicely print out to console

# TODO:

 - fix film difference logic    [✓]
 - fix innacurate imdb results  [ ]
 - make prettier				[✓] 
 - querying list by genre       [✓]
 - make years easier to read    [ ]