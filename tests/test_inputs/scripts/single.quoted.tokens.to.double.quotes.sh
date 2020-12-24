# e.g. 
cat top100.60s.albums.just.album.names.txt | sed -E s/"^'(.*)'$"/\"\\1\"/ > doublequoted.top100.60s.albums.just.album.names.txt
