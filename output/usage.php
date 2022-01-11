<html>
<head>
    <title>Home Energy</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <style>
    /* color palette
      https://coolors.co/
    --inchworm: #8cea5d;
    --Xiketic: #171216;
    --caroline-blue: #09FF5;
    --maximum-yellow-red: #ffc95c;
    --fire-opal: #e15a51;
    --ghost-white: #f4f4f9;
    --honey-yellow: #f7B32b;
    peak: DC5665
    */
    body
    {
        font-family: Arial, Tahoma, sans-serif;
        text-align: center;
        background-color: #171216;
        
    }
    .current_usage_us
    {
        font-size: 160pt;
        font-weight: 900;
        color: #8cea5d;
    }
    .current_usage_ds_normal
    {
        font-size: 160pt;
        font-weight: 900;
        color: #009FF5;
    }
    .current_usage_ds_high
    {
        font-size: 160pt;
        font-weight: 900;
        color: #ffc95c;
    }
    .current_usage_ds_very_high
    {
        font-size: 160pt;
        font-weight: 900;
        color: #e15a51;
    }
    .current_prod
    {
        display: inline-block;
        padding: 0px 50px 0px 50px;
        font-size: 40pt;
        font-weight: 900;
        color: #f7B32b;
    }
    .current_peak
    {
        display: inline-block;
        padding: 0px 50px 0px 50px;
        font-size: 40pt;
        font-weight: 900;
        color: #dc5665;
    }
    .mode_button
    {
        display: inline-block;
        color: #f4f4f9;
        padding: 50px 50px 0px 50px;
        font-size: 20pt;
        font-weight: 900;
    }
    .chart
    {
        text-align: center;
        margin-left: auto;
        margin-right: auto;
    }
    .day_date
    {
        display: inline-block;
        color: #f4f4f9;
        font-size: 40pt;
        font-weight: 900;
    }
    .control_button
    {
        display: inline-block;
        color: #f4f4f9;
        padding: 0px 50px 0px 50px;
        font-size: 40pt;
        font-weight: 900;
    }
    .data_fields
    {
        margin-left: auto;
        margin-right: auto;
    }
    .data_field
    {
        padding: 50px 50px 50px 50px;
        font-size: 120pt;
        font-weight: 900;
        /*display: table-cell;
        vertical-align: middle;*/
        /*display: inline-block;
        padding: 0px 50px 0px 50px;*/
    }
    #data_field_total_up_div
    {
        color: #8cea5d;
    }
    #data_field_total_down_div
    {
        color: #009ff5;
    }
    #data_field_peak_down_div
    {
        color: #dc5665;
    }
    #data_field_total_prod_div
    {
        color: #f7B32b;
    }
    </style>
    <script>
    const ModeEnum = { "DAY":1, "MONTH":2, "YEAR":3 };
    Object.freeze(ModeEnum);

    var FEATURE_PRODUCTION = 1;

    var mode = ModeEnum.DAY;
    var detailedDate = new Date();

    //chart variables
    var chart;
    var chartData;
    var chartDisplayData;

    var chartCreated = false;

    var chartColors = ['#009FF5', '#8cea5d', '#f7B32b', '#dc5665'];
    var chartShowUp = true;
    var chartShowDown = true;
    var chartShowProd = true;
    var chartShowPeakDown = false;

    var chartPrevShowUp;
    var chartPrevShowDown;
    var chartPrevShowProd;

    Date.prototype.addDays = function (days) {
        const date = new Date(this.valueOf());
        date.setDate(date.getDate() + days);
        return date;
    };

    Date.prototype.substractDays = function (days) {
        const date = new Date(this.valueOf());
        date.setDate(date.getDate() - days);
        return date;
    };

    Date.prototype.addMonths = function (months) {
        const date = new Date(this.valueOf());
        date.setMonth(date.getMonth() + months);
        return date;
    };

    Date.prototype.substractMonths = function (months) {
        const date = new Date(this.valueOf());
        date.setMonth(date.getMonth() - months);
        return date;
    };

    Date.prototype.addYears = function (years) {
        const date = new Date(this.valueOf());
        date.setFullYear(date.getFullYear() + years);
        return date;
    };

    Date.prototype.substractYears = function (years) {
        const date = new Date(this.valueOf());
        date.setFullYear(date.getFullYear() - years);
        return date;
    };

    function round(value, decimals) {
        return Number(Math.round(value +'e'+ decimals) +'e-'+ decimals).toFixed(decimals);
    }

    function getLatestUsage() {
        $.getJSON("get_latest.php", function(latest) {
            current_usage_div = document.getElementById("current_usage_div");

            if (latest.down > 3150) {
                current_usage_div.className = "current_usage_ds_very_high";
            } else if (latest.down > 2500) {
                current_usage_div.className = "current_usage_ds_high";
            } else if (latest.down > 0) {
                current_usage_div.className = "current_usage_ds_normal";
            } else {
                current_usage_div.className = "current_usage_us";
            }

            if (latest.down == -1 && latest.up == -1) {
                current_usage_div.innerHTML = "No data"
                current_usage_div.className = "current_usage_ds_very_high";
            } else {
                displayVal = (latest.down > 0) ? latest.down : latest.up;
                current_usage_div.innerHTML = displayVal + " W";
            }

            $("#current_peak_div").html(round(latest.predicted_peak_down, 1));

            if (FEATURE_PRODUCTION)
            {
                $("#current_prod_div").html(latest.prod + " W");
            }
            setTimeout("getLatestUsage()", 1000);
        });
    }
    getLatestUsage();

    function getDetailedUsage(dayDate) {
        detailedDate = dayDate;
        dayStr = dayDate.getFullYear() + '-' + (dayDate.getMonth() + 1).toString().padStart(2, '0') + '-' + dayDate.getDate().toString().padStart(2, '0');
        $.getJSON("get_detailed_usage.php", 
            {
                date: dayStr,
                mode: mode
            },
            function(result) {
                //display the total values
                if (result.total_up >= 100) {
                    rounded_total_up = round(result.total_up, 0);
                } else if (result.total_up >= 10) {
                    rounded_total_up = round(result.total_up, 1);
                } else {
                    rounded_total_up = round(result.total_up, 2);
                }
                if (result.total_down >= 100) {
                    rounded_total_down = round(result.total_down, 0);
                } else if (result.total_down >= 10) {
                    rounded_total_down = round(result.total_down, 1);
                } else {
                    rounded_total_down = round(result.total_down, 2);
                }
                $("#data_field_total_up_div").html(rounded_total_up);
                $("#data_field_total_down_div").html(rounded_total_down);
                $("#data_field_peak_down_div").html(round(result.peak_down, 1));

                if (FEATURE_PRODUCTION)
                {
                    if (result.total_prod >= 100) {
                        rounded_total_prod= round(result.total_prod, 0);
                    } else if (result.total_down >= 10) {
                        rounded_total_prod = round(result.total_prod, 1);
                    } else {
                        rounded_total_prod = round(result.total_prod, 2);
                    }
                    $("#data_field_total_prod_div").html(rounded_total_prod);
                }

                // Create the data table
                chartData = new google.visualization.DataTable();
                p = null;

                chartData.addColumn('datetime', 'Tijd'); //datetime or timeofday
                chartData.addColumn('number', 'Down');
                chartData.addColumn('number', 'Up');
                chartData.addColumn('number', 'Production');
                chartData.addColumn('number', 'Peak Down');

                $.each(result.detailed_up_down, function(i, entry) {        
                    timestamp = new Date(entry.t);
                    if (FEATURE_PRODUCTION) {
                        if (entry.p) {
                            p = -entry.p
                        } else {
                            p = null;
                        }
                    }
                    chartData.addRow([timestamp, entry.d, (entry.u == 0) ? null : -entry.u, p, entry.pd]);
                });

                //How dates are displayed in the tooltips
                dateFormatPattern = ""
                if (mode == ModeEnum.DAY) {
                    dateFormatPattern = "HH:mm"
                } else if (mode == ModeEnum.MONTH) {
                    dateFormatPattern = "MMM dd"
                } else if (mode == ModeEnum.YEAR) {
                    dateFormatPattern = "MMM"
                }
                dateFormatter = new google.visualization.DateFormat({ 
                    pattern: dateFormatPattern
                });
                dateFormatter.format(chartData, 0);

                //animations don't work with a dataview
                //var chartDataView = new google.visualization.DataView(chartData);
                showHideChartColumns();
                drawChart(mode, chartDisplayData);

                //display the date
                if (mode == ModeEnum.DAY) {
                    displayDateStr = dayStr;
                } else if (mode == ModeEnum.MONTH) {
                    displayDateStr = detailedDate.toLocaleString('en', { month: 'long', year: 'numeric'});
                } else if (mode == ModeEnum.YEAR) {
                    displayDateStr = detailedDate.toLocaleString('en', { year: 'numeric'});
                }
                $("#day_date_div").html(displayDateStr);
            });
    }

    function showHideChartColumns() {
        chartDisplayData = chartData.clone();
        if (!chartShowUp) {
            cId = chartDisplayData.getColumnIndex('Up');
            //chartDisplayData.removeColumns(cId, 1);
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowDown) {
            cId = chartDisplayData.getColumnIndex('Down');
            //chartDisplayData.removeColumns(cId, 1);
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowProd) {
            cId = chartDisplayData.getColumnIndex('Production');
            //chartDisplayData.removeColumns(cId, 1);
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowPeakDown) {
            cId = chartDisplayData.getColumnIndex('Peak Down');
            //chartDisplayData.removeColumns(cId, 1);
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }

        /*chartColors = [];
        if (chartShowDown) {
            chartColors.push('#009FF5');
        }
        if (chartShowUp) {
            chartColors.push('#8cea5d');
        }
        if (chartShowProd) {
            chartColors.push('#f7B32b');
        }
        if (chartShowPeakDown) {
            chartColors.push('#dc5665');
        }*/

        if (chartShowUp && chartShowProd) {
            //set the production to the self usage, not the full production
            cId1 = chartData.getColumnIndex('Production');
            cUpId = chartData.getColumnIndex('Up');
            cId2 = chartDisplayData.getColumnIndex('Production');
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                prod = chartData.getValue(rId, cId1);
                if (prod) {
                    prod = -prod;
                    up = -chartData.getValue(rId, cUpId);
                    chartDisplayData.setValue(rId, cId2, (prod > up) ? -(prod - up) : 0);
                }
            }
        }

        if (chartShowPeakDown && mode == ModeEnum.DAY) {
            //Filter out the rows where peak down is null. This gives wider bars.
            cId1 = chartDisplayData.getColumnIndex('Peak Down');
            for (rId = 0;rId < chartDisplayData.getNumberOfRows();) {
                peak_down = chartDisplayData.getValue(rId, cId1);
                if (peak_down == null) {
                    chartDisplayData.removeRow(rId);
                    continue;
                }
                rId++;
            }
        }
    }

    //controls
    window.onload = function() {
        $("#mode_year_div").click(
            function() {
                if (mode != ModeEnum.YEAR) {
                    mode = ModeEnum.YEAR;
                    getDetailedUsage(detailedDate);
                }
            }
        );
        $("#mode_month_div").click(
            function() {
                if (mode != ModeEnum.MONTH) {
                    mode = ModeEnum.MONTH;
                    getDetailedUsage(detailedDate);
                }
            }
        );
        $("#mode_day_div").click(
            function() {
                if (mode != ModeEnum.DAY) {
                    mode = ModeEnum.DAY;
                    getDetailedUsage(detailedDate);
                }
            }
        );
        $("#controls_prev_1_div").click(
            function() {
                if (mode == ModeEnum.DAY) {
                    prevDate = detailedDate.substractDays(1);
                } else if (mode == ModeEnum.MONTH) {
                    prevDate = detailedDate.substractMonths(1);
                } else if (mode == ModeEnum.YEAR) {
                    prevDate = detailedDate.substractYears(1);
                }
                getDetailedUsage(prevDate);
            }
        );
        $("#controls_next_1_div").click(
            function() {
                if (mode == ModeEnum.DAY) {
                    nextDate = detailedDate.addDays(1);
                } else if (mode == ModeEnum.MONTH) {
                    nextDate = detailedDate.addMonths(1);
                } else if (mode == ModeEnum.YEAR) {
                    nextDate = detailedDate.addYears(1);
                }
                getDetailedUsage(nextDate);
            }
        );
        $("#controls_prev_2_div").click(
            function() {
                if (mode == ModeEnum.DAY) {
                    prevDate = detailedDate.substractDays(7);
                } else if (mode == ModeEnum.MONTH) {
                    prevDate = detailedDate.substractMonths(12);
                } else if (mode == ModeEnum.YEAR) {
                    prevDate = detailedDate.substractYears(2);
                }
                getDetailedUsage(prevDate);
            }
        );
        $("#controls_next_2_div").click(
            function() {
                if (mode == ModeEnum.DAY) {
                    nextDate = detailedDate.addDays(7);
                } else if (mode == ModeEnum.MONTH) {
                    nextDate = detailedDate.addMonths(12);
                } else if (mode == ModeEnum.YEAR) {
                    nextDate = detailedDate.addYears(2);
                }
                getDetailedUsage(nextDate);
            }
        );
        $("#day_date_div").click(
            function() {
                //refresh detailed data
                getDetailedUsage(detailedDate);
            }
        );
        $("#data_field_total_up_div").click(
            function() {
                if (chartShowPeakDown) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;

                    //disable peak data
                    chartShowPeakDown = false;
                } else {
                    chartShowUp = !chartShowUp;
                }
                showHideChartColumns();
                drawChart(mode, chartDisplayData);
            }
        );
        $("#data_field_total_down_div").click(
            function() {
                if (chartShowPeakDown) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;

                    //disable peak data
                    chartShowPeakDown = false;
                } else {
                    chartShowDown = !chartShowDown;
                }
                showHideChartColumns();
                drawChart(mode, chartDisplayData);
            }
        );
        $("#data_field_total_prod_div").click(
            function() {
                if (chartShowPeakDown) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;

                    //disable peak data
                    chartShowPeakDown = false;
                } else {
                    chartShowProd = !chartShowProd;
                }
                showHideChartColumns();
                drawChart(mode, chartDisplayData);
            }
        );
        $("#data_field_peak_down_div").click(
            function() {
                if (chartShowPeakDown) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;
                } else {
                    //save the current settings
                    chartPrevShowUp = chartShowUp;
                    chartPrevShowDown = chartShowDown;
                    chartPrevShowProd = chartShowProd;

                    //disable other data
                    chartShowUp = false;
                    chartShowDown = false;
                    chartShowProd = false;
                }
                chartShowPeakDown = !chartShowPeakDown;
                showHideChartColumns();
                drawChart(mode, chartDisplayData);
            }
        );
    }

    /* charts */
    // Load the Visualization API and the corechart package.
    google.charts.load('current', {'packages':['corechart']});

    // Set a callback to run when the Google Visualization API is loaded.
    google.charts.setOnLoadCallback(getDetailedDataAndDrawChart);

    function getDetailedDataAndDrawChart() {
        getDetailedUsage(detailedDate);
    }

    function drawChart(mode, data) {
        var dayOptions = { 
                        curveType: 'function',
                        height: 600,
                        chartArea: {width: '85%', height: '85%'},
                        backgroundColor: 'transparent',
                        colors: chartColors,
                        bar: { 
                            groupWidth: '100%'
                        },
                        vAxis: { 
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: {  
                                multiple: 500,
                                color: '#6e6e6e',
                            }, 
                            minorGridlines: { 
                                count: 0,
                            },
                        },
                        hAxis: {
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: { 
                                count : 12,
                                color: 'transparent',
                                units: { hours: { format: 'HH' } }
                            },
                            minorGridlines: { 
                                count: 0,
                            } 
                        },
                        explorer: {
                            axis: 'horizontal',
                            maxZoomOut: 1,
                            keepInBounds: true
                        },
                        animation: {
                            startup: true,
                            duration: 500
                            //easing: 'out'
                        },
                        isStacked: true,
                        legend: 'none'}


        var monthOptions = { 
                        height: 600,
                        chartArea: {width: '85%', height: '85%'},
                        backgroundColor: 'transparent',
                        colors: chartColors,
                        vAxis: { 
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: {  
                                multiple: 1,
                                color: '#6e6e6e',
                            }, 
                            minorGridlines: { 
                                count: 0,
                            },
                        },
                        hAxis: {
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: { 
                                color: 'transparent',
                                units: { days: { format: 'd' } }
                            },
                            minorGridlines: { 
                                count: 0,
                            } 
                        },
                        animation: {
                            startup: true,
                            duration: 500
                            //easing: 'out'
                        },
                        isStacked: true,
                        legend: 'none'}

        var yearOptions = { 
                        height: 600,
                        chartArea: {width: '85%', height: '85%'},
                        backgroundColor: 'transparent',
                        colors: chartColors,
                        vAxis: { 
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: {  
                                multiple: 1,
                                color: '#6e6e6e',
                            }, 
                            minorGridlines: { 
                                count: 0,
                            },
                        },
                        hAxis: {
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: { 
                                color: 'transparent',
                            },
                            minorGridlines: { 
                                count: 0,
                            },
                            format: 'MMM'
                        },
                        animation: {
                            startup: true,
                            duration: 500
                            //easing: 'out'
                        },
                        isStacked: true,
                        legend: 'none'}

        chartDiv = document.getElementById('chart_div');

        if (!chartCreated) {
            chart = new google.visualization.ColumnChart(chartDiv);
            chartCreated = true;
        }

        if (mode == ModeEnum.DAY) {
            options = dayOptions;
        } else if (mode == ModeEnum.MONTH) {
            options = monthOptions;
        } else if (mode == ModeEnum.YEAR) {
            options = yearOptions;
        }
       
        chart.draw(data, options);
    }
    </script>
    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
<body>
    <div id="current_usage_div" class="current_usage_normal">
    </div>
    <div id="current_peak_div" class="current_peak">
    </div>
    <div id="current_prod_div" class="current_prod">
    </div>
    <div id="mode_div" class="mode">
        <div id="mode_year_div" class="mode_button">
            Year
        </div>
        <div id="mode_month_div" class="mode_button">
            Month
        </div>
        <div id="mode_day_div" class="mode_button">
            Day
        </div>
    </div>
    <div id="chart_div" class="chart">
    </div>
    <div id="controls_div" class="controls">
        <div id="controls_prev_2_div" class="control_button">
            <<
        </div>
        <div id="controls_prev_1_div" class="control_button">
            <
        </div>
        <div id="day_date_div" class="day_date">
        </div>
        <div id="controls_next_1_div" class="control_button">
            >
        </div>
        <div id="controls_next_2_div" class="control_button">
            >>
        </div>
    </div>
    <br/>
    <table id="data_fields_div" class="data_fields">
        <tr>
            <td><div id="data_field_total_down_div" class="data_field"></div></td>
            <td><div id="data_field_total_up_div" class="data_field"></div></td>
        </tr>
        <tr>
            <td><div id="data_field_peak_down_div" class="data_field"></div></td>
            <td><div id="data_field_total_prod_div" class="data_field"></div></td>
        </tr>
    </table>
</body>
</html>
