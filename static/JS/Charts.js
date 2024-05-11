// Load google charts
google.charts.load('current', {packages: ['corechart', 'table']});
google.charts.setOnLoadCallback(drawTopMovieGenresPieChart);
google.charts.setOnLoadCallback(drawTopCountriesBarChart);
google.charts.setOnLoadCallback(drawTopCompaniesTable);
google.charts.setOnLoadCallback(drawTopBoxOfficeHitsColumnChart);
google.charts.setOnLoadCallback(drawGenreRuntimeGroupBarChart);
google.charts.setOnLoadCallback(drawGenreBudgetColumnChart);

// Draw the chart and set the chart values
function drawTopMovieGenresPieChart() {
    var pieChartData = [['Genre', 'Count']];

    for (let  i = 0; i < genresData.length; i++)
    {
        pieChartData.push([genresData[i]._id, genresData[i].count]);
    }

  var data = google.visualization.arrayToDataTable(pieChartData);
  var options = {title:'Top Movie Genres', height: 300, legend: 'left', chartArea: {width: "80%", height: "80%" }};

  var chart = new google.visualization.PieChart(document.getElementById('genrePieChart'));
  chart.draw(data, options);
}

function drawTopCountriesBarChart() {

    var barChartData = [['Country', 'Count']];

    for (let  i = 0; i < countryData.length; i++)
    {
        barChartData.push([countryData[i]._id, countryData[i].count]);
    }

    var data = google.visualization.arrayToDataTable(barChartData);

    var options = {title:'Number of Movies Produced By Top Countries',  height: 300, legend: 'none'};

    const chart = new google.visualization.BarChart(document.getElementById('countriesBarChart'));
    chart.draw(data, options);
}

function drawTopBoxOfficeHitsColumnChart() {

    var columnChartData = [['Company', 'Profit']];

    for (let  i = 0; i < boxOfficeData.length; i++)
    {
        columnChartData.push([boxOfficeData[i]._id, boxOfficeData[i].profit]);
    }

    var data = google.visualization.arrayToDataTable(columnChartData);

    var options = {title:"Box office hits", height: 300,
    bar: {groupWidth: "50%"},
    legend: { position: "none" },
    };
    var chart = new google.visualization.ColumnChart(document.getElementById("boxOfficeColumnChart"));
    chart.draw(data, options);
}

function drawTopCompaniesTable() {
   var tableData = [];

   for (let i = 0; i < companiesData.length; i++)
   {
        tableData.push([companiesData[i]._id, companiesData[i].vote_average]);
   }

   var data = new google.visualization.DataTable();
   data.addColumn('string', 'Company');
   data.addColumn('number', 'Rating');

   // Add individual arrays as rows to the DataTable
   for (let i = 0; i < tableData.length; i++)
   {
       data.addRow(tableData[i]);
   }

   var table = new google.visualization.Table(document.getElementById('companyTable'));

   var options = {showRowNumber: true, width: '100%', height: '100%'}

   table.draw(data, options);
}

function drawGenreRuntimeGroupBarChart() {
  var data = new google.visualization.DataTable();
  data.addColumn('string', 'Genre');
  data.addColumn('number', 'Max Runtime');
  data.addColumn('number', 'Min Runtime');
  data.addColumn('number', 'Rounded Runtime');

  var groupBarChartData = [];
  for (let i = 0; i < runtimeData.length; i++) {
    groupBarChartData.push([
      runtimeData[i]._id, // Genre (bar label)
      runtimeData[i].max_runtime, // Max Runtime
      runtimeData[i].min_runtime, // Min Runtime
      runtimeData[i].rounded_runtime // Rounded Runtime
      
    ]);
  }

  data.addRows(groupBarChartData);

  var options = {
    width: 450,
    height: 600,
     chart: {
      title: 'Runtime Data by Genre',
    },
    bars: 'horizontal', // Set bars to horizontal
    series: {
      0: { // First series (Max Runtime)
        bar: { groupHeight: '100%' } // Adjust the bar width as needed (e.g., '80%')
      },
      1: { // Second series (Min Runtime)
        bar: { groupHeight: '100%' } // Adjust the bar width as needed (e.g., '80%')
      },
      2: { // Third series (Rounded Runtime)
        bar: { groupHeight: '100%' } // Adjust the bar width as needed (e.g., '80%')
      }
    },
    axes: {
      y: {
        0: { label: 'Genre' }, // Genre on the y-axis
      },
    },
  };

  var chart = new google.visualization.BarChart(document.getElementById('runtimeGroupBarChart'));
  chart.draw(data, options);
}

function drawGenreBudgetColumnChart() {

    var columnChartData = [['Genre', 'Budget']];

    for (let  i = 0; i < budgetData.length; i++)
    {
        columnChartData.push([budgetData[i]._id, budgetData[i].rounded_budget]);
    }

    var data = google.visualization.arrayToDataTable(columnChartData);

    var options = {title:"Budget by Genre", height: 600,
    bar: {groupWidth: "50%"},
    legend: { position: "none" },
    };
    var chart = new google.visualization.ColumnChart(document.getElementById("genreBudgetColumnChart"));
    chart.draw(data, options);
}

