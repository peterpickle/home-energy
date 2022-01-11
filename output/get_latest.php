<?php
    #For some reason it doesn work when /usr/bin/python of /usr/bin/python3 is used
    $command=system("python get_latest.py 2>&1");
    #$command = escapeshellcmd('python get_latest.py');
    $output = shell_exec($command);

    #$redisObj = new Redis();
    #$redisObj->connect('127.0.1.1', 6379);
    #$output = $redisObj->get('electricity_down_sec');
    #$output = 'A';

     echo $output;
?>
