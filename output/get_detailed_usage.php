<?php
    #Get the date in format YYYY-MM-dd from the request
    $url = $_SERVER['REQUEST_URI'];
    $parts = parse_url($url);
    $query_part = parse_url($url, PHP_URL_QUERY);
    parse_str($query_part, $query);
    $date = $query['date'];
    $mode = $query['mode'];
    #echo $date;
    #echo $mode;

    $command=system("python get_detailed_usage.py " . $date . " " . $mode . " 2>&1");
    #$command = escapeshellcmd('python get_detailed_usage.py');
    $output = shell_exec($command);
    echo $output;
?>
