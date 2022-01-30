<html>
<head>
    <title>P1 reader debug</title>    
</head>
<body>
    <pre>
<?php
    $command=system("python p1_reader_debug.py 2>&1");
    $output = shell_exec($command);
     echo $output;
?>
    </pre>
</body>
