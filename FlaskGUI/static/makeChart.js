/*!
 * makeChart.js v0.0.1
 */


var activeSensorsList = Object.create(null); // key: canvasID    value: array of active sensor plots
var dataDict = Object.create(null);
var maxLabel = 0;
var minLabel = 0;

function plotLines(canvasID) {
    // Draws lines on canvas with name canvasID, based on sensorData
    console.log("plot lines " + canvasID);

    const canvas = document.getElementById(canvasID);
    const context = canvas.getContext('2d');
    const activeSensors = activeSensorsList[canvasID];

    context.clearRect(0, 0, canvas.width, canvas.height);

    context.beginPath();
    context.moveTo(40, canvas.height);
    context.lineTo(40, 0);
    context.stroke();

    activeSensors.forEach (function (sensor) {
        const data = dataDict[sensor];

        const dataPoints = data.map((value, index) => ({
            x: index * (canvas.width / (data.length - 1)),
            y: canvas.height*((maxLabel - value)/(maxLabel - minLabel))
        }));
    
        context.beginPath();
        context.moveTo(dataPoints[0].x + 40, dataPoints[0].y);
    
        dataPoints.forEach(point => {
            context.lineTo(point.x + 40, point.y);
        });
    
        context.lineWidth = 1;
        context.strokeStyle = 'black';
        context.stroke();
    });
}

function defineScale(canvasID){
    const canvas = document.getElementById(canvasID);
    const context = canvas.getContext('2d');

    // Find the data range of all active plots on the canvas
    const activeSensors = activeSensorsList[canvasID];
    const activeData = [];

    activeSensors.forEach(function (sensor) {
        activeData.push.apply(activeData, dataDict[sensor]);
    });
    
    maxLabel = Math.ceil(Math.max(...activeData));
    minLabel = Math.floor(Math.min(...activeData));

    const yStep = (maxLabel - minLabel) / 10;

     // Draw y-axis labels
    context.fillStyle = 'black';
    for (let i = 0; i <= 10; i++) {
        const yLabel = (minLabel + i * yStep).toFixed(5);
        const yPosition = canvas.height - (i * (canvas.height / 10));
        context.fillText(yLabel, 0, yPosition);
    }
}

function createEmptyChart(canvasID, sensorsList){
    createCheckboxes(canvasID, sensorsList);
    activeSensorsList[canvasID] = [];
    sensorsList.forEach(function(sensorName) {
        dataDict[sensorName] = [];
    });  
}

function createCheckboxes(canvasID, sensorList){
    // Create empty chart in the canvas with checkboxes for each sensor
    const canvas = document.getElementById(canvasID);
    const container = document.getElementById("chartContainer");

    sensorList.forEach(function (sensor) {
        // Create checkboxes
        var checkbox = document.createElement('INPUT');
        checkbox.type = "checkbox";
        checkbox.class = canvas.id;
        checkbox.id = canvas.id + sensor + "Checkbox";
        checkbox.addEventListener('change', function() {
            handleGraphCheckbox(canvas.id, checkbox.id, sensor);
        })

        var label = document.createElement('label')
        label.id = canvas.id + sensor + "Label";
        label.htmlFor = "id";
        label.appendChild(document.createTextNode(sensor));

        container.appendChild(checkbox);
        container.appendChild(label);  
    });

    // Create entry in dictionary for current chart
    activeSensorsList[canvas.id] = [];
}

function removeCheckboxes(canvasID, sensorList){
    const canvas = document.getElementById(canvasID);
    const container = document.getElementById("chartContainer");

    sensorList.forEach(function (sensor) {
        const checkbox = document.getElementById(canvasID + sensor + "Checkbox");
        const label = document.getElementById(canvasID + sensor + "Label");

        container.removeChild(checkbox);
        container.removeChild(label);
    });
}

function updateData(sensorTupleList) {
    sensorTupleList.forEach (function (sensorTuple) {
        const sensorName = sensorTuple[0];
        const sensorValue = sensorTuple[1];

        var data = dataDict[sensorName];
        // TODO: circular buffer class
        data.push(sensorValue);

        if (data.length > 60*30) {
            // Discard the oldest data points
            // TODO: circlular buffer class, make data.length a parameter of this function
            data.shift();
        }
    });  
}
 
function handleGraphCheckbox(canvasID, checkboxID, sensor){
    var activeSensors = activeSensorsList[canvasID]

    checkbox = document.getElementById(checkboxID);
    if (checkbox.checked){
        activeSensors.push(sensor);
    } else {
        const index = activeSensors.indexOf(sensor);
        if (index > -1) {
            activeSensors.splice(index,1);
        }
    }
}
