<!DOCTYPE html>
<html lang="en">
<head>
    <title>Home Energy</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link href="usage.css" rel="stylesheet" type="text/css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script src="https://www.gstatic.com/charts/loader.js"></script>
    <script>
    const ModeEnum = { "DAY":1, "MONTH":2, "YEAR":3 };
    Object.freeze(ModeEnum);

    var FEATURE_PRODUCTION = 1;
    var FEATURE_CONSUMPTION = 1;
    var FEATURE_GAS = 1;

    var mode = ModeEnum.DAY;
    var detailedDate = new Date();

    //chart variables
    var chart;
    var chartData;
    var chartDisplayData;

    var chartCreated = false;

    var chartVaxisMultiple = 500;

    var chartColors = ['#009FF5', '#8cea5d', '#f7B32b', '#dc5665', '#2266bf', '#cc1467'];
    var chartShowUp = true;
    var chartShowDown = true;
    var chartShowProd = true;
    var chartShowCons = false;
    var chartShowPeakDown = false;
    var chartShowGas = false;

    var chartPrevShowUp;
    var chartPrevShowDown;
    var chartPrevShowProd;
    var chartPrevShowCons;
    var chartPrevShowPeakDown;
    var chartPrevShowGas;

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

    function get_fixed_digits(value) {
        if (value >= 100) {
            return round(value, 0);
        } else if (value >= 10) {
            return round(value, 1);
        } else {
            return round(value, 2);
        }
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
                $("#data_field_total_up_div").html(get_fixed_digits(result.total_up));
                $("#data_field_total_down_div").html(get_fixed_digits(result.total_down));
                $("#data_field_peak_down_div").html(round(result.peak_down, 1));

                if (FEATURE_PRODUCTION)
                {
                    $("#data_field_total_prod_div").html(get_fixed_digits(result.total_prod));
                }
                if (FEATURE_CONSUMPTION)
                {
                    total_cons = result.total_down + result.total_prod - result.total_up;
                    $("#data_field_total_cons_div").html(get_fixed_digits(total_cons));
                }
                if (FEATURE_GAS)
                {
                    $("#data_field_total_gas_div").html(get_fixed_digits(result.total_gas));
                }

                // Create the data table
                chartData = new google.visualization.DataTable();
                p = null;
                c = null;
                g = null;

                chartData.addColumn('datetime', 'Tijd'); //datetime or timeofday
                chartData.addColumn('number', 'Down');
                chartData.addColumn('number', 'Up');
                chartData.addColumn('number', 'Production');
                chartData.addColumn('number', 'Peak Down');
                chartData.addColumn('number', 'Consumption');
                chartData.addColumn('number', 'Gas');

                $.each(result.detailed_up_down, function(i, entry) {        
                    timestamp = new Date(entry.t);
                    if (FEATURE_PRODUCTION) {
                        if (entry.p) {
                            p = -entry.p
                        } else {
                            p = null;
                        }
                    }
                    if (FEATURE_CONSUMPTION) {
                        if (entry.p <= entry.u) {
                            c = entry.d;
                        } else {
                            c = entry.d + entry.p - entry.u;
                        }
                    }
                    if (FEATURE_GAS) {
                        if (entry.g) {
                            g = entry.g
                        } else {
                            g = null;
                        }
                    }
                    chartData.addRow([timestamp,
                                      entry.d,
                                      (entry.u == 0) ? null : -entry.u,
                                      p,
                                      entry.pd,
                                      c,
                                      g]);
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
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowDown) {
            cId = chartDisplayData.getColumnIndex('Down');
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowProd) {
            cId = chartDisplayData.getColumnIndex('Production');
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowCons) {
            cId = chartDisplayData.getColumnIndex('Consumption');
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowPeakDown) {
            cId = chartDisplayData.getColumnIndex('Peak Down');
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }
        if (!chartShowGas) {
            cId = chartDisplayData.getColumnIndex('Gas');
            nbOfRows = chartDisplayData.getNumberOfRows();
            for (rId = 0;rId < nbOfRows; rId++) {
                chartDisplayData.setValue(rId, cId, null);
            }
        }

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

        if (chartShowGas && mode == ModeEnum.DAY) {
            chartVaxisMultiple = 0.01;
            //Filter out the rows where gas is null. This gives wider bars.
            cId1 = chartDisplayData.getColumnIndex('Gas');
            for (rId = 0;rId < chartDisplayData.getNumberOfRows();) {
                gas = chartDisplayData.getValue(rId, cId1);
                if (gas == null) {
                    chartDisplayData.removeRow(rId);
                    continue;
                }
                rId++;
            }
        } else {
            chartVaxisMultiple = 500;
        }
    }

    //controls
    window.onload = function() {
        if (FEATURE_PRODUCTION == 0) {
            FEATURE_CONSUMPTION = 0;
        }

        const data_fields = [];

        data_fields.push({id:"data_field_total_down_div", label:"DOWN"});
        data_fields.push({id:"data_field_total_up_div", label:"UP"});
        data_fields.push({id:"data_field_peak_down_div", label:"PEAK"});
        if (FEATURE_PRODUCTION) {
            data_fields.push({id:"data_field_total_prod_div", label:"PRODUCTION"});
        }
        if (FEATURE_CONSUMPTION) {
            data_fields.push({id:"data_field_total_cons_div", label:"CONSUMPTION"});
        }
        if (FEATURE_GAS) {
            data_fields.push({id:"data_field_total_gas_div", label:"GAS (㎥)"});
        }

        var data_fields_table = document.getElementById("data_fields_table");
        for (var i = 0, row; row = data_fields_table.rows[i]; i++) {
           for (var j = 0, cell; cell = row.cells[j]; j++) {
                if (data_fields.length) {
                    data_field = data_fields.shift();
                    cell.childNodes[0].id = data_field.id;
                    cell.childNodes[1].id = data_field.id.slice(0, -3) + 'label_div';
                    cell.childNodes[1].innerHTML = data_field.label;
                }
           }
        }

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
                if (FEATURE_PRODUCTION) {
                    if (chartShowPeakDown) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;

                        //disable peak data
                        chartShowPeakDown = false;
                    } else if (chartShowCons) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;

                        //disable consumption data
                        chartShowCons = false;
                    } else if (chartShowGas) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;

                        //disable gas data
                        chartShowGas = false;
                    } else {
                        chartShowUp = !chartShowUp;
                    }
                    showHideChartColumns();
                    drawChart(mode, chartDisplayData);
                }
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
                } else if (chartShowCons) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;

                    //disable consumption data
                    chartShowCons = false;
                } else if (chartShowGas) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;

                    //disable gas data
                    chartShowGas = false;
                } else {
                    chartShowDown = !chartShowDown;
                }
                showHideChartColumns();
                drawChart(mode, chartDisplayData);
            }
        );
        $("#data_field_total_prod_div").click(
            function() {
                if (FEATURE_PRODUCTION) {
                    if (chartShowPeakDown) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;

                        //disable peak data
                        chartShowPeakDown = false;
                    } else if (chartShowCons) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;

                        //disable consumption data
                        chartShowCons = false;
                    } else if (chartShowGas) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;

                        //disable gas data
                        chartShowGas = false;
                    } else {
                        chartShowProd = !chartShowProd;
                    }
                    showHideChartColumns();
                    drawChart(mode, chartDisplayData);
                }
            }
        );
        $("#data_field_peak_down_div").click(
            function() {
                if (chartShowPeakDown) {
                    //restore the saved settings
                    chartShowUp = chartPrevShowUp;
                    chartShowDown = chartPrevShowDown;
                    chartShowProd = chartPrevShowProd;
                    chartShowCons = chartPrevShowCons;
                    chartShowGas = chartPrevShowGas;
                } else if (chartShowCons) {
                    chartShowCons = false;
                } else if (chartShowGas) {
                    chartShowGas = false;
                } else {
                    //save the current settings
                    chartPrevShowUp = chartShowUp;
                    chartPrevShowDown = chartShowDown;
                    chartPrevShowProd = chartShowProd;
                    chartPrevShowCons = chartShowCons;
                    chartPrevShowGas = chartShowGas;

                    //disable other data
                    chartShowUp = false;
                    chartShowDown = false;
                    chartShowProd = false;
                    chartShowCons = false;
                    chartShowGas = false;
                }
                chartShowPeakDown = !chartShowPeakDown;
                showHideChartColumns();
                drawChart(mode, chartDisplayData);
            }
        );
        $("#data_field_total_cons_div").click(
            function() {
                if (FEATURE_CONSUMPTION) {
                    if (chartShowCons) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;
                        chartShowPeakDown = chartPrevShowPeakDown;
                        chartShowGas = chartPrevShowGas;
                    } else if (chartShowPeakDown) {
                        chartShowPeakDown = false;
                    } else if (chartShowGas) {
                        chartShowGas = false;
                    } else {
                        //save the current settings
                        chartPrevShowUp = chartShowUp;
                        chartPrevShowDown = chartShowDown;
                        chartPrevShowProd = chartShowProd;
                        chartPrevShowPeakDown = chartShowPeakDown;
                        chartPrevShowGas = chartShowGas;

                        //disable other data
                        chartShowUp = false;
                        chartShowDown = false;
                        chartShowProd = false;
                        chartShowPeakDown = false;
                        chartShowGas = false;
                    }
                    chartShowCons = !chartShowCons;
                    showHideChartColumns();
                    drawChart(mode, chartDisplayData);
                }
            }
        );
        $("#data_field_total_gas_div").click(
            function() {
                if (FEATURE_GAS) {
                    if (chartShowGas) {
                        //restore the saved settings
                        chartShowUp = chartPrevShowUp;
                        chartShowDown = chartPrevShowDown;
                        chartShowProd = chartPrevShowProd;
                        chartShowCons = chartPrevShowCons;
                        chartShowPeakDown = chartPrevShowPeakDown;
                    } else if (chartShowPeakDown) {
                        chartShowPeakDown = false;
                    } else if (chartShowCons) {
                        chartShowCons = false;
                    } else {
                        //save the current settings
                        chartPrevShowUp = chartShowUp;
                        chartPrevShowDown = chartShowDown;
                        chartPrevShowProd = chartShowProd;
                        chartPrevShowCons = chartShowCons;
                        chartPrevShowPeakDown = chartShowPeakDown;

                        //disable other data
                        chartShowUp = false;
                        chartShowDown = false;
                        chartShowProd = false;
                        chartShowCons = false;
                        chartShowPeakDown = false;
                    }
                    chartShowGas = !chartShowGas;
                    showHideChartColumns();
                    drawChart(mode, chartDisplayData);
                }
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
                            groupWidth: '80%'
                        },
                        vAxis: { 
                            textStyle: { 
                                color: '#f4f4f9' 
                            },
                            gridlines: {  
                                multiple: chartVaxisMultiple,
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
            &lt;&lt;
        </div>
        <div id="controls_prev_1_div" class="control_button">
            &lt;
        </div>
        <div id="day_date_div" class="day_date">
        </div>
        <div id="controls_next_1_div" class="control_button">
            &gt;
        </div>
        <div id="controls_next_2_div" class="control_button">
            &gt;&gt;
        </div>
    </div>
    <br/>
    <table id="data_fields_table" class="data_fields">
        <tr>
            <td><div class="data_field"></div><div class="data_field_label"></div></td>
            <td><div class="data_field"></div><div class="data_field_label"></div></td>
        </tr>
        <tr>
            <td><div class="data_field"></div><div class="data_field_label"></div></td>
            <td><div class="data_field"></div><div class="data_field_label"></div></td>
        </tr>
        <tr>
            <td><div class="data_field"></div><div class="data_field_label"></div></td>
            <td><div class="data_field"></div><div class="data_field_label"></div></td>
        </tr>
    </table>
</body>
</html>
