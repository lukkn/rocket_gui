/*!
 * makeChart.js v0.0.1
 */

//const colors = ["#D2691E", "CD5C5C", "#DB7093", "#FA8072", "F4A460", "DAA520", "9ACD32", "556B2F", "008080", "87CEEB", "4682B4", "6A5ACD", "EE82EE"];
// chocolate, indianred, palevioletred, salmon, sandybrown, goldenrod, yellowgreen,  darkolivegreen, teal, skyblue, steelblue, slateblue, violet
//const colors = ['red', 'blue', 'green'];
const colors = [
    'red', 'blue', 'green', 'orange', 'violet', 'brown', 'salmon', 'purple',
    'cyan', 'pink', 'teal', 'maroon', 'olive', 'navy', 'magenta', 'turquoise',
    'indigo', 'lime', 'gold', 'silver', 'orchid', 'sienna', 'slategray', 'peru'
  ];
var sensorColors = Object.create(null);
var activeSensorsList = Object.create(null); // key: canvasID    value: array of active sensor plots
var dataDict = Object.create(null);
var maxLabel = -Infinity;
var minLabel = Infinity;

function plotLines(chartNumber) {
    const canvasID = "chart" + chartNumber
    const containerID = "container" + chartNumber
    defineScale(containerID);

    const canvas = document.getElementById(canvasID);
    const context = canvas.getContext('2d');
    const activeSensors = activeSensorsList[containerID];

    resizeCanvasToDisplaySize(canvas)
    
    // clear canvas
    context.clearRect(0, 0, canvas.width, canvas.height);

    // draw y-axis line
    context.beginPath();
    context.moveTo(40, canvas.height);
    context.lineTo(40, 0);
    context.strokeStyle = '#161b22';
    context.stroke();

    const yStep = (maxLabel - minLabel) / 10;

    // Draw grid and y-axis labels
    context.fillStyle = '#161b22';
    context.font = 'bold 12px Arial';
    for (let i = 0; i <= 10; i++) {
        // determine position
        const yPosition = canvas.height - (i * (canvas.height / 10));

        // draw labels
        const yLabel = (minLabel + i * yStep).toFixed(1);
        context.fillText(yLabel, 5, yPosition);

        // draw grid lines
        context.beginPath();
        context.moveTo(40, yPosition);
        context.lineTo(canvas.width, yPosition);
        context.strokeStyle = '#89929b';
        context.stroke();
    }

    // plot lines
    activeSensors.forEach (function (sensor) {
        let data = dataDict[sensor];

        const dataPoints = data.map((value, index) => ({
            x: index * ((canvas.width-40) / (data.length - 1)),
            y: canvas.height*((maxLabel - value)/(maxLabel - minLabel))
        }));

        context.beginPath();
        context.moveTo(dataPoints[0].x + 40, dataPoints[0].y);

        dataPoints.forEach(point => {
            context.lineTo(point.x + 40, point.y);
        });

        context.lineWidth = 1;
        context.strokeStyle = sensorColors[sensor];
        context.stroke();
    });
}

function defineScale(containerID){

    // Find the data range of all active plots on the canvas
    const activeSensors = activeSensorsList[containerID];
    const activeData = [];

    activeSensors.forEach(function (sensor) {
        activeData.push.apply(activeData, dataDict[sensor]);
    });

    maxLabel = Math.ceil(Math.max(...activeData));
    minLabel = Math.floor(Math.min(...activeData));
}

function createEmptyChart(containerID, sensorsList){
    activeSensorsList[containerID] = [];
    createCheckboxes(containerID, sensorsList);
    sensorsList.forEach(function(sensorName) {
        dataDict[sensorName] = [];
    });

}

function createCheckboxes(containerID, sensorList){
    // Create empty chart in the canvas with checkboxes for each sensor
    const container = document.getElementById(containerID);
    let index = 0;

    sensorList.forEach(function (sensor) {
        // Assgin colors
        sensorColors[sensor] = colors[index % colors.length];
        index++;

        // Create checkboxes
        let checkbox = document.createElement('INPUT');
        checkbox.type = "checkbox";
        checkbox.class = container.id;
        checkbox.id = container.id + sensor + "Checkbox";
        checkbox.addEventListener('change', function() {
            handleGraphCheckbox(container.id, checkbox.id, sensor);
        })

        let label = document.createElement('label')
        label.id = container.id + sensor + "Label";
        label.htmlFor = "id";
        label.style.color = sensorColors[sensor];
        label.appendChild(document.createTextNode(sensor));

        container.appendChild(checkbox);
        container.appendChild(label);
    });
}

function removeCheckboxes(containerID, sensorList){
    const canvas = document.getElementById(containerID);
    const container = document.getElementById("chartContainer");

    sensorList.forEach(function (sensor) {
        const checkbox = document.getElementById(containerID + sensor + "Checkbox");
        const label = document.getElementById(containerID + sensor + "Label");

        container.removeChild(checkbox);
        container.removeChild(label);
    });
}

function updateData(sensorDataDict, dataLength) {
    for(const [sensorID, sensorValue] of Object.entries(sensorDataDict)){
        let data = dataDict[sensorID];
        if (data != undefined){
            data.push(sensorValue);
            if (data.length > dataLength) {
                // Discard the oldest data points
                // TODO: next ambitious person should make a circlular buffer class
                data.shift();
            }
        }
    }
}

function handleGraphCheckbox(containerID, checkboxID, sensor){
    let activeSensors = activeSensorsList[containerID]

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

function resizeCanvasToDisplaySize(canvas) {
    // Lookup the size the browser is displaying the canvas in CSS pixels.
    const displayWidth  = canvas.clientWidth;
    const displayHeight = canvas.clientHeight;
    
    // Check if the canvas is not the same size.
    const needResize = canvas.width  !== displayWidth ||
                        canvas.height !== displayHeight;
    if (needResize) {
        // Make the canvas the same size
        canvas.width  = displayWidth;
        canvas.height = displayHeight;
    }
}

