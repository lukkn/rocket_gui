/*!
 * makeChart.js v0.0.1
 */



const data = [];

function drawChart(canvasID) {
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

function updateData(canvasID, newData) {
    data.push(newData);

    if (data.length > 50) {
        // Discard the oldest data points
        data.shift();
    }
    drawChart(canvasID);
}

function log(text){
    console.log(text);
}
