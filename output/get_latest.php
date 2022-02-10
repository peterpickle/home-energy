<?php
    #For some reason it doesn work when /usr/bin/python of /usr/bin/python3 is used
    $command = "python get_latest.py 2>&1";
    #$command = system($command);
    #$command = escapeshellcmd('python get_latest.py');
    $output = shell_exec($command);
    echo $output;
?>
