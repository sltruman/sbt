!/bin/bash 
find /home/speedbot/large_sorting_first/db/plates_sorting/ -mtime +7 | xargs rm -f
find /home/speedbot/large_sorting_first/db/plates/ -mtime +7 | xargs rm -f
find /home/speedbot/zlt/mybigsort_v2/saveImgs -mtime +7 | xargs rm -f
find /home/speedbot/zlt/mybigsort_v4/saveImgs -mtime +7 | xargs rm -f