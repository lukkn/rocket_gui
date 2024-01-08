/*!
 * makeChart.js v0.0.1
 */


var activeSensorsList = Object.create(null);
const data = [];

function plotLines(canvasID) {
    // Draws lines on canvas with name canvasID, based on sensorData

    const canvas = document.getElementById(canvasID);
    const context = canvas.getContext('2d');

    context.clearRect(0, 0, canvas.width, canvas.height);

    context.beginPath();
    context.moveTo(80, canvas.height);
    context.lineTo(80, 0);
    context.stroke();

    const dataPoints = data.map((value, index) => ({
        x: index * (canvas.width / (data.length - 1)),
        y: canvas.height*((Math.ceil(Math.max(...data)) - value)/(Math.ceil(Math.max(...data)) - Math.floor(Math.min(...data))))
    }));

    context.beginPath();
    context.moveTo(dataPoints[0].x + 80, dataPoints[0].y);

    dataPoints.forEach(point => {
        context.lineTo(point.x + 80, point.y);
    });

    context.lineWidth = 1;
    context.strokeStyle = 'black';
    context.stroke();
}

function defineScale(canvasID, dataList){
    const canvas = document.getElementById(canvasID);
    const context = canvas.getContext('2d');
    
    // Draw y-axis labels
    const maxLabel = Math.ceil(Math.max(...data));
    const minLabel = Math.floor(Math.min(...data));

    const yStep = (maxLabel - minLabel) / 10;

    context.fillStyle = 'black';
    for (let i = 0; i <= 10; i++) {
        const yLabel = (minLabel + i * yStep).toFixed(5);
        const yPosition = canvas.height - (i * (canvas.height / 10));
        context.fillText(yLabel, 0, yPosition);
    }
}

function createCheckboxes(canvasID, sensorList){
    // Create empty chart in the canvas with checkboxes for each sensor
    const canvas = document.getElementById(canvasID);
    const container = document.getElementById("chartContainer");

    sensorList.forEach(function (sensor) {
        // Create checkboxes
        var checkbox = document.createElement('INPUT');
        checkbox.type = "checkbox";
        checkbox.id = canvas.id + sensor + "Checkbox";
        checkbox.addEventListener('change', function() {
            handleGraphCheckbox(checkbox.id);
        })

        var label = document.createElement('label')
        label.htmlFor = "id";
        label.appendChild(document.createTextNode(sensor));

        container.appendChild(checkbox);
        container.appendChild(label);  
    });

    // Create entry in dictionary for current chart
    activeSensorsList[canvas.id] = [];
}

function updateData(canvasID, Data) {

    newData.forEach (function (sensor) {
        if (activeSensorsList[canvasID].includes(sensor)) {

        }
    });

    data.push(Data);

    if (data.length > 50) {
        // Discard the oldest data points
        data.shift();
    }
    plotLines(canvasID);
    defineScale(canvasID);
}

function handleGraphCheckbox(checkboxID){
    checkbox = document.getElementById(checkboxID);
    if (checkbox.checked){
        //display line
    } else {
        //remove line
    }
}
